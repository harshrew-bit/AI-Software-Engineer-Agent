"""Task Orchestration and Execution Service."""

import asyncio
import json
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database.repository import TaskRepository
from app.database.session import get_session_factory
from app.graph.state import GraphState
from app.llm.base import BaseLLMClient
from app.llm.factory import get_llm_client
from app.models.enums import ApprovalStatus, TaskStatus, WorkflowPhase
from app.models.state import AgentPlan, PendingApproval, TestExecutionSummary, ToolExecutionRecord
from app.models.task import (
    CreateTaskRequest,
    TaskDetailResponse,
    TaskEvent,
    TaskResponse,
)
from app.repository.git_manager import GitWorkspaceManager
from app.services.event_bus import global_event_bus
from app.services.workspace_service import WorkspaceService
from app.tools.registry import create_default_tool_registry

logger = logging.getLogger(__name__)


class TaskManagerService:
    """Service managing task lifecycles, database persistence, and background LangGraph workers."""

    def __init__(
        self,
        llm_client: Optional[BaseLLMClient] = None,
        workspace_service: Optional[WorkspaceService] = None,
    ):
        self.settings = get_settings()
        self.llm_client = llm_client or get_llm_client()
        self.workspace_service = workspace_service or WorkspaceService()
        self._active_tasks: Dict[str, asyncio.Task] = {}

    async def create_and_start_task(
        self,
        request: CreateTaskRequest,
        session: AsyncSession,
    ) -> TaskResponse:
        """Create task in DB, initialize workspace, and start background workflow execution."""
        task_id = f"task_{uuid.uuid4().hex[:10]}"
        workspace_path = self.workspace_service.allocate_workspace(task_id)
        working_branch = request.working_branch or f"agent-fix/{task_id}"

        repo = TaskRepository(session)
        task_model = await repo.create_task(
            task_id=task_id,
            repository_url=request.repository_url,
            user_instruction=request.user_instruction,
            workspace_path=str(workspace_path),
            base_branch=request.base_branch,
            working_branch=working_branch,
            max_retries=request.max_retries,
        )

        # Spawn background LangGraph workflow
        bg_task = asyncio.create_task(
            self._execute_workflow(
                task_id=task_id,
                repository_url=request.repository_url,
                user_instruction=request.user_instruction,
                workspace_path=str(workspace_path),
                base_branch=request.base_branch,
                working_branch=working_branch,
                max_retries=request.max_retries,
            )
        )
        self._active_tasks[task_id] = bg_task

        return TaskResponse(
            id=task_model.id,
            repository_url=task_model.repository_url,
            user_instruction=task_model.user_instruction,
            status=TaskStatus(task_model.status),
            current_phase=WorkflowPhase(task_model.current_phase),
            base_branch=task_model.base_branch,
            working_branch=task_model.working_branch,
            retry_count=task_model.retry_count,
            created_at=task_model.created_at,
            updated_at=task_model.updated_at,
        )

    async def _execute_workflow(
        self,
        task_id: str,
        repository_url: str,
        user_instruction: str,
        workspace_path: str,
        base_branch: str,
        working_branch: str,
        max_retries: int,
    ) -> None:
        """Background worker that runs the LangGraph state machine and broadcasts progress."""
        session_factory = get_session_factory()
        git_manager = GitWorkspaceManager(task_id=task_id, workspace_path=Path(workspace_path))

        try:
            # 1. Initialize Git Workspace
            await global_event_bus.publish(
                task_id,
                TaskEvent(
                    task_id=task_id,
                    event_type="workspace_init",
                    phase=WorkflowPhase.INITIALIZED,
                    message=f"Initializing workspace for {repository_url}...",
                ),
            )

            try:
                git_manager.initialize_workspace(
                    repository_url=repository_url,
                    base_branch=base_branch,
                    working_branch=working_branch,
                )
            except Exception as clone_err:
                logger.warning(
                    f"Remote clone failed ({clone_err}); initializing local repository for testing/bootstrapping."
                )
                git_manager.init_local_empty_repo(default_branch=base_branch)

            # 2. Update DB to RUNNING and build Graph with DB repository
            async with session_factory() as session:
                repo = TaskRepository(session)
                await repo.update_task_phase(
                    task_id=task_id,
                    phase=WorkflowPhase.REPOSITORY_ANALYSIS,
                    status=TaskStatus.RUNNING,
                )

                tool_registry = create_default_tool_registry()
                from app.graph.builder import build_agent_graph
                app = build_agent_graph(
                    llm_client=self.llm_client,
                    tool_registry=tool_registry,
                    repository=repo,
                )

                initial_state: GraphState = {
                    "task_id": task_id,
                    "repository_url": repository_url,
                    "base_branch": base_branch,
                    "working_branch": working_branch,
                    "workspace_path": workspace_path,
                    "user_instruction": user_instruction,
                    "max_retries": max_retries,
                    "retry_count": 0,
                }

                final_state = await app.ainvoke(initial_state)

                # 3. Evaluate Workflow Result & Status
                plan_obj = None
                if final_state.get("plan"):
                    plan_obj = AgentPlan.model_validate(final_state["plan"])

                modified_files = final_state.get("modified_files", [])
                test_results = final_state.get("test_results", [])
                latest_test_passed = final_state.get("latest_test_passed", False)
                commit_sha = final_state.get("commit_sha")
                pull_request_url = final_state.get("pull_request_url")
                pending_approval = final_state.get("pending_approval")

                if pending_approval:
                    task_status = TaskStatus.PAUSED_FOR_APPROVAL
                    task_phase = WorkflowPhase.CODING
                    error_msg = f"Action '{pending_approval.get('tool_name')}' requires human approval."
                elif not latest_test_passed and test_results:
                    task_status = TaskStatus.FAILED
                    task_phase = WorkflowPhase.FINISHED
                    error_msg = "Automated tests failed after max retries."
                elif not commit_sha and not modified_files:
                    task_status = TaskStatus.FAILED
                    task_phase = WorkflowPhase.FINISHED
                    error_msg = "No code modifications were implemented."
                else:
                    task_status = TaskStatus.COMPLETED
                    task_phase = WorkflowPhase.FINISHED
                    error_msg = None

                await repo.update_task_phase(
                    task_id=task_id,
                    phase=task_phase,
                    status=task_status,
                    plan=plan_obj,
                    retry_count=final_state.get("retry_count", 0),
                    commit_sha=commit_sha,
                    pull_request_url=pull_request_url,
                    modified_files=modified_files,
                    test_results=test_results,
                    error_message=error_msg,
                )

            if task_status == TaskStatus.COMPLETED:
                await global_event_bus.publish(
                    task_id,
                    TaskEvent(
                        task_id=task_id,
                        event_type="task_completed",
                        phase=WorkflowPhase.FINISHED,
                        message="Task completed successfully!",
                        data={
                            "commit_sha": commit_sha,
                            "pull_request_url": pull_request_url,
                            "modified_files": modified_files,
                        },
                    ),
                )
            elif task_status == TaskStatus.FAILED:
                await global_event_bus.publish(
                    task_id,
                    TaskEvent(
                        task_id=task_id,
                        event_type="task_failed",
                        phase=WorkflowPhase.FINISHED,
                        message=f"Task execution failed: {error_msg}",
                        data={"error_message": error_msg},
                    ),
                )

        except Exception as e:
            logger.error(f"Task {task_id} workflow execution failed: {e}", exc_info=True)
            async with session_factory() as session:
                repo = TaskRepository(session)
                await repo.update_task_phase(
                    task_id=task_id,
                    phase=WorkflowPhase.FINISHED,
                    status=TaskStatus.FAILED,
                    error_message=str(e),
                )
            await global_event_bus.publish(
                task_id,
                TaskEvent(
                    task_id=task_id,
                    event_type="task_failed",
                    phase=WorkflowPhase.FINISHED,
                    message=f"Task failed: {str(e)}",
                ),
            )
        finally:
            self._active_tasks.pop(task_id, None)

    async def get_task_summary(self, task_id: str, session: AsyncSession) -> Optional[TaskResponse]:
        """Fetch summary model for a task."""
        repo = TaskRepository(session)
        task = await repo.get_task(task_id)
        if not task:
            return None

        plan = AgentPlan.model_validate_json(task.plan_json) if task.plan_json else None
        return TaskResponse(
            id=task.id,
            repository_url=task.repository_url,
            user_instruction=task.user_instruction,
            status=TaskStatus(task.status),
            current_phase=WorkflowPhase(task.current_phase),
            base_branch=task.base_branch,
            working_branch=task.working_branch,
            commit_sha=task.commit_sha,
            pull_request_url=task.pull_request_url,
            plan=plan,
            retry_count=task.retry_count,
            created_at=task.created_at,
            updated_at=task.updated_at,
            error_message=task.error_message,
        )

    async def get_task_detail(self, task_id: str, session: AsyncSession) -> Optional[TaskDetailResponse]:
        """Fetch comprehensive details for a task."""
        repo = TaskRepository(session)
        task = await repo.get_task(task_id, include_relations=True)
        if not task:
            return None

        plan = AgentPlan.model_validate_json(task.plan_json) if task.plan_json else None
        tool_records = [
            ToolExecutionRecord(
                call_id=tc.id,
                tool_name=tc.tool_name,
                input_args=json.loads(tc.input_parameters) if tc.input_parameters else {},
                output=tc.output_result,
                error=tc.error,
                exit_code=tc.exit_code,
                execution_time_ms=tc.execution_time_ms,
                requires_approval=tc.requires_approval,
                approval_status=ApprovalStatus(tc.approval_status),
                timestamp=tc.created_at,
            )
            for tc in task.tool_calls
        ]

        modified_files = json.loads(task.modified_files_json) if task.modified_files_json else []
        raw_tests = json.loads(task.test_results_json) if task.test_results_json else []
        test_summaries = [
            TestExecutionSummary(
                command=t.get("command", ""),
                is_success=t.get("is_success", False),
                output=t.get("output", ""),
                exit_code=t.get("exit_code"),
                metadata=t.get("metadata", {}),
            )
            for t in raw_tests
        ]

        pending_approvals = [
            PendingApproval(
                approval_id=a.id,
                action_type=a.action_type,
                tool_name=a.tool_name,
                action_payload=json.loads(a.action_payload) if a.action_payload else {},
                status=ApprovalStatus(a.status),
                reviewer_feedback=a.reviewer_feedback,
                created_at=a.requested_at,
            )
            for a in task.approval_requests
            if a.status == "pending"
        ]

        return TaskDetailResponse(
            id=task.id,
            repository_url=task.repository_url,
            user_instruction=task.user_instruction,
            status=TaskStatus(task.status),
            current_phase=WorkflowPhase(task.current_phase),
            base_branch=task.base_branch,
            working_branch=task.working_branch,
            commit_sha=task.commit_sha,
            pull_request_url=task.pull_request_url,
            plan=plan,
            retry_count=task.retry_count,
            created_at=task.created_at,
            updated_at=task.updated_at,
            error_message=task.error_message,
            tool_history=tool_records,
            modified_files=modified_files,
            test_results=test_summaries,
            pending_approval=pending_approvals[0] if pending_approvals else None,
        )

    async def get_task_diff(self, task_id: str, session: AsyncSession) -> str:
        """Fetch active unified git diff against base branch."""
        repo = TaskRepository(session)
        task = await repo.get_task(task_id)
        if not task:
            return ""

        git_manager = GitWorkspaceManager(task_id=task_id, workspace_path=Path(task.workspace_path))
        try:
            return git_manager.get_diff(against_branch=task.base_branch)
        except Exception:
            return ""

    async def resolve_approval(
        self,
        task_id: str,
        approval_id: str,
        approved: bool,
        feedback: Optional[str],
        session: AsyncSession,
    ) -> bool:
        """Resolve a human-in-the-loop approval checkpoint."""
        repo = TaskRepository(session)
        result = await repo.resolve_approval_request(
            approval_id=approval_id,
            approved=approved,
            reviewer_feedback=feedback,
        )
        if result:
            await global_event_bus.publish(
                task_id,
                TaskEvent(
                    task_id=task_id,
                    event_type="approval_resolved",
                    phase=WorkflowPhase.CODING,
                    message=f"Human approval resolved: {'APPROVED' if approved else 'REJECTED'}",
                    data={"approval_id": approval_id, "approved": approved, "feedback": feedback},
                ),
            )
            return True
        return False

    async def cancel_task(self, task_id: str, session: AsyncSession) -> bool:
        """Cancel an active task."""
        bg_task = self._active_tasks.get(task_id)
        if bg_task and not bg_task.done():
            bg_task.cancel()

        repo = TaskRepository(session)
        await repo.update_task_phase(
            task_id=task_id,
            phase=WorkflowPhase.FINISHED,
            status=TaskStatus.CANCELLED,
        )
        return True
