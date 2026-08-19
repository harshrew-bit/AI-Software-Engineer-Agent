import logging
from langgraph.graph import END

from app.graph.state import GraphState

logger = logging.getLogger(__name__)


def should_continue_coding(
    state: GraphState,
) -> str:
    """Evaluate whether coding paused for human approval or should proceed to testing."""
    task_id = state.get("task_id", "unknown")
    if state.get("pending_approval"):
        logger.info(f"[{task_id}] Pending human approval detected. Pausing graph execution at 'coding'.")
        return END
    return "testing"


def should_continue_testing(
    state: GraphState,
) -> str:
    """Evaluate test results and determine whether to proceed to review, retry via debugging, or terminate on failure."""
    task_id = state.get("task_id", "unknown")
    passed = state.get("latest_test_passed", False)
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 5)

    if passed:
        logger.info(f"[{task_id}] All tests passed. Routing to 'review'.")
        return "review"

    if retry_count < max_retries:
        logger.info(
            f"[{task_id}] Tests failed. Retry {retry_count + 1}/{max_retries}. Routing to 'debugging'."
        )
        return "debugging"

    logger.warning(
        f"[{task_id}] Tests failed and max retries ({max_retries}) reached. Terminating as failed."
    )
    return END
