"""Unit & Integration tests for LangGraph Workflow execution."""

from pathlib import Path
import pytest

from app.agents.schemas import (
    DebugAnalysisOutput,
    PlanGenerationOutput,
    ReviewSummaryOutput,
)
from app.graph.builder import build_agent_graph
from app.graph.edges import should_continue_testing
from app.graph.state import GraphState
from app.llm.base import LLMResponse, ToolCallRequest
from app.llm.mock import MockLLMClient
from app.models.state import PlanStep
from app.repository.git_manager import GitWorkspaceManager
from app.tools.registry import create_default_tool_registry


def test_should_continue_testing_edges():
    """Test conditional edge routing logic."""
    # 1. Tests passed -> route to review
    state_pass: GraphState = {"latest_test_passed": True, "retry_count": 0, "max_retries": 3}
    assert should_continue_testing(state_pass) == "review"

    # 2. Tests failed & retry < max -> route to debugging
    state_fail: GraphState = {"latest_test_passed": False, "retry_count": 1, "max_retries": 3}
    assert should_continue_testing(state_fail) == "debugging"

    # 3. Tests failed & retry >= max -> route to END (__end__)
    state_max_retry: GraphState = {"latest_test_passed": False, "retry_count": 3, "max_retries": 3}
    assert should_continue_testing(state_max_retry) == "__end__"


@pytest.mark.asyncio
async def test_full_graph_workflow_single_pass(tmp_path, test_settings):
    """Test end-to-end execution of compiled LangGraph with single pass."""
    ws = tmp_path / "workspace"
    git_manager = GitWorkspaceManager(task_id="task-graph-1", workspace_path=ws)
    git_manager.init_local_empty_repo()

    # Initial sample test file that passes
    (ws / "test_calc.py").write_text("def test_add():\n    assert 1 + 1 == 2\n")
    git_manager.commit("Initial test setup")

    mock_llm = MockLLMClient()

    # 1. Planner Output
    mock_llm.set_structured_response(
        "PlanGenerationOutput",
        PlanGenerationOutput(
            objective="Add calculator feature",
            architecture_overview="Add calc.py with add function",
            steps=[PlanStep(step_id=1, title="Create calc", description="Create calc.py")],
        ),
    )

    # 2. Coder Tool Call
    mock_llm.add_canned_response(
        LLMResponse(
            content="Creating calc.py",
            tool_calls=[
                ToolCallRequest(
                    id="call_1",
                    name="create_file",
                    arguments={"file_path": "calc.py", "content": "def add(a, b):\n    return a + b\n"},
                )
            ],
        )
    )

    # 3. Reviewer Output
    mock_llm.set_structured_response(
        "ReviewSummaryOutput",
        ReviewSummaryOutput(
            summary="Added calc.py with add function",
            commit_message="feat: add calculator function",
            is_ready_for_commit=True,
        ),
    )

    app = build_agent_graph(llm_client=mock_llm, tool_registry=create_default_tool_registry(), settings=test_settings)

    initial_state: GraphState = {
        "task_id": "task-graph-1",
        "repository_url": "https://github.com/example/calc",
        "base_branch": "main",
        "working_branch": "agent-fix/task-graph-1",
        "workspace_path": str(ws),
        "user_instruction": "Add calculator add function",
        "max_retries": 3,
        "retry_count": 0,
    }

    final_state = await app.ainvoke(initial_state)

    assert final_state["current_phase"] in ("commit", "pull_request")
    assert final_state["latest_test_passed"] is True
    assert final_state["commit_sha"] is not None
    assert (ws / "calc.py").exists()


@pytest.mark.asyncio
async def test_graph_workflow_with_debug_retry_loop(tmp_path, test_settings):
    """Test iterative self-healing test & debug loop."""
    ws = tmp_path / "workspace_debug"
    git_manager = GitWorkspaceManager(task_id="task-graph-debug", workspace_path=ws)
    git_manager.init_local_empty_repo()

    # Initial test file expecting multiply function
    (ws / "test_multiply.py").write_text("import multiply\ndef test_mult():\n    assert multiply.multiply(3, 4) == 12\n")
    git_manager.commit("Initial multiply test")

    mock_llm = MockLLMClient()

    # 1. Planner Output
    mock_llm.set_structured_response(
        "PlanGenerationOutput",
        PlanGenerationOutput(
            objective="Implement multiply",
            architecture_overview="Create multiply.py",
            steps=[PlanStep(step_id=1, title="Create multiply.py", description="Write function")],
        ),
    )

    # 2. Coder Turn 1 (Buggy implementation: return a + b instead of a * b)
    mock_llm.add_canned_response(
        LLMResponse(
            content="Creating multiply.py with bug",
            tool_calls=[
                ToolCallRequest(
                    id="call_bug",
                    name="create_file",
                    arguments={"file_path": "multiply.py", "content": "def multiply(a, b):\n    return a + b\n"},
                )
            ],
        )
    )
    # Turn 1 completes coding
    mock_llm.add_canned_response(LLMResponse(content="Completed initial implementation", tool_calls=[]))

    # 3. Debugger Output (Analyzing failure: 7 != 12)
    mock_llm.set_structured_response(
        "DebugAnalysisOutput",
        DebugAnalysisOutput(
            root_cause="Used addition '+' instead of multiplication '*'",
            proposed_fix="Change return a + b to return a * b",
            files_to_modify=["multiply.py"],
        ),
    )

    # 4. Coder Turn 2 (Fixing the bug)
    mock_llm.add_canned_response(
        LLMResponse(
            content="Fixing multiply.py",
            tool_calls=[
                ToolCallRequest(
                    id="call_fix",
                    name="modify_file",
                    arguments={
                        "file_path": "multiply.py",
                        "replacements": [
                            {"old_content": "return a + b", "new_content": "return a * b"}
                        ],
                    },
                )
            ],
        )
    )
    # Turn 2 completes coding
    mock_llm.add_canned_response(LLMResponse(content="Completed fix", tool_calls=[]))

    # 5. Reviewer Output
    mock_llm.set_structured_response(
        "ReviewSummaryOutput",
        ReviewSummaryOutput(
            summary="Implemented and fixed multiply function",
            commit_message="feat: implement multiply function",
            is_ready_for_commit=True,
        ),
    )

    app = build_agent_graph(llm_client=mock_llm, tool_registry=create_default_tool_registry(), settings=test_settings)

    initial_state: GraphState = {
        "task_id": "task-graph-debug",
        "repository_url": "https://github.com/example/math",
        "base_branch": "main",
        "working_branch": "agent-fix/task-graph-debug",
        "workspace_path": str(ws),
        "user_instruction": "Implement multiply module",
        "max_retries": 3,
        "retry_count": 0,
    }

    final_state = await app.ainvoke(initial_state)

    # Verified that it entered debugging, looped back to coding, and succeeded on second test pass!
    assert final_state["retry_count"] == 1
    assert final_state["latest_test_passed"] is True
    assert final_state["current_phase"] in ("commit", "pull_request")
    assert "return a * b" in (ws / "multiply.py").read_text()
