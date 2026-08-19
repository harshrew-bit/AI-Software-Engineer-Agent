"""Targeted Unit & Integration Tests validating all 8 execution fixes."""

import json
from pathlib import Path
from unittest.mock import MagicMock
import pytest
import asyncio

from app.agents.schemas import DebugAnalysisOutput, PlanGenerationOutput, ReviewSummaryOutput
from app.database.repository import TaskRepository
from app.graph.builder import build_agent_graph
from app.graph.edges import should_continue_testing
from app.graph.nodes import WorkflowContext, coding_node, repository_analysis_node
from app.graph.state import GraphState
from app.llm.base import LLMMessage, LLMResponse, ToolCallRequest, ToolDefinition
from app.llm.gemini import GeminiLLMClient
from app.llm.mock import MockLLMClient
from app.models.enums import TaskStatus, WorkflowPhase
from app.models.state import PlanStep
from app.repository.git_manager import GitWorkspaceManager
from app.sandbox.local import LocalSubprocessSandbox
from app.services.task_service import TaskManagerService
from app.tools.base import ToolExecutionContext
from app.tools.registry import create_default_tool_registry


# --- 1. Test Gemini Tool-Calling Format & Extraction ---
def test_gemini_tool_definition_formatting():
    """Verify GeminiLLMClient converts ToolDefinition to Interactions API format."""
    client = GeminiLLMClient(api_key="test-key")
    tool = ToolDefinition(
        name="create_file",
        description="Creates a file on disk",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["file_path", "content"],
        },
    )

    formatted = client._format_tools_for_gemini([tool])
    assert len(formatted) == 1
    assert formatted[0]["type"] == "function"
    assert formatted[0]["name"] == "create_file"
    assert formatted[0]["description"] == "Creates a file on disk"
    assert "file_path" in formatted[0]["parameters"]["properties"]


@pytest.mark.asyncio
async def test_gemini_initial_request_sends_normal_string_input():
    """Requirement 17a: Verify initial Gemini request sends normal string input with system_instruction and tools."""
    client = GeminiLLMClient(api_key="test-key")
    mock_genai_client = MagicMock()
    mock_interaction = MagicMock()
    mock_interaction.id = "int_001"
    mock_interaction.output_text = "I will list the files."
    mock_interaction.steps = []
    mock_interaction.usage = None
    mock_genai_client.interactions.create.return_value = mock_interaction
    client._client = mock_genai_client

    tools = [
        ToolDefinition(name="list_files", description="List repo files", parameters={"type": "object"})
    ]

    await client.generate(
        messages=[LLMMessage(role="user", content="List all files in repo")],
        system_instruction="You are an expert AI engineer.",
        tools=tools,
        previous_interaction_id=None,
    )

    kwargs = mock_genai_client.interactions.create.call_args[1]
    # Initial request: string input
    assert isinstance(kwargs["input"], str)
    assert kwargs["input"] == "List all files in repo"
    assert kwargs["system_instruction"] == "You are an expert AI engineer."
    assert "previous_interaction_id" not in kwargs
    assert len(kwargs["tools"]) == 1
    assert kwargs["tools"][0]["name"] == "list_files"

