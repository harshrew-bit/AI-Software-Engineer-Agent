"""API Request, Response, and Event Models."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl

from app.models.enums import ApprovalStatus, TaskStatus, WorkflowPhase
from app.models.state import (
    AgentPlan,
    PendingApproval,
    TestExecutionSummary,
    ToolExecutionRecord,
)


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class CreateTaskRequest(BaseModel):
    """Payload to launch a new software engineering task."""
    repository_url: str = Field(
        ...,
        description="Public or authenticated Git/GitHub repository URL",
        examples=["https://github.com/fastapi/fastapi"],
    )
    user_instruction: str = Field(
        ...,
        description="Natural language instruction for the agent",
        min_length=5,
        examples=["Add JWT authentication endpoints and write unit tests."],
    )
    base_branch: str = Field(default="main", description="Target base branch")
    working_branch: Optional[str] = Field(
        default=None,
        description="Custom branch name (auto-generated if omitted)",
    )
    max_retries: int = Field(
        default=5,
        ge=1,
        le=15,
        description="Maximum test & debug retry loops before asking human input",
    )


class TaskResponse(BaseModel):
    """Summary of an engineering task."""
    id: str
    repository_url: str
    user_instruction: str
    status: TaskStatus
    current_phase: WorkflowPhase
    base_branch: str
    working_branch: str
    commit_sha: Optional[str] = None
    pull_request_url: Optional[str] = None
    plan: Optional[AgentPlan] = None
    retry_count: int = 0
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None


class TaskDetailResponse(TaskResponse):
    """Comprehensive task details including full execution history."""
    tool_history: List[ToolExecutionRecord] = Field(default_factory=list)
    modified_files: List[str] = Field(default_factory=list)
    test_results: List[TestExecutionSummary] = Field(default_factory=list)
    pending_approval: Optional[PendingApproval] = None


class ApprovalDecisionRequest(BaseModel):
    """Payload to approve or reject a paused action."""
    approved: bool
    feedback: Optional[str] = Field(
        default=None,
        description="Feedback or corrective guidance if rejecting or adjusting",
    )


class TaskEvent(BaseModel):
    """Event emitted over SSE/WebSocket streams."""
    task_id: str
    event_type: str
    phase: WorkflowPhase
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=utc_now)
