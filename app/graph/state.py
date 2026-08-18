"""LangGraph Graph State Definition."""

from typing import Annotated, Any, Dict, List, Optional, TypedDict
from pydantic import BaseModel, Field

from app.models.enums import WorkflowPhase
from app.models.state import (
    AgentPlan,
    PendingApproval,
    TestExecutionSummary,
    ToolExecutionRecord,
)


class GraphState(TypedDict, total=False):
    """LangGraph State representation across all graph nodes."""
    task_id: str
    repository_url: str
    base_branch: str
    working_branch: str
    workspace_path: str
    user_instruction: str

    # Workflow Status
    current_phase: str

    # Analysis
    file_list: List[str]
    detected_framework: Optional[str]
    detected_test_command: Optional[str]
    repo_summary: str

    # Planning
    plan: Optional[Dict[str, Any]]

    # Coding & Tools
    tool_history: List[Dict[str, Any]]
    modified_files: List[str]

    # Testing & Debugging Loop
    test_results: List[Dict[str, Any]]
    latest_test_passed: bool
    retry_count: int
    max_retries: int
    debug_guidance: Optional[str]

    # Review & Final Deliverables
    review_summary: Optional[str]
    commit_message: Optional[str]
    commit_sha: Optional[str]
    pull_request_url: Optional[str]
    error_message: Optional[str]