@pytest.mark.asyncio
async def test_gemini_retries_on_429_and_succeeds(monkeypatch):
    """Gemini 429 errors should be retried using the configured retry delay."""
    client = GeminiLLMClient(api_key="test-key")
    mock_genai_client = MagicMock()

    mock_interaction = MagicMock()
    mock_interaction.id = "int_retry_success"
    mock_interaction.output_text = "Success after retry"
    mock_interaction.steps = []
    mock_interaction.usage = None

    rate_limit_error = Exception(
        "Error code: 429 - too_many_requests. Please retry in 0.1s."
    )

    mock_genai_client.interactions.create.side_effect = [
        rate_limit_error,
        mock_interaction,
    ]

    client._client = mock_genai_client
    client.max_retries = 2

    sleep_mock = MagicMock()

    async def fake_sleep(delay):
        sleep_mock(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    response = await client.generate(
        messages=[LLMMessage(role="user", content="Hello")],
    )

    assert response.content == "Success after retry"
    assert mock_genai_client.interactions.create.call_count == 2
    sleep_mock.assert_called_once_with(0.1)

@pytest.mark.asyncio
async def test_gemini_429_retries_are_bounded(monkeypatch):
    """Gemini 429 errors should eventually be raised after max retries."""
    client = GeminiLLMClient(api_key="test-key")
    mock_genai_client = MagicMock()

    rate_limit_error = Exception(
        "Error code: 429 - too_many_requests. Please retry in 0.1s."
    )

    mock_genai_client.interactions.create.side_effect = rate_limit_error
    client._client = mock_genai_client
    client.max_retries = 2

    async def fake_sleep(delay):
        pass

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    with pytest.raises(Exception, match="429"):
        await client.generate(
            messages=[LLMMessage(role="user", content="Hello")],
        )

    # Initial attempt + 2 retries
    assert mock_genai_client.interactions.create.call_count == 3

@pytest.mark.asyncio
async def test_gemini_structured_retries_on_429_and_succeeds(monkeypatch):
    """Gemini structured generation should retry 429 errors and then succeed."""
    client = GeminiLLMClient(api_key="test-key")
    mock_genai_client = MagicMock()

    mock_interaction = MagicMock()
    mock_interaction.output_text = (
        '{"objective": "Test objective", '
        '"architecture_overview": "Test architecture", '
        '"steps": []}'
    )

    rate_limit_error = Exception(
        "Error code: 429 - too_many_requests. Please retry in 0.1s."
    )

    mock_genai_client.interactions.create.side_effect = [
        rate_limit_error,
        mock_interaction,
    ]

    client._client = mock_genai_client
    client.max_retries = 2

    sleep_mock = MagicMock()

    async def fake_sleep(delay):
        sleep_mock(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    response = await client.generate_structured(
        prompt="Generate an empty plan.",
        response_schema=PlanGenerationOutput,
    )

    assert response is not None
    assert mock_genai_client.interactions.create.call_count == 2
    sleep_mock.assert_called_once_with(0.1)


@pytest.mark.asyncio
async def test_gemini_structured_429_retries_are_bounded(monkeypatch):
    """Gemini structured generation should raise after max 429 retries."""
    client = GeminiLLMClient(api_key="test-key")
    mock_genai_client = MagicMock()

    rate_limit_error = Exception(
        "Error code: 429 - too_many_requests. Please retry in 0.1s."
    )

    mock_genai_client.interactions.create.side_effect = rate_limit_error
    client._client = mock_genai_client
    client.max_retries = 2

    async def fake_sleep(delay):
        pass

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    with pytest.raises(Exception, match="429"):
        await client.generate_structured(
            prompt="Generate an empty plan.",
            response_schema=PlanGenerationOutput,
        )

    # Initial attempt + 2 retries
    assert mock_genai_client.interactions.create.call_count == 3


@pytest.mark.asyncio
async def test_gemini_tool_result_turn_sends_structured_function_result():
    """Requirement 17b-e, g, h: Verify tool-result turn sends structured function_result input."""
    client = GeminiLLMClient(api_key="test-key")
    mock_genai_client = MagicMock()
    mock_interaction = MagicMock()
    mock_interaction.id = "int_002"
    mock_interaction.output_text = "Files found."
    mock_interaction.steps = []
    mock_interaction.usage = None
    mock_genai_client.interactions.create.return_value = mock_interaction
    client._client = mock_genai_client

    tools = [
        ToolDefinition(name="list_files", description="List repo files", parameters={"type": "object"})
    ]

    # Tool result message
    tool_msg = LLMMessage(
        role="tool",
        content="No matching files found.",
        name="list_files",
        tool_call_id="call_6f4e7946",
    )

    await client.generate(
        messages=[tool_msg],
        tools=tools,
        previous_interaction_id="int_001",
    )

    kwargs = mock_genai_client.interactions.create.call_args[1]

    # 17b: input is a structured list (not a plain string)
    assert isinstance(kwargs["input"], list)
    assert len(kwargs["input"]) == 1

    func_result = kwargs["input"][0]
    # 17c: correct name
    assert func_result["name"] == "list_files"
    # 17d: correct call_id
    assert func_result["call_id"] == "call_6f4e7946"
    assert func_result["type"] == "function_result"
    # 17e: result format is [{"type": "text", "text": "..."}]
    assert func_result["result"] == [
        {
            "type": "text",
            "text": "No matching files found.",
        }
    ]

    # 17g: tools still supplied on subsequent interaction
    assert len(kwargs["tools"]) == 1
    assert kwargs["tools"][0]["name"] == "list_files"
    # 17h: previous_interaction_id is supplied
    assert kwargs["previous_interaction_id"] == "int_001"


@pytest.mark.asyncio
async def test_gemini_multiple_function_results_in_single_turn():
    """Requirement 17f: Support multiple tool results in one model follow-up interaction."""
    client = GeminiLLMClient(api_key="test-key")
    mock_genai_client = MagicMock()
    mock_interaction = MagicMock()
    mock_interaction.id = "int_003"
    mock_interaction.output_text = "Done executing both tools."
    mock_interaction.steps = []
    mock_interaction.usage = None
    mock_genai_client.interactions.create.return_value = mock_interaction
    client._client = mock_genai_client

    tools = [
        ToolDefinition(name="read_file", description="Read file", parameters={"type": "object"}),
        ToolDefinition(name="list_files", description="List files", parameters={"type": "object"}),
    ]

    tool_msg_1 = LLMMessage(
        role="tool",
        content="File content: def hello(): pass",
        name="read_file",
        tool_call_id="call_read_1",
    )
    tool_msg_2 = LLMMessage(
        role="tool",
        content="main.py\nutils.py",
        name="list_files",
        tool_call_id="call_list_2",
    )

    await client.generate(
        messages=[tool_msg_1, tool_msg_2],
        tools=tools,
        previous_interaction_id="int_002",
    )

    kwargs = mock_genai_client.interactions.create.call_args[1]

    assert isinstance(kwargs["input"], list)
    assert len(kwargs["input"]) == 2

    assert kwargs["input"][0]["type"] == "function_result"
    assert kwargs["input"][0]["name"] == "read_file"
    assert kwargs["input"][0]["call_id"] == "call_read_1"
    assert kwargs["input"][0]["result"][0]["text"] == "File content: def hello(): pass"

    assert kwargs["input"][1]["type"] == "function_result"
    assert kwargs["input"][1]["name"] == "list_files"
    assert kwargs["input"][1]["call_id"] == "call_list_2"
    assert kwargs["input"][1]["result"][0]["text"] == "main.py\nutils.py"

    assert kwargs["previous_interaction_id"] == "int_002"
    assert len(kwargs["tools"]) == 2


@pytest.mark.asyncio
async def test_gemini_regression_tool_message_must_not_become_string_when_previous_interaction_id_used():
    """Requirement 18: Regression test proving LLMMessage(role='tool') does NOT become '[TOOL RESULT ...]' string."""
    client = GeminiLLMClient(api_key="test-key")
    mock_genai_client = MagicMock()
    mock_interaction = MagicMock()
    mock_interaction.id = "int_004"
    mock_interaction.output_text = "Analysis finished."
    mock_interaction.steps = []
    mock_interaction.usage = None
    mock_genai_client.interactions.create.return_value = mock_interaction
    client._client = mock_genai_client

    tool_msg = LLMMessage(
        role="tool",
        content="No matching files found.",
        name="list_files",
        tool_call_id="call_6f4e7946",
    )

    await client.generate(
        messages=[tool_msg],
        previous_interaction_id="int_prev_999",
    )

    kwargs = mock_genai_client.interactions.create.call_args[1]

    # MUST NOT be a string like "[TOOL RESULT for list_files (call_id: call_6f4e7946)]:\nNo matching files found."
    assert not isinstance(kwargs["input"], str), "input must not be converted to string on tool turns with previous_interaction_id"
    assert isinstance(kwargs["input"], list)
    assert kwargs["input"][0]["type"] == "function_result"
    assert "[TOOL RESULT" not in json.dumps(kwargs["input"])


@pytest.mark.asyncio
async def test_gemini_generate_tool_call_extraction():
    """Verify GeminiLLMClient.generate parses function_call steps into ToolCallRequest."""
    client = GeminiLLMClient(api_key="test-key")

    # Mock the internal google.genai.Client interactions.create call
    mock_genai_client = MagicMock()
    mock_step = MagicMock()
    mock_step.type = "function_call"
    mock_step.name = "modify_file"
    mock_step.arguments = json.dumps({"file_path": "app.py", "replacements": []})
    mock_step.id = "call_step_123"

    mock_interaction = MagicMock()
    mock_interaction.id = "int_abc_123"
    mock_interaction.output_text = "Modifying app.py"
    mock_interaction.steps = [mock_step]
    mock_interaction.usage = None

    mock_genai_client.interactions.create.return_value = mock_interaction
    client._client = mock_genai_client

    response = await client.generate(
        messages=[LLMMessage(role="user", content="Fix bug")],
        tools=[
            ToolDefinition(
                name="modify_file",
                description="Modify file",
                parameters={"type": "object"},
            )
        ],
        previous_interaction_id="prev_int_001",
    )

    # Verify kwargs passed to interactions.create
    kwargs = mock_genai_client.interactions.create.call_args[1]
    assert kwargs["previous_interaction_id"] == "prev_int_001"
    assert len(kwargs["tools"]) == 1
    assert kwargs["tools"][0]["name"] == "modify_file"

    # Verify parsed tool calls
    assert response.has_tool_calls is True
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].name == "modify_file"
    assert response.tool_calls[0].arguments["file_path"] == "app.py"
    assert response.interaction_id == "int_abc_123"


# --- 2. Test Agentic Multi-Turn Tool Execution Loop ---
@pytest.mark.asyncio
async def test_coding_node_multi_turn_agentic_tool_loop(tmp_path):
    """Verify coding_node executes tools iteratively across multiple turns."""
    ws = tmp_path / "workspace_loop"
    git_manager = GitWorkspaceManager(task_id="task-loop-1", workspace_path=ws)
    git_manager.init_local_empty_repo()

    mock_llm = MockLLMClient()

    # Turn 1: Model creates helper file
    mock_llm.add_canned_response(
        LLMResponse(
            content="Creating helper.py",
            tool_calls=[
                ToolCallRequest(
                    id="call_helper",
                    name="create_file",
                    arguments={"file_path": "helper.py", "content": "def get_value():\n    return 42\n"},
                )
            ],
            interaction_id="int_turn_1",
        )
    )

    # Turn 2: Model creates main file referencing helper
    mock_llm.add_canned_response(
        LLMResponse(
            content="Creating main.py",
            tool_calls=[
                ToolCallRequest(
                    id="call_main",
                    name="create_file",
                    arguments={"file_path": "main.py", "content": "import helper\nprint(helper.get_value())\n"},
                )
            ],
            interaction_id="int_turn_2",
        )
    )

    # Turn 3: Model finishes
    mock_llm.add_canned_response(
        LLMResponse(
            content="Done implementing files.",
            tool_calls=[],
            interaction_id="int_turn_3",
        )
    )

    registry = create_default_tool_registry()
    context = WorkflowContext(llm_client=mock_llm, tool_registry=registry)

    state: GraphState = {
        "task_id": "task-loop-1",
        "repository_url": "https://github.com/example/repo",
        "base_branch": "main",
        "working_branch": "agent-fix/task-loop-1",
        "workspace_path": str(ws),
        "user_instruction": "Create helper and main modules",
        "plan": {"objective": "Create modules", "steps": []},
    }

    updated_state = await coding_node(state, context)

    # Both files created on disk through the multi-turn loop
    assert (ws / "helper.py").exists()
    assert (ws / "main.py").exists()
    assert len(updated_state["tool_history"]) == 2
    assert "helper.py" in updated_state["modified_files"]
    assert "main.py" in updated_state["modified_files"]


# --- 3. Test Tool Execution Database Persistence ---
@pytest.mark.asyncio
async def test_tool_execution_database_persistence(tmp_path, async_db_session):
    """Verify tool executions are persisted into the database tool_calls table."""
    ws = tmp_path / "workspace_db_audit"
    git_manager = GitWorkspaceManager(task_id="task-db-audit", workspace_path=ws)
    git_manager.init_local_empty_repo()

    repo = TaskRepository(async_db_session)
    await repo.create_task(
        task_id="task-db-audit",
        repository_url="https://github.com/example/audit",
        user_instruction="Create audited file",
        workspace_path=str(ws),
    )

    mock_llm = MockLLMClient()
    mock_llm.add_canned_response(
        LLMResponse(
            content="Creating audited file",
            tool_calls=[
                ToolCallRequest(
                    id="call_audit_1",
                    name="create_file",
                    arguments={"file_path": "audited.py", "content": "# audited content\n"},
                )
            ],
        )
    )
    mock_llm.add_canned_response(LLMResponse(content="Done", tool_calls=[]))

    registry = create_default_tool_registry()
    context = WorkflowContext(llm_client=mock_llm, tool_registry=registry, repository=repo)

    state: GraphState = {
        "task_id": "task-db-audit",
        "repository_url": "https://github.com/example/audit",
        "base_branch": "main",
        "working_branch": "agent-fix/task-db-audit",
        "workspace_path": str(ws),
        "user_instruction": "Create audited file",
        "plan": {"objective": "Audit test", "steps": []},
    }

    await coding_node(state, context)

    # Verify task in DB has tool_calls recorded
    db_task = await repo.get_task("task-db-audit", include_relations=True)
    assert db_task is not None
    assert len(db_task.tool_calls) >= 1
    assert any(tc.tool_name == "create_file" for tc in db_task.tool_calls)


# --- 4. Test Routing: Failed Tests Do NOT Proceed to Commit/PR ---
def test_failed_tests_routing_terminates_at_end():
    """Verify that after max retries, failed tests terminate at END and do NOT route to review."""
    state_failed_max: GraphState = {
        "task_id": "task-fail-routing",
        "latest_test_passed": False,
        "retry_count": 3,
        "max_retries": 3,
    }
    # Must route to END (__end__)
    route = should_continue_testing(state_failed_max)
    assert route == "__end__"


def test_successful_tests_proceed_to_review():
    """Verify that passing tests proceed directly to review."""
    state_pass: GraphState = {
        "task_id": "task-pass-routing",
        "latest_test_passed": True,
        "retry_count": 0,
        "max_retries": 3,
    }
    route = should_continue_testing(state_pass)
    assert route == "review"


# --- 5. Full End-to-End Workflow with Task Execution Failure Status Verification ---
@pytest.mark.asyncio
async def test_workflow_fails_when_tests_never_pass(tmp_path):
    """Verify full graph terminates at testing without committing when tests consistently fail."""
    ws = tmp_path / "workspace_failing_repo"
    git_manager = GitWorkspaceManager(task_id="task-failing", workspace_path=ws)
    git_manager.init_local_empty_repo()

    # Initial test file that always fails
    (ws / "test_failing.py").write_text("def test_always_fail():\n    assert False\n")
    git_manager.commit("Initial test setup")

    mock_llm = MockLLMClient()
    mock_llm.set_structured_response(
        "PlanGenerationOutput",
        PlanGenerationOutput(
            objective="Fix failing test",
            architecture_overview="Fix test",
            steps=[PlanStep(step_id=1, title="Fix", description="Fix test")],
        ),
    )
    mock_llm.set_structured_response(
        "DebugAnalysisOutput",
        DebugAnalysisOutput(
            root_cause="Test asserted False",
            proposed_fix="Cannot fix",
            files_to_modify=["test_failing.py"],
        ),
    )

    # Empty responses for coder turns
    mock_llm.add_canned_response(LLMResponse(content="Tried fix 1", tool_calls=[]))
    mock_llm.add_canned_response(LLMResponse(content="Tried fix 2", tool_calls=[]))

    app = build_agent_graph(llm_client=mock_llm, tool_registry=create_default_tool_registry())

    initial_state: GraphState = {
        "task_id": "task-failing",
        "repository_url": "https://github.com/example/fail",
        "base_branch": "main",
        "working_branch": "agent-fix/task-failing",
        "workspace_path": str(ws),
        "user_instruction": "Fix test",
        "max_retries": 1,
        "retry_count": 0,
    }

    final_state = await app.ainvoke(initial_state)

    # Final state terminated at testing, did NOT commit or create PR!
    assert final_state["current_phase"] == "testing"
    assert final_state["latest_test_passed"] is False
    assert final_state.get("commit_sha") is None
    assert final_state.get("pull_request_url") is None

def test_modify_file_tool_schema_resolves_pydantic_refs():
    """modify_file tool schema should not contain unresolved JSON Schema refs."""
    from app.tools.registry import create_default_tool_registry

    registry = create_default_tool_registry()
    tool = registry.get_tool("modify_file")

    parameters = tool.to_tool_definition().parameters

    schema_text = str(parameters)

    assert "$ref" not in schema_text
    assert "$defs" not in schema_text

    replacements = parameters["properties"]["replacements"]
    replacement_item = replacements["items"]

    assert replacement_item["type"] == "object"
    assert "old_content" in replacement_item["properties"]
    assert "new_content" in replacement_item["properties"]
    assert "start_line" in replacement_item["properties"]
    assert "end_line" in replacement_item["properties"]

    assert replacement_item["required"] == [
        "old_content",
        "new_content",
    ]


def test_gemini_quota_exhaustion_detection():
    """Verify GeminiLLMClient._is_rate_limit_error detects quota and resource exhausted errors."""
    client = GeminiLLMClient(api_key="test-key")

    # 1. Quota exceeded free tier string
    err_quota = Exception(
        "ResourceExhausted: Quota exceeded for metric: "
        "generativelanguage.googleapis.com/generate_content_free_tier_requests"
    )
    assert client._is_rate_limit_error(err_quota) is True

    # 2. 429 RESOURCE_EXHAUSTED string
    err_429 = Exception("429 RESOURCE_EXHAUSTED. Please retry in 10s.")
    assert client._is_rate_limit_error(err_429) is True

    # 3. Exception object with status_code attribute
    class MockStatusError(Exception):
        status_code = 429

    assert client._is_rate_limit_error(MockStatusError("Some rate error")) is True

    # 4. Non-rate-limit errors return False
    err_syntax = Exception("Invalid JSON payload: syntax error in request body")
    assert client._is_rate_limit_error(err_syntax) is False


@pytest.mark.asyncio
async def test_terminal_gemini_quota_failure_marks_task_as_failed(tmp_path, async_db_session, monkeypatch):
    """Verify workflow catches terminal Gemini quota exception and marks task as FAILED in DB."""
    import git

    # Setup local bare repo as the remote repository
    remote_dir = tmp_path / "remote_quota.git"
    remote_repo = git.Repo.init(str(remote_dir), bare=True)

    # Seed it with an initial commit
    seed_dir = tmp_path / "seed_quota"
    seed_repo = git.Repo.init(str(seed_dir))
    (seed_dir / "README.md").write_text("# Initial Repo")
    seed_repo.git.add(A=True)
    seed_repo.index.commit("Initial seed commit")
    seed_repo.create_head("main")
    seed_repo.create_remote("origin", str(remote_dir))
    seed_repo.git.push("origin", "main:main")

    ws = tmp_path / "workspace_quota_fail"

    repo = TaskRepository(async_db_session)
    await repo.create_task(
        task_id="task-quota-fail",
        repository_url=str(remote_dir),
        user_instruction="Implement feature",
        workspace_path=str(ws),
    )

    class MockSessionFactory:
        def __call__(self):
            return self

        async def __aenter__(self):
            return async_db_session

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    monkeypatch.setattr("app.services.task_service.get_session_factory", lambda: MockSessionFactory())

    # Mock LLM that raises terminal quota exhaustion error during planning
    class QuotaExhaustedLLMClient(MockLLMClient):
        async def generate_structured(self, *args, **kwargs):
            raise Exception(
                "Gemini API rate limit persisted after 2 retries: "
                "Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests"
            )

    quota_llm = QuotaExhaustedLLMClient()
    task_svc = TaskManagerService(llm_client=quota_llm)

    # Execute workflow which should catch terminal Gemini quota error
    await task_svc._execute_workflow(
        task_id="task-quota-fail",
        repository_url=str(remote_dir),
        user_instruction="Implement feature",
        workspace_path=str(ws),
        base_branch="main",
        working_branch="agent-fix/task-quota-fail",
        max_retries=1,
    )

    # Verify task in DB is FAILED with useful error message, NOT RUNNING
    db_task = await repo.get_task("task-quota-fail")
    assert db_task is not None
    assert db_task.status == TaskStatus.FAILED.value
    assert db_task.current_phase == WorkflowPhase.FINISHED.value
    assert "Quota exceeded" in db_task.error_message


def test_uvicorn_reload_excludes_temp_workspaces():
    """Verify settings configure Uvicorn to watch only app/ and exclude temp_workspaces/."""
    from app.config import get_settings

    settings = get_settings()
    assert "app" in settings.reload_dirs
    assert any("temp_workspaces" in pat for pat in settings.reload_excludes)


@pytest.mark.asyncio
async def test_lifespan_recovers_orphaned_tasks(async_db_session, monkeypatch):
    """Verify application lifespan recovers orphaned RUNNING tasks on server startup."""
    from unittest.mock import AsyncMock
    from app.main import lifespan, app

    repo = TaskRepository(async_db_session)
    # Create an orphaned task in RUNNING state
    await repo.create_task(
        task_id="task-orphaned-1",
        repository_url="https://github.com/example/orphan",
        user_instruction="Fix issue",
        workspace_path="/tmp/orphan",
    )
    await repo.update_task_phase(
        task_id="task-orphaned-1",
        phase=WorkflowPhase.CODING,
        status=TaskStatus.RUNNING,
    )

    class MockSessionFactory:
        def __call__(self):
            return self

        async def __aenter__(self):
            return async_db_session

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    monkeypatch.setattr("app.main.get_session_factory", lambda: MockSessionFactory())
    monkeypatch.setattr("app.main.init_db", AsyncMock())

    # Run lifespan context
    async with lifespan(app):
        pass

    # Verify task is recovered to FAILED
    task = await repo.get_task("task-orphaned-1")
    assert task.status == TaskStatus.FAILED.value
    assert task.current_phase == WorkflowPhase.FINISHED.value
    assert "interrupted" in task.error_message.lower()