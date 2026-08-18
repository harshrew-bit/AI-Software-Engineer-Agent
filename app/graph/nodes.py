"""LangGraph Node Implementations with Agentic Tool Execution Loop & DB Auditing."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from app.agents.prompts import (
    CODER_SYSTEM_PROMPT,
    DEBUGGER_SYSTEM_PROMPT,
    PLANNER_SYSTEM_PROMPT,
    REVIEWER_SYSTEM_PROMPT,
)
from app.agents.schemas import (
    DebugAnalysisOutput,
    PlanGenerationOutput,
    ReviewSummaryOutput,
)
from app.config import get_settings
from app.graph.state import GraphState
from app.llm.base import BaseLLMClient, LLMMessage
from app.models.enums import TaskStatus, WorkflowPhase
from app.models.state import AgentPlan, PlanStep
from app.models.task import TaskEvent
from app.repository.git_manager import GitWorkspaceManager
from app.sandbox.factory import get_sandbox
from app.services.event_bus import global_event_bus
from app.tools.base import ToolExecutionContext
from app.tools.registry import ToolRegistry, create_default_tool_registry

logger = logging.getLogger(__name__)


class WorkflowContext:
    """Dependency container passed to nodes during graph execution."""

    def __init__(
        self,
        llm_client: BaseLLMClient,
        tool_registry: Optional[ToolRegistry] = None,
        repository: Optional[Any] = None,
    ):
        self.llm_client = llm_client
        self.tool_registry = tool_registry or create_default_tool_registry()
        self.repository = repository
        self.settings = get_settings()


# --- Node 1: Repository Analysis ---
async def repository_analysis_node(state: GraphState, context: WorkflowContext) -> GraphState:
    """Analyze repo structure, find relevant files and detect test configurations."""
    task_id = state["task_id"]
    logger.info(f"[{task_id}] Running Repository Analysis Node")
    workspace_path = Path(state["workspace_path"])
    git_manager = GitWorkspaceManager(task_id=task_id, workspace_path=workspace_path)
    sandbox = get_sandbox(workspace_path=workspace_path)

    tool_context = ToolExecutionContext(
        task_id=task_id,
        workspace_path=workspace_path,
        git_manager=git_manager,
        sandbox=sandbox,
        settings=context.settings,
        repository=context.repository,
    )

    await global_event_bus.publish(
        task_id,
        TaskEvent(
            task_id=task_id,
            event_type="repository_analysis",
            phase=WorkflowPhase.REPOSITORY_ANALYSIS,
            message="Analyzing repository files and test configurations...",
        ),
    )

    # 1. List repository files
    list_tool = context.tool_registry.get_tool("list_files")
    list_res = await context.tool_registry.dispatch(
        "list_files",
        {"directory": ".", "recursive": True},
        tool_context,
    )
    file_list = list_res.output.splitlines() if list_res.success and list_res.output else []

    # 2. Detect language & framework
    detected_framework = "Python"
    test_command = "pytest -v"
    if any(f.endswith(".py") for f in file_list):
        detected_framework = "Python"
        test_command = "pytest -v"
    elif any(f.endswith("package.json") for f in file_list):
        detected_framework = "Node.js"
        test_command = "npm test"
    elif any(f.endswith("Cargo.toml") for f in file_list):
        detected_framework = "Rust"
        test_command = "cargo test"

    summary = (
        f"Repository contains {len(file_list)} files.\n"
        f"Detected Framework: {detected_framework}\n"
        f"Detected Test Command: {test_command}\n"
        f"Key files:\n" + "\n".join(f"  - {f}" for f in file_list[:15])
    )

    return {
        **state,
        "current_phase": WorkflowPhase.REPOSITORY_ANALYSIS.value,
        "file_list": file_list,
        "detected_framework": detected_framework,
        "detected_test_command": test_command,
        "repo_summary": summary,
    }


# --- Node 2: Implementation Planning ---
async def planning_node(state: GraphState, context: WorkflowContext) -> GraphState:
    """Generate structured implementation plan."""
    task_id = state["task_id"]
    logger.info(f"[{task_id}] Running Planning Node")

    await global_event_bus.publish(
        task_id,
        TaskEvent(
            task_id=task_id,
            event_type="planning",
            phase=WorkflowPhase.PLANNING,
            message="Generating implementation plan...",
        ),
    )

    prompt = (
        f"USER INSTRUCTION:\n{state['user_instruction']}\n\n"
        f"REPOSITORY CONTEXT:\n{state.get('repo_summary', '')}\n\n"
        f"AVAILABLE FILES:\n" + "\n".join(state.get("file_list", [])[:30])
    )

    plan_output: PlanGenerationOutput = await context.llm_client.generate_structured(
        prompt=prompt,
        response_schema=PlanGenerationOutput,
        system_instruction=PLANNER_SYSTEM_PROMPT,
    )

    agent_plan = AgentPlan(
        objective=plan_output.objective,
        architecture_overview=plan_output.architecture_overview,
        steps=plan_output.steps,
    )

    await global_event_bus.publish(
        task_id,
        TaskEvent(
            task_id=task_id,
            event_type="planning_completed",
            phase=WorkflowPhase.PLANNING,
            message=f"Plan generated: {agent_plan.objective}",
            data={"objective": agent_plan.objective, "steps_count": len(agent_plan.steps)},
        ),
    )

    return {
        **state,
        "current_phase": WorkflowPhase.PLANNING.value,
        "plan": agent_plan.model_dump(),
    }


# --- Node 3: Coding (Agentic Multi-Turn Tool Execution Loop) ---
async def coding_node(state: GraphState, context: WorkflowContext) -> GraphState:
    """Apply file creations, modifications, and shell operations via iterative agentic tool loop."""
    task_id = state["task_id"]
    retry_num = state.get("retry_count", 0)
    logger.info(f"[{task_id}] Running Coding Node (Attempt #{retry_num + 1})")
    workspace_path = Path(state["workspace_path"])
    git_manager = GitWorkspaceManager(task_id=task_id, workspace_path=workspace_path)
    sandbox = get_sandbox(workspace_path=workspace_path)

    tool_context = ToolExecutionContext(
        task_id=task_id,
        workspace_path=workspace_path,
        git_manager=git_manager,
        sandbox=sandbox,
        settings=context.settings,
        repository=context.repository,
    )

    await global_event_bus.publish(
        task_id,
        TaskEvent(
            task_id=task_id,
            event_type="coding",
            phase=WorkflowPhase.CODING,
            message=f"Agent starting coding phase (Attempt #{retry_num + 1})...",
        ),
    )

    plan_data = state.get("plan", {})
    debug_guidance = state.get("debug_guidance")

    coder_prompt = (
        f"USER INSTRUCTION:\n{state['user_instruction']}\n\n"
        f"IMPLEMENTATION PLAN:\n{plan_data}\n\n"
    )
    if debug_guidance:
        coder_prompt += f"DEBUGGER GUIDANCE & REQUIRED FIX:\n{debug_guidance}\n\n"

    tool_defs = context.tool_registry.get_tool_definitions()
    tool_history = list(state.get("tool_history", []))
    modified_files: Set[str] = set(state.get("modified_files", []))
    pending_approval: Optional[Dict[str, Any]] = None

    messages: List[LLMMessage] = [LLMMessage(role="user", content=coder_prompt)]
    last_interaction_id: Optional[str] = None
    max_tool_rounds = 10

    for round_idx in range(max_tool_rounds):
        logger.info(f"[{task_id}] Coding round {round_idx + 1}/{max_tool_rounds}")
        response = await context.llm_client.generate(
            messages=messages,
            system_instruction=CODER_SYSTEM_PROMPT,
            tools=tool_defs,
            previous_interaction_id=last_interaction_id,
        )

        last_interaction_id = response.interaction_id

        if not response.has_tool_calls:
            logger.info(f"[{task_id}] Model finished coding turn without additional tool calls.")
            if response.content:
                messages.append(LLMMessage(role="assistant", content=response.content))
            break

        # Execute each requested tool call through ToolRegistry (which performs safety checks & DB auditing)
        for tool_call in response.tool_calls:
            logger.info(f"[{task_id}] Executing tool '{tool_call.name}' with args {tool_call.arguments}")

            tool_res = await context.tool_registry.dispatch(
                tool_name=tool_call.name,
                arguments=tool_call.arguments,
                context=tool_context,
            )

            tool_history.append(tool_res.model_dump())

            await global_event_bus.publish(
                task_id,
                TaskEvent(
                    task_id=task_id,
                    event_type="tool_execution",
                    phase=WorkflowPhase.CODING,
                    message=f"Executed {tool_call.name} (success={tool_res.success})",
                    data={
                        "tool_name": tool_call.name,
                        "success": tool_res.success,
                        "requires_approval": tool_res.requires_approval,
                        "execution_time_ms": tool_res.execution_time_ms,
                    },
                ),
            )

            # Check if intercepted by safety gate
            if tool_res.requires_approval:
                logger.warning(f"[{task_id}] Action '{tool_call.name}' paused for human approval.")
                pending_approval = {
                    "approval_id": f"appr_{task_id}_{tool_call.name}",
                    "action_type": "tool_execution",
                    "tool_name": tool_call.name,
                    "action_payload": tool_call.arguments,
                    "status": "pending",
                }
                await global_event_bus.publish(
                    task_id,
                    TaskEvent(
                        task_id=task_id,
                        event_type="approval_required",
                        phase=WorkflowPhase.CODING,
                        message=f"Human approval required for action: {tool_call.name}",
                        data=pending_approval,
                    ),
                )
                break

            # Track modified files
            if tool_call.name in ("create_file", "modify_file", "delete_file"):
                target_f = tool_call.arguments.get("file_path")
                if target_f:
                    modified_files.add(target_f)

            # Send function output or error back to the model
            if tool_res.success:
                result_str = tool_res.output if tool_res.output else "Tool executed successfully."
            else:
                result_str = f"Error executing {tool_call.name}: {tool_res.error}"

            messages.append(
                LLMMessage(
                    role="tool",
                    content=result_str,
                    name=tool_call.name,
                    tool_call_id=tool_call.id,
                )
            )

        if pending_approval:
            break

    # Inspect git status for all modified and untracked files
    try:
        status = git_manager.get_status()
        for f in status.get("modified", []) + status.get("untracked", []):
            modified_files.add(f)
    except Exception as e:
        logger.debug(f"Git status inspection note: {e}")

    return {
        **state,
        "current_phase": WorkflowPhase.CODING.value,
        "tool_history": tool_history,
        "modified_files": sorted(list(modified_files)),
        "pending_approval": pending_approval,
    }


# --- Node 4: Testing ---
async def testing_node(state: GraphState, context: WorkflowContext) -> GraphState:
    """Execute tests inside the sandbox and evaluate results."""
    task_id = state["task_id"]
    logger.info(f"[{task_id}] Running Testing Node")
    workspace_path = Path(state["workspace_path"])
    git_manager = GitWorkspaceManager(task_id=task_id, workspace_path=workspace_path)
    sandbox = get_sandbox(workspace_path=workspace_path)

    tool_context = ToolExecutionContext(
        task_id=task_id,
        workspace_path=workspace_path,
        git_manager=git_manager,
        sandbox=sandbox,
        settings=context.settings,
        repository=context.repository,
    )

    test_cmd = state.get("detected_test_command") or "pytest -v"

    await global_event_bus.publish(
        task_id,
        TaskEvent(
            task_id=task_id,
            event_type="testing",
            phase=WorkflowPhase.TESTING,
            message=f"Running tests in sandbox: '{test_cmd}'...",
        ),
    )

    test_res = await context.tool_registry.dispatch(
        "run_tests",
        {"test_command": test_cmd},
        tool_context,
    )

    test_passed = test_res.success
    test_results = list(state.get("test_results", []))
    test_results.append({
        "command": test_cmd,
        "is_success": test_passed,
        "output": test_res.output or test_res.error or "",
        "exit_code": test_res.exit_code,
        "metadata": test_res.metadata,
    })

    await global_event_bus.publish(
        task_id,
        TaskEvent(
            task_id=task_id,
            event_type="testing_completed",
            phase=WorkflowPhase.TESTING,
            message=f"Tests completed: {'PASSED' if test_passed else 'FAILED'}",
            data={"passed": test_passed, "exit_code": test_res.exit_code},
        ),
    )

    return {
        **state,
        "current_phase": WorkflowPhase.TESTING.value,
        "latest_test_passed": test_passed,
        "test_results": test_results,
    }


# --- Node 5: Debugging ---
async def debugging_node(state: GraphState, context: WorkflowContext) -> GraphState:
    """Diagnose test failures and generate targeted corrective fix instructions."""
    task_id = state["task_id"]
    retry_count = state.get("retry_count", 0) + 1
    logger.info(f"[{task_id}] Running Debugging Node (Starting attempt #{retry_count})")

    await global_event_bus.publish(
        task_id,
        TaskEvent(
            task_id=task_id,
            event_type="debugging",
            phase=WorkflowPhase.DEBUGGING,
            message=f"Diagnosing test failure (Attempt #{retry_count})...",
        ),
    )

    latest_test = state["test_results"][-1] if state.get("test_results") else {}
    test_output = latest_test.get("output", "No test output available.")

    prompt = (
        f"TEST FAILURE OUTPUT:\n{test_output}\n\n"
        f"RECENT MODIFICATIONS:\n{state.get('modified_files', [])}\n\n"
        f"USER GOAL:\n{state['user_instruction']}"
    )

    debug_output: DebugAnalysisOutput = await context.llm_client.generate_structured(
        prompt=prompt,
        response_schema=DebugAnalysisOutput,
        system_instruction=DEBUGGER_SYSTEM_PROMPT,
    )

    guidance = (
        f"ROOT CAUSE: {debug_output.root_cause}\n"
        f"PROPOSED FIX: {debug_output.proposed_fix}\n"
        f"TARGET FILES: {', '.join(debug_output.files_to_modify)}"
    )

    await global_event_bus.publish(
        task_id,
        TaskEvent(
            task_id=task_id,
            event_type="debugging_completed",
            phase=WorkflowPhase.DEBUGGING,
            message=f"Root cause diagnosed: {debug_output.root_cause}",
            data={
                "root_cause": debug_output.root_cause,
                "proposed_fix": debug_output.proposed_fix,
                "files_to_modify": debug_output.files_to_modify,
            },
        ),
    )

    return {
        **state,
        "current_phase": WorkflowPhase.DEBUGGING.value,
        "retry_count": retry_count,
        "debug_guidance": guidance,
    }


# --- Node 6: Review ---
async def review_node(state: GraphState, context: WorkflowContext) -> GraphState:
    """Audit diff, formulate summary, and craft commit message."""
    task_id = state["task_id"]
    logger.info(f"[{task_id}] Running Review Node")
    workspace_path = Path(state["workspace_path"])
    git_manager = GitWorkspaceManager(task_id=task_id, workspace_path=workspace_path)

    await global_event_bus.publish(
        task_id,
        TaskEvent(
            task_id=task_id,
            event_type="review",
            phase=WorkflowPhase.REVIEW,
            message="Reviewing code changes and formulating git commit...",
        ),
    )

    diff_text = git_manager.get_diff(against_branch=state.get("base_branch", "main"))

    prompt = (
        f"USER INSTRUCTION:\n{state['user_instruction']}\n\n"
        f"MODIFIED FILES:\n{state.get('modified_files', [])}\n\n"
        f"GIT DIFF:\n{diff_text or '(No diff)'}"
    )

    review_output: ReviewSummaryOutput = await context.llm_client.generate_structured(
        prompt=prompt,
        response_schema=ReviewSummaryOutput,
        system_instruction=REVIEWER_SYSTEM_PROMPT,
    )

    await global_event_bus.publish(
        task_id,
        TaskEvent(
            task_id=task_id,
            event_type="review_completed",
            phase=WorkflowPhase.REVIEW,
            message=f"Review completed: {review_output.commit_message}",
        ),
    )

    return {
        **state,
        "current_phase": WorkflowPhase.REVIEW.value,
        "review_summary": review_output.summary,
        "commit_message": review_output.commit_message,
    }


# --- Node 7: Commit ---
async def commit_node(state: GraphState, context: WorkflowContext) -> GraphState:
    """Create local git commit."""
    task_id = state["task_id"]
    logger.info(f"[{task_id}] Running Commit Node")
    workspace_path = Path(state["workspace_path"])
    git_manager = GitWorkspaceManager(task_id=task_id, workspace_path=workspace_path)

    await global_event_bus.publish(
        task_id,
        TaskEvent(
            task_id=task_id,
            event_type="commit",
            phase=WorkflowPhase.COMMIT,
            message="Committing verified changes...",
        ),
    )

    commit_msg = state.get("commit_message") or f"feat: {state['user_instruction']}"
    commit_sha = git_manager.commit(message=commit_msg)

    await global_event_bus.publish(
        task_id,
        TaskEvent(
            task_id=task_id,
            event_type="commit_completed",
            phase=WorkflowPhase.COMMIT,
            message=f"Committed changes with SHA: {commit_sha[:7] if commit_sha else 'N/A'}",
            data={"commit_sha": commit_sha},
        ),
    )

    return {
        **state,
        "current_phase": WorkflowPhase.COMMIT.value,
        "commit_sha": commit_sha,
    }


# --- Node 8: Pull Request ---
async def pull_request_node(state: GraphState, context: WorkflowContext) -> GraphState:
    """Optionally generate GitHub Pull Request for the committed changes."""
    task_id = state["task_id"]
    logger.info(f"[{task_id}] Running Pull Request Node")
    from app.github.client import GitHubManager

    gh = GitHubManager(token=context.settings.github_token)
    repo_url = state.get("repository_url", "")
    commit_sha = state.get("commit_sha", "")
    review_summary = state.get("review_summary", "")

    pr_title = state.get("commit_message") or f"feat: {state['user_instruction']}"
    pr_body = (
        f"## Autonomous Software Engineer Summary\n\n"
        f"**Task Description**: {state['user_instruction']}\n"
        f"**Commit SHA**: `{commit_sha[:7] if commit_sha else 'N/A'}`\n\n"
        f"### Changes\n{review_summary}\n\n"
        f"---\n*Generated autonomously by AI Software Engineer Agent.*"
    )

    pr_url = None
    try:
        pr_result = await gh.create_pull_request(
            repository_url=repo_url,
            title=pr_title,
            body=pr_body,
            head_branch=state.get("working_branch", "agent-fix"),
            base_branch=state.get("base_branch", "main"),
            dry_run=not bool(context.settings.github_token),
        )
        if not pr_result.get("is_dry_run"):
            pr_url = pr_result.get("html_url")
    except Exception as e:
        logger.warning(f"Pull Request creation failed or was skipped: {e}")
        pr_url = None

    if pr_url:
        await global_event_bus.publish(
            task_id,
            TaskEvent(
                task_id=task_id,
                event_type="pull_request_completed",
                phase=WorkflowPhase.PULL_REQUEST,
                message=f"Created Pull Request: {pr_url}",
                data={"pull_request_url": pr_url},
            ),
        )

    return {
        **state,
        "current_phase": WorkflowPhase.PULL_REQUEST.value,
        "pull_request_url": pr_url,
    }

