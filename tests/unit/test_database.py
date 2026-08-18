"""Unit tests for Database repositories and models."""

import pytest
from app.database.repository import TaskRepository
from app.models.enums import ApprovalStatus, TaskStatus, WorkflowPhase
from app.models.state import AgentPlan, PlanStep


@pytest.mark.asyncio
async def test_task_repository_crud(async_db_session):
    """Test task creation, retrieval, and status updates."""
    repo = TaskRepository(async_db_session)

    # 1. Create task
    task = await repo.create_task(
        task_id="task-test-01",
        repository_url="https://github.com/example/demo",
        user_instruction="Add login endpoint",
        workspace_path="/tmp/test_workspace",
        base_branch="main",
        working_branch="agent/login",
    )
    assert task.id == "task-test-01"
    assert task.status == TaskStatus.PENDING.value

    # 2. Get task
    fetched = await repo.get_task("task-test-01")
    assert fetched is not None
    assert fetched.user_instruction == "Add login endpoint"

    # 3. Update task phase & plan
    plan = AgentPlan(
        objective="Add login endpoint",
        architecture_overview="JWT + FastAPI router",
        steps=[PlanStep(step_id=1, title="Draft model", description="Create user model")],
    )
    updated = await repo.update_task_phase(
        task_id="task-test-01",
        phase=WorkflowPhase.CODING,
        status=TaskStatus.RUNNING,
        plan=plan,
        retry_count=1,
    )
    assert updated.current_phase == WorkflowPhase.CODING.value
    assert updated.status == TaskStatus.RUNNING.value
    assert updated.retry_count == 1
    assert "Draft model" in updated.plan_json


@pytest.mark.asyncio
async def test_tool_call_and_approval_records(async_db_session):
    """Test auditing of tool execution and approval workflow records."""
    repo = TaskRepository(async_db_session)
    await repo.create_task(
        task_id="task-test-02",
        repository_url="https://github.com/example/demo",
        user_instruction="Refactor database",
        workspace_path="/tmp/test",
    )

    # Record tool call
    tool_call = await repo.record_tool_call(
        task_id="task-test-02",
        call_id="call-01",
        tool_name="modify_file",
        input_args={"path": "db.py", "lines": "10-20"},
        output="Successfully modified",
        execution_time_ms=45.2,
    )
    assert tool_call.tool_name == "modify_file"
    assert tool_call.execution_time_ms == 45.2

    # Create & Resolve Approval Request
    approval = await repo.create_approval_request(
        approval_id="appr-01",
        task_id="task-test-02",
        action_type="delete_file",
        tool_name="delete_file",
        action_payload={"path": "legacy.py"},
    )
    assert approval.status == ApprovalStatus.PENDING.value

    resolved = await repo.resolve_approval_request(
        approval_id="appr-01",
        approved=True,
        reviewer_feedback="Approved for removal",
    )
    assert resolved.status == ApprovalStatus.APPROVED.value
    assert resolved.reviewer_feedback == "Approved for removal"
