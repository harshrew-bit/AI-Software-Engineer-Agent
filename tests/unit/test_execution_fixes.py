"""Targeted Unit & Integration Tests validating all 8 execution fixes."""

import json
from pathlib import Path
from unittest.mock import MagicMock
import pytest

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
