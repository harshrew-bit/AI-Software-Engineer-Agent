"""Unit tests for Pydantic models, LangGraph State, and DTOs."""

from app.models.enums import ApprovalStatus, TaskStatus, WorkflowPhase
from app.models.state import (
    AgentPlan,
    AgentState,
    PlanStep,
    TestExecutionSummary,
    ToolExecutionRecord,
)
from app.models.task import CreateTaskRequest, TaskDetailResponse


def test_agent_plan_serialization():
    """Verify AgentPlan structure and step indexing."""
    step1 = PlanStep(
        step_id=1,
        title="Analyze dependencies",
        description="Check pyproject.toml",
        target_files=["pyproject.toml"],
    )
    plan = AgentPlan(
        objective="Add JWT Authentication",
        architecture_overview="Create auth module with PyJWT",
        steps=[step1],
    )
    json_data = plan.model_dump_json()
    deserialized = AgentPlan.model_validate_json(json_data)
    assert deserialized.objective == "Add JWT Authentication"
    assert len(deserialized.steps) == 1
    assert deserialized.steps[0].target_files == ["pyproject.toml"]


def test_agent_state_transitions():
    """Verify AgentState validation and tool execution logs."""
    state = AgentState(
        task_id="task-123",
        repository_url="https://github.com/example/repo",
        working_branch="feat-jwt",
        workspace_path="/tmp/workspace",
        user_instruction="Add JWT authentication",
    )
    assert state.current_phase == WorkflowPhase.INITIALIZED
    assert state.retry_count == 0

    # Add tool execution record
    record = ToolExecutionRecord(
        call_id="call-1",
        tool_name="read_file",
        input_args={"file_path": "main.py"},
        output="from fastapi import FastAPI",
        execution_time_ms=12.5,
    )
    state.tool_history.append(record)
    assert len(state.tool_history) == 1
    assert state.tool_history[0].tool_name == "read_file"


def test_create_task_request_validation():
    """Test task request validation rules."""
    req = CreateTaskRequest(
        repository_url="https://github.com/fastapi/fastapi",
        user_instruction="Fix CORS middleware issue in router.",
        base_branch="main",
        max_retries=3,
    )
    assert req.base_branch == "main"
    assert req.max_retries == 3
