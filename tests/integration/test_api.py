"""Integration tests for FastAPI REST API endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.routes import task_service
from app.database.session import init_db
from app.llm.mock import MockLLMClient
from app.main import app
from app.agents.schemas import PlanGenerationOutput, ReviewSummaryOutput
from app.models.state import PlanStep
import app.database.session as db_session


@pytest.fixture(autouse=True)
async def setup_test_app(tmp_path):
    """Ensure database schema is created and inject MockLLM client into task service."""
    db_session._engine = None
    db_session._session_factory = None
    await init_db()

    mock_llm = MockLLMClient(default_response="Mocked API LLM Response")
    mock_llm.set_structured_response(
        "PlanGenerationOutput",
        PlanGenerationOutput(
            objective="Add health check endpoint",
            architecture_overview="Create endpoint in main.py",
            steps=[PlanStep(step_id=1, title="Create health", description="Add endpoint")],
        ),
    )
    mock_llm.set_structured_response(
        "ReviewSummaryOutput",
        ReviewSummaryOutput(
            summary="Added health check endpoint",
            commit_message="feat: add health check endpoint",
            is_ready_for_commit=True,
        ),
    )
    task_service.llm_client = mock_llm


@pytest.mark.asyncio
async def test_health_and_root_endpoints():
    """Verify system health check and root endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"

        # 2. Root index
        root_resp = await client.get("/")
        assert root_resp.status_code == 200
        assert "Welcome to" in root_resp.json()["message"]


@pytest.mark.asyncio
async def test_task_creation_and_retrieval(tmp_path):
    """Verify task creation, list, and detail API endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create Task
        payload = {
            "repository_url": "https://github.com/example/api-demo",
            "user_instruction": "Add health check endpoint to FastAPI app",
            "base_branch": "main",
            "max_retries": 3,
        }
        create_resp = await client.post("/api/v1/tasks", json=payload)
        assert create_resp.status_code == 201
        task_data = create_resp.json()
        task_id = task_data["id"]
        assert task_data["user_instruction"] == payload["user_instruction"]
        assert task_data["status"] in ("pending", "running", "completed")

        # 2. List Tasks
        list_resp = await client.get("/api/v1/tasks")
        assert list_resp.status_code == 200
        tasks = list_resp.json()
        assert len(tasks) >= 1
        assert any(t["id"] == task_id for t in tasks)

        # 3. Get Task Status
        get_resp = await client.get(f"/api/v1/tasks/{task_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == task_id

        # 4. Get Task Detail
        detail_resp = await client.get(f"/api/v1/tasks/{task_id}/detail")
        assert detail_resp.status_code == 200
        assert detail_resp.json()["id"] == task_id

        # 5. Get Task Diff
        diff_resp = await client.get(f"/api/v1/tasks/{task_id}/diff")
        assert diff_resp.status_code == 200
        assert "diff" in diff_resp.json()

        # 6. Cancel Task
        cancel_resp = await client.post(f"/api/v1/tasks/{task_id}/cancel")
        assert cancel_resp.status_code == 200
        assert cancel_resp.json()["cancelled"] is True


@pytest.mark.asyncio
async def test_non_existent_task_returns_404():
    """Verify 404 behavior for non-existent tasks."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/tasks/task_does_not_exist")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_task_detail_with_stored_test_results():
    """Verify GET /tasks/{task_id}/detail parses stored test_results_json without 500 ValidationError."""
    import uuid
    from app.database.session import get_session_factory
    from app.database.repository import TaskRepository
    from app.models.enums import TaskStatus, WorkflowPhase

    test_task_id = f"task_detail_{uuid.uuid4().hex[:8]}"

    session_factory = get_session_factory()
    async with session_factory() as session:
        repo = TaskRepository(session)
        await repo.create_task(
            task_id=test_task_id,
            repository_url="https://github.com/example/test-detail",
            user_instruction="Test detail serialization",
            workspace_path="/tmp/test_detail",
        )
        # Store test results containing both successful and failed records in legacy structure
        stored_results = [
            {
                "command": "pytest -v",
                "is_success": True,
                "output": "1 passed in 0.05s",
                "exit_code": 0,
                "metadata": {
                    "passed": 1,
                    "failed": 0,
                    "errors": 0,
                    "total": 1,
                    "is_success": True,
                },
            },
            {
                "command": "pytest -v tests/test_extra.py",
                "result": {
                    "is_success": False,
                    "stdout": "1 failed in 0.02s",
                    "exit_code": 1,
                    "total_tests": 1,
                    "failures": 1,
                },
            },
        ]
        await repo.update_task_phase(
            task_id=test_task_id,
            phase=WorkflowPhase.FINISHED,
            status=TaskStatus.COMPLETED,
            test_results=stored_results,
        )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/v1/tasks/{test_task_id}/detail")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["id"] == test_task_id
        assert len(data["test_results"]) == 2

        # Verify successful test record
        test_1 = data["test_results"][0]
        assert test_1["command"] == "pytest -v"
        assert test_1["passed"] is True
        assert test_1["total_tests"] == 1
        assert test_1["failures"] == 0

        # Verify failed test record
        test_2 = data["test_results"][1]
        assert test_2["command"] == "pytest -v tests/test_extra.py"
        assert test_2["passed"] is False
        assert test_2["failures"] == 1


@pytest.mark.asyncio
async def test_get_task_detail_with_pending_approval():
    """Verify GET /tasks/{task_id}/detail returns HTTP 200 and serializes pending_approval cleanly."""
    import uuid
    from app.database.session import get_session_factory
    from app.database.repository import TaskRepository
    from app.models.enums import TaskStatus, WorkflowPhase

    test_task_id = f"task_appr_detail_{uuid.uuid4().hex[:8]}"

    session_factory = get_session_factory()
    async with session_factory() as session:
        repo = TaskRepository(session)
        await repo.create_task(
            task_id=test_task_id,
            repository_url="https://github.com/example/test-appr",
            user_instruction="Delete sensitive file",
            workspace_path="/tmp/test_appr",
        )
        await repo.update_task_phase(
            task_id=test_task_id,
            phase=WorkflowPhase.CODING,
            status=TaskStatus.PAUSED_FOR_APPROVAL,
        )
        await repo.create_approval_request(
            approval_id=f"appr_{test_task_id}_delete_file",
            task_id=test_task_id,
            action_type="tool_execution",
            tool_name="delete_file",
            action_payload={"file_path": "sensitive.env"},
        )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/v1/tasks/{test_task_id}/detail")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["id"] == test_task_id
        assert data["status"] == "paused_for_approval"

        # Verify pending_approval structure
        pending_appr = data["pending_approval"]
        assert pending_appr is not None
        assert pending_appr["approval_id"] == f"appr_{test_task_id}_delete_file"
        assert pending_appr["tool_name"] == "delete_file"
        assert pending_appr["action_type"] == "tool_execution"
        assert pending_appr["status"] == "pending"
        # Verify both payload and action_payload are present and matched
        assert pending_appr["action_payload"] == {"file_path": "sensitive.env"}
        assert pending_appr["payload"] == {"file_path": "sensitive.env"}
        # Verify reason is present
        assert "delete_file" in pending_appr["reason"]
