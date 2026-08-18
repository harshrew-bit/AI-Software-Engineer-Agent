"""FastAPI REST API Routes."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repository import TaskRepository
from app.database.session import get_db_session
from app.models.enums import TaskStatus
from app.models.task import (
    ApprovalDecisionRequest,
    CreateTaskRequest,
    TaskDetailResponse,
    TaskResponse,
)
from app.services.task_service import TaskManagerService

api_router = APIRouter(prefix="/api/v1")
task_service = TaskManagerService()


@api_router.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and launch a software engineering task",
)
async def create_task(
    request: CreateTaskRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """Launch an autonomous engineering task on a GitHub repository."""
    try:
        return await task_service.create_and_start_task(request, session)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start task: {str(e)}",
        )


@api_router.get(
    "/tasks",
    response_model=List[TaskResponse],
    summary="List tasks",
)
async def list_tasks(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
):
    """Retrieve list of tasks ordered by creation date."""
    repo = TaskRepository(session)
    tasks = await repo.list_tasks(limit=limit, offset=offset)
    return [
        TaskResponse(
            id=t.id,
            repository_url=t.repository_url,
            user_instruction=t.user_instruction,
            status=TaskStatus(t.status),
            current_phase=t.current_phase,
            base_branch=t.base_branch,
            working_branch=t.working_branch,
            commit_sha=t.commit_sha,
            pull_request_url=t.pull_request_url,
            retry_count=t.retry_count,
            created_at=t.created_at,
            updated_at=t.updated_at,
            error_message=t.error_message,
        )
        for t in tasks
    ]


@api_router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    summary="Get task status",
)
async def get_task(
    task_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Get high-level summary and status of a task."""
    task = await task_service.get_task_summary(task_id, session)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found.",
        )
    return task


@api_router.get(
    "/tasks/{task_id}/detail",
    response_model=TaskDetailResponse,
    summary="Get comprehensive task details",
)
async def get_task_detail(
    task_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Get full task history including tool calls and test outputs."""
    detail = await task_service.get_task_detail(task_id, session)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found.",
        )
    return detail


@api_router.get(
    "/tasks/{task_id}/diff",
    summary="Get active git diff",
)
async def get_task_diff(
    task_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Retrieve the unified git diff of all modifications made so far."""
    diff = await task_service.get_task_diff(task_id, session)
    return {"task_id": task_id, "diff": diff}


@api_router.post(
    "/tasks/{task_id}/approve",
    summary="Submit human approval decision",
)
async def approve_task_action(
    task_id: str,
    approval_id: str,
    decision: ApprovalDecisionRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """Approve or reject a paused dangerous action."""
    resolved = await task_service.resolve_approval(
        task_id=task_id,
        approval_id=approval_id,
        approved=decision.approved,
        feedback=decision.feedback,
        session=session,
    )
    if not resolved:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval request '{approval_id}' for task '{task_id}' not found.",
        )
    return {
        "task_id": task_id,
        "approval_id": approval_id,
        "status": "approved" if decision.approved else "rejected",
    }


@api_router.post(
    "/tasks/{task_id}/cancel",
    summary="Cancel active task",
)
async def cancel_task(
    task_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Cancel a running task."""
    cancelled = await task_service.cancel_task(task_id, session)
    return {"task_id": task_id, "cancelled": cancelled}
