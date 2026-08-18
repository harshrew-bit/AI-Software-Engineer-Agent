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
