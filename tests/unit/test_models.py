"""Unit tests for Pydantic models, LangGraph State, and DTOs."""

from app.models.enums import ApprovalStatus, TaskStatus, WorkflowPhase
from app.models.state import (
    AgentPlan,
    AgentState,
    PendingApproval,
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


def test_test_execution_summary_normalization_success_and_failure():
    """Verify TestExecutionSummary normalization from legacy, nested, and canonical dictionaries."""
    # 1. Legacy format with is_success and metadata
    raw_success = {
        "command": "pytest -v",
        "is_success": True,
        "output": "1 passed in 0.1s",
        "exit_code": 0,
        "metadata": {
            "passed": 1,
            "failed": 0,
            "errors": 0,
            "total": 1,
            "is_success": True,
        },
    }
    summary_success = TestExecutionSummary.model_validate(raw_success)
    assert summary_success.command == "pytest -v"
    assert summary_success.passed is True
    assert summary_success.total_tests == 1
    assert summary_success.failures == 0
    assert summary_success.exit_code == 0
    assert "1 passed" in summary_success.stdout

    # 2. Failed test result with failures count
    raw_failed = {
        "command": "pytest -v",
        "is_success": False,
        "output": "1 failed in 0.2s",
        "exit_code": 1,
        "metadata": {
            "passed": 0,
            "failed": 1,
            "errors": 0,
            "total": 1,
            "is_success": False,
        },
    }
    summary_failed = TestExecutionSummary.model_validate(raw_failed)
    assert summary_failed.command == "pytest -v"
    assert summary_failed.passed is False
    assert summary_failed.failures == 1
    assert summary_failed.exit_code == 1

    # 3. Nested result dictionary format
    raw_nested = {
        "command": "pytest -v",
        "result": {
            "is_success": True,
            "stdout": "All tests passed",
            "exit_code": 0,
        },
    }
    summary_nested = TestExecutionSummary.model_validate(raw_nested)
    assert summary_nested.passed is True
    assert summary_nested.stdout == "All tests passed"

    # 4. Canonical format with passed boolean
    raw_canonical = {
        "command": "npm test",
        "passed": True,
        "total_tests": 5,
        "failures": 0,
        "errors": 0,
        "stdout": "PASS",
        "stderr": "",
        "exit_code": 0,
        "duration_seconds": 1.5,
    }
    summary_canonical = TestExecutionSummary.model_validate(raw_canonical)
    assert summary_canonical.command == "npm test"
    assert summary_canonical.passed is True
    assert summary_canonical.total_tests == 5
    assert summary_canonical.duration_seconds == 1.5


def test_pending_approval_model_normalization():
    """Verify PendingApproval normalizes payload/action_payload and reason from different formats."""
    # 1. Stored DB approval format (with action_payload and reviewer_feedback)
    raw_db = {
        "approval_id": "appr_123_delete_file",
        "action_type": "tool_execution",
        "tool_name": "delete_file",
        "action_payload": {"file_path": "legacy.py"},
        "status": "pending",
        "reviewer_feedback": "Requires destructive file approval",
    }
    appr1 = PendingApproval.model_validate(raw_db)
    assert appr1.approval_id == "appr_123_delete_file"
    assert appr1.tool_name == "delete_file"
    assert appr1.payload == {"file_path": "legacy.py"}
    assert appr1.action_payload == {"file_path": "legacy.py"}
    assert appr1.reason == "Requires destructive file approval"
    assert appr1.status == ApprovalStatus.PENDING

    # 2. Original schema format (with payload and reason)
    raw_schema = {
        "action_type": "tool_execution",
        "tool_name": "run_command",
        "payload": {"command": "rm -rf /tmp/data"},
        "reason": "Destructive system command",
    }
    appr2 = PendingApproval.model_validate(raw_schema)
    assert appr2.tool_name == "run_command"
    assert appr2.payload == {"command": "rm -rf /tmp/data"}
    assert appr2.action_payload == {"command": "rm -rf /tmp/data"}
    assert appr2.reason == "Destructive system command"

    # 3. Stringified JSON action_payload
    raw_json_str = {
        "id": "appr_456",
        "tool_name": "modify_file",
        "action_payload": '{"file_path": "config.yaml", "changes": "key: val"}',
    }
    appr3 = PendingApproval.model_validate(raw_json_str)
    assert appr3.approval_id == "appr_456"
    assert appr3.payload == {"file_path": "config.yaml", "changes": "key: val"}
    assert "modify_file" in appr3.reason
