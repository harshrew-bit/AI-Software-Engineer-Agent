"""LangGraph StateGraph Builder and Compiler."""

import logging
from typing import Any, Optional
from langgraph.graph import END, START, StateGraph

from app.graph.edges import should_continue_coding, should_continue_testing
from app.graph.nodes import (
    WorkflowContext,
    coding_node,
    commit_node,
    debugging_node,
    planning_node,
    pull_request_node,
    repository_analysis_node,
    review_node,
    testing_node,
)
from app.graph.state import GraphState
from app.llm.base import BaseLLMClient
from app.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


def build_agent_graph(
    llm_client: BaseLLMClient,
    tool_registry: Optional[ToolRegistry] = None,
    repository: Optional[Any] = None,
    checkpointer: Optional[Any] = None,
    settings: Optional[Any] = None,
):
    """Construct and compile the autonomous software engineering LangGraph state machine."""
    context = WorkflowContext(
        llm_client=llm_client,
        tool_registry=tool_registry,
        repository=repository,
        settings=settings,
    )
    workflow = StateGraph(GraphState)

    # 1. Add Async Nodes (wrapping with context)
    async def _analysis_node(state: GraphState) -> GraphState:
        return await repository_analysis_node(state, context)

    async def _planning_node(state: GraphState) -> GraphState:
        return await planning_node(state, context)

    async def _coding_node(state: GraphState) -> GraphState:
        return await coding_node(state, context)

    async def _testing_node(state: GraphState) -> GraphState:
        return await testing_node(state, context)

    async def _debugging_node(state: GraphState) -> GraphState:
        return await debugging_node(state, context)

    async def _review_node(state: GraphState) -> GraphState:
        return await review_node(state, context)

    async def _commit_node(state: GraphState) -> GraphState:
        return await commit_node(state, context)

    async def _pull_request_node(state: GraphState) -> GraphState:
        return await pull_request_node(state, context)

    workflow.add_node("repository_analysis", _analysis_node)
    workflow.add_node("planning", _planning_node)
    workflow.add_node("coding", _coding_node)
    workflow.add_node("testing", _testing_node)
    workflow.add_node("debugging", _debugging_node)
    workflow.add_node("review", _review_node)
    workflow.add_node("commit", _commit_node)
    workflow.add_node("pull_request", _pull_request_node)

    # 2. Add Fixed Edges
    workflow.add_edge(START, "repository_analysis")
    workflow.add_edge("repository_analysis", "planning")
    workflow.add_edge("planning", "coding")

    # 3. Add Conditional Routing Edge from Coding (for human approval pauses)
    workflow.add_conditional_edges(
        "coding",
        should_continue_coding,
        {
            "testing": "testing",
            END: END,
        },
    )

    # 4. Add Conditional Routing Edge from Testing
    workflow.add_conditional_edges(
        "testing",
        should_continue_testing,
        {
            "review": "review",
            "debugging": "debugging",
            END: END,
        },
    )

    # 4. Add Debugging Loop back to Coding
    workflow.add_edge("debugging", "coding")

    # 5. Add Review -> Commit -> Pull Request -> END
    workflow.add_edge("review", "commit")
    workflow.add_edge("commit", "pull_request")
    workflow.add_edge("pull_request", END)

    # Compile the graph (with optional checkpointer)
    app = workflow.compile(checkpointer=checkpointer)
    logger.info("Compiled LangGraph Agent Workflow with Pull Request stage successfully.")
    return app
