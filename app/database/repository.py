"""Database repository pattern for tasks, steps, tool calls, and approvals."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.db_models import (
    ApprovalRequestModel,
    StepModel,
    TaskModel,
    ToolCallModel,
)
from app.models.enums import ApprovalStatus, TaskStatus, WorkflowPhase
from app.models.state import AgentPlan, ToolExecutionRecord


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class TaskRepository:
    """Async repository for managing Task entities."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_task(
        self,
        task_id: str,
        repository_url: str,
        user_instruction: str,
        workspace_path: str,
        base_branch: str = "main",
        working_branch: str = "agent-fix",
        max_retries: int = 5,
    ) -> TaskModel:
        """Insert a new task into the database."""
        task = TaskModel(
            id=task_id,
            repository_url=repository_url,
            user_instruction=user_instruction,
            workspace_path=workspace_path,
            base_branch=base_branch,
            working_branch=working_branch,
            status=TaskStatus.PENDING.value,
            current_phase=WorkflowPhase.INITIALIZED.value,
            max_retries=max_retries,
        )
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def get_task(self, task_id: str, include_relations: bool = False) -> Optional[TaskModel]:
        """Fetch a task by ID."""
        stmt = select(TaskModel).where(TaskModel.id == task_id)
        if include_relations:
            stmt = stmt.options(
                selectinload(TaskModel.steps),
                selectinload(TaskModel.tool_calls),
                selectinload(TaskModel.approval_requests),
            )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_tasks(self, limit: int = 50, offset: int = 0) -> List[TaskModel]:
        """List tasks ordered by creation date descending."""
        stmt = (
            select(TaskModel)
            .order_by(desc(TaskModel.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_active_tasks(self) -> List[TaskModel]:
        """Fetch all tasks currently in PENDING or RUNNING status."""
        stmt = select(TaskModel).where(
            TaskModel.status.in_([
                TaskStatus.PENDING.value,
                TaskStatus.RUNNING.value,
            ])
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_task_phase(
        self,
        task_id: str,
        phase: WorkflowPhase,
        status: Optional[TaskStatus] = None,
        plan: Optional[AgentPlan] = None,
        retry_count: Optional[int] = None,
        commit_sha: Optional[str] = None,
        pull_request_url: Optional[str] = None,
        modified_files: Optional[List[str]] = None,
        test_results: Optional[List[Dict[str, Any]]] = None,
        error_message: Optional[str] = None,
    ) -> Optional[TaskModel]:
        """Update task phase, status, or deliverables."""
        task = await self.get_task(task_id)
        if not task:
            return None

        task.current_phase = phase.value
        if status:
            task.status = status.value
        if plan:
            task.plan_json = plan.model_dump_json()
        if retry_count is not None:
            task.retry_count = retry_count
        if commit_sha:
            task.commit_sha = commit_sha
        if pull_request_url is not None:
            task.pull_request_url = pull_request_url
        if modified_files is not None:
            task.modified_files_json = json.dumps(modified_files)
        if test_results is not None:
            task.test_results_json = json.dumps(test_results)
        if error_message:
            task.error_message = error_message

        task.updated_at = utc_now()
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def record_tool_call(
        self,
        task_id: str,
        call_id: str,
        tool_name: str,
        input_args: Dict[str, Any],
        output: Optional[str] = None,
        error: Optional[str] = None,
        exit_code: Optional[int] = None,
        execution_time_ms: float = 0.0,
        requires_approval: bool = False,
        approval_status: ApprovalStatus = ApprovalStatus.NOT_REQUIRED,
    ) -> ToolCallModel:
        """Insert a tool execution audit record."""
        tool_call = ToolCallModel(
            id=call_id,
            task_id=task_id,
            tool_name=tool_name,
            input_parameters=json.dumps(input_args),
            output_result=output,
            error=error,
            exit_code=exit_code,
            execution_time_ms=execution_time_ms,
            requires_approval=requires_approval,
            approval_status=approval_status.value,
        )
        self.session.add(tool_call)
        await self.session.commit()
        await self.session.refresh(tool_call)
        return tool_call

    async def record_step(
        self,
        step_id: str,
        task_id: str,
        node_name: str,
        phase: WorkflowPhase,
        step_index: int,
        state_snapshot: Optional[Dict[str, Any]] = None,
    ) -> StepModel:
        """Record workflow step transition."""
        step = StepModel(
            id=step_id,
            task_id=task_id,
            node_name=node_name,
            phase=phase.value,
            step_index=step_index,
            state_snapshot=json.dumps(state_snapshot) if state_snapshot else None,
        )
        self.session.add(step)
        await self.session.commit()
        await self.session.refresh(step)
        return step

    async def create_approval_request(
        self,
        approval_id: str,
        task_id: str,
        action_type: str,
        tool_name: str,
        action_payload: Dict[str, Any],
    ) -> ApprovalRequestModel:
        """Create a pending human approval request."""
        approval = ApprovalRequestModel(
            id=approval_id,
            task_id=task_id,
            action_type=action_type,
            tool_name=tool_name,
            action_payload=json.dumps(action_payload),
            status=ApprovalStatus.PENDING.value,
        )
        self.session.add(approval)
        await self.session.commit()
        await self.session.refresh(approval)
        return approval

    async def resolve_approval_request(
        self,
        approval_id: str,
        approved: bool,
        reviewer_feedback: Optional[str] = None,
    ) -> Optional[ApprovalRequestModel]:
        """Mark an approval request as approved or rejected."""
        stmt = select(ApprovalRequestModel).where(ApprovalRequestModel.id == approval_id)
        result = await self.session.execute(stmt)
        approval = result.scalar_one_or_none()
        if not approval:
            return None

        approval.status = ApprovalStatus.APPROVED.value if approved else ApprovalStatus.REJECTED.value
        approval.reviewer_feedback = reviewer_feedback
        approval.resolved_at = utc_now()
        await self.session.commit()
        await self.session.refresh(approval)
        return approval
