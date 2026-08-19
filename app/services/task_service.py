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
from app.sandbox.factory import get_sandbox
from app.models.task import (
    CreateTaskRequest,
    TaskDetailResponse,
    TaskEvent,
    TaskResponse,
)
from app.repository.git_manager import GitWorkspaceManager
from app.services.event_bus import global_event_bus
from app.services.workspace_service import WorkspaceService
from app.tools.base import ToolExecutionContext
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
        is_resumption: bool = False,
        initial_graph_state: Optional[GraphState] = None,
    ) -> None:
        """Background worker that runs the LangGraph state machine and broadcasts progress."""
        session_factory = get_session_factory()
        git_manager = GitWorkspaceManager(task_id=task_id, workspace_path=Path(workspace_path))

        try:
            if not is_resumption:
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
                    logger.error(
                        f"Failed to initialize repository '{repository_url}': {clone_err}",
                        exc_info=True,
                    )
                    raise
            else:
                # Resumed workflow event
                await global_event_bus.publish(
                    task_id,
                    TaskEvent(
                        task_id=task_id,
                        event_type="workflow_resumed",
                        phase=WorkflowPhase.CODING,
                        message=f"Resuming workflow for task {task_id}...",
                    ),
                )

            # 2. Update DB to RUNNING and build Graph with DB repository
            async with session_factory() as session:
                repo = TaskRepository(session)
                current_phase = WorkflowPhase.CODING if is_resumption else WorkflowPhase.REPOSITORY_ANALYSIS
                await repo.update_task_phase(
                    task_id=task_id,
                    phase=current_phase,
                    status=TaskStatus.RUNNING,
                )

                tool_registry = create_default_tool_registry()
                from app.graph.builder import build_agent_graph
                app = build_agent_graph(
                    llm_client=self.llm_client,
                    tool_registry=tool_registry,
                    repository=repo,
                )

                if initial_graph_state:
                    initial_state: GraphState = initial_graph_state
                else:
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
        """Resolve a human-in-the-loop approval checkpoint and resume workflow."""
        # 1. Prevent duplicate concurrent executions
        active_bg = self._active_tasks.get(task_id)
        if active_bg and not active_bg.done():
            logger.warning(f"Task '{task_id}' already has an active execution in progress.")
            return False

        repo = TaskRepository(session)
        task = await repo.get_task(task_id, include_relations=True)
        if not task:
            logger.warning(f"Task '{task_id}' not found for approval resolution.")
            return False

        if task.status != TaskStatus.PAUSED_FOR_APPROVAL.value:
            logger.warning(
                f"Task '{task_id}' is in status '{task.status}', cannot resolve approval unless '{TaskStatus.PAUSED_FOR_APPROVAL.value}'."
            )
            return False

        # 2. Resolve the approval request record in the database
        approval = await repo.resolve_approval_request(
            approval_id=approval_id,
            approved=approved,
            reviewer_feedback=feedback,
        )
        if not approval:
            logger.warning(f"Approval request '{approval_id}' not found for task '{task_id}'.")
            return False

        # 3. Publish approval_resolved event
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

        # 4. Reconstruct tool history & modified files from DB
        tool_history: List[Dict[str, Any]] = []
        for tc in task.tool_calls or []:
            tool_history.append({
                "tool_name": tc.tool_name,
                "call_id": tc.id,
                "success": (tc.error is None or tc.error == ""),
                "output": tc.output_result,
                "error": tc.error,
                "requires_approval": tc.requires_approval,
                "approval_status": tc.approval_status,
                "execution_time_ms": tc.execution_time_ms,
            })

        modified_files_list = json.loads(task.modified_files_json) if task.modified_files_json else []
        modified_files_set = set(modified_files_list)
        plan_dict = json.loads(task.plan_json) if task.plan_json else None
        test_results = json.loads(task.test_results_json) if task.test_results_json else []

        workspace_path = Path(task.workspace_path)
        git_manager = GitWorkspaceManager(task_id=task_id, workspace_path=workspace_path)
        sandbox = get_sandbox(workspace_path=workspace_path)
        tool_registry = create_default_tool_registry()
        tool_context = ToolExecutionContext(
            task_id=task_id,
            workspace_path=workspace_path,
            git_manager=git_manager,
            sandbox=sandbox,
            settings=get_settings(),
            repository=repo,
        )

        # 5. Handle action execution (if approved) or rejection note (if rejected)
        raw_payload = {}
        if approval.action_payload:
            try:
                raw_payload = json.loads(approval.action_payload) if isinstance(approval.action_payload, str) else approval.action_payload
            except Exception:
                raw_payload = {}

        if approved:
            # Execute the approved dangerous tool with bypass_approval=True
            logger.info(f"Executing approved tool '{approval.tool_name}' for task '{task_id}'")
            tool_res = await tool_registry.dispatch(
                tool_name=approval.tool_name,
                arguments=raw_payload,
                context=tool_context,
                bypass_approval=True,
            )
            tool_history.append(tool_res.model_dump())

            if approval.tool_name in ("create_file", "modify_file", "delete_file"):
                target_f = raw_payload.get("file_path")
                if target_f:
                    modified_files_set.add(target_f)

            await global_event_bus.publish(
                task_id,
                TaskEvent(
                    task_id=task_id,
                    event_type="tool_execution",
                    phase=WorkflowPhase.CODING,
                    message=f"Executed approved {approval.tool_name} (success={tool_res.success})",
                    data={
                        "tool_name": approval.tool_name,
                        "success": tool_res.success,
                        "requires_approval": False,
                        "execution_time_ms": tool_res.execution_time_ms,
                    },
                ),
            )
        else:
            # Rejection handling
            reject_msg = f"Action rejected by reviewer: {feedback or 'No feedback provided'}"
            tool_history.append({
                "tool_name": approval.tool_name,
                "call_id": f"rejected_{approval_id}",
                "success": False,
                "output": None,
                "error": reject_msg,
                "requires_approval": False,
                "approval_status": "rejected",
                "execution_time_ms": 0.0,
            })
            await global_event_bus.publish(
                task_id,
                TaskEvent(
                    task_id=task_id,
                    event_type="tool_execution",
                    phase=WorkflowPhase.CODING,
                    message=f"Tool execution rejected: {approval.tool_name}",
                    data={
                        "tool_name": approval.tool_name,
                        "success": False,
                        "error": reject_msg,
                    },
                ),
            )

        # Inspect git status for modified files
        try:
            status = git_manager.get_status()
            for f in status.get("modified", []) + status.get("untracked", []):
                modified_files_set.add(f)
        except Exception:
            pass

        # 6. Build initial state for resumed workflow
        initial_graph_state: GraphState = {
            "task_id": task.id,
            "repository_url": task.repository_url,
            "base_branch": task.base_branch,
            "working_branch": task.working_branch,
            "workspace_path": task.workspace_path,
            "user_instruction": task.user_instruction,
            "current_phase": WorkflowPhase.CODING.value,
            "plan": plan_dict,
            "tool_history": tool_history,
            "modified_files": sorted(list(modified_files_set)),
            "test_results": test_results,
            "max_retries": task.max_retries,
            "retry_count": task.retry_count,
            "pending_approval": None,
        }

        # 7. Launch resumed workflow in the background
        bg_task = asyncio.create_task(
            self._execute_workflow(
                task_id=task.id,
                repository_url=task.repository_url,
                user_instruction=task.user_instruction,
                workspace_path=task.workspace_path,
                base_branch=task.base_branch,
                working_branch=task.working_branch,
                max_retries=task.max_retries,
                is_resumption=True,
                initial_graph_state=initial_graph_state,
            )
        )
        self._active_tasks[task_id] = bg_task
        return True

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
