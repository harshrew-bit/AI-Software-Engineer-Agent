"""Tool Registry and Dispatcher with Safety Interception and Database Auditing."""

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from app.llm.base import ToolDefinition
from app.models.enums import ApprovalStatus
from app.tools.base import BaseTool, ToolExecutionContext, ToolResult
from app.tools.edit_tools import CreateFileTool, DeleteFileTool, ModifyFileTool
from app.tools.execution_tools import RunCommandTool, RunTestsTool
from app.tools.git_tools import GitCommitTool, GitDiffTool, GitStatusTool
from app.tools.repo_tools import (
    InspectDirectoryTool,
    ListFilesTool,
    ReadFileTool,
    SearchCodeTool,
)

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Central registry and execution dispatcher for agent tools."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool instance."""
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Retrieve tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        """List all registered tools."""
        return list(self._tools.values())

    def get_tool_definitions(self) -> List[ToolDefinition]:
        """Export all registered tools as provider-agnostic ToolDefinitions for LLM function calling."""
        return [tool.to_tool_definition() for tool in self._tools.values()]

    async def dispatch(
        self,
        tool_name: str,
        arguments: Dict[str, Any] | BaseModel,
        context: ToolExecutionContext,
    ) -> ToolResult:
        """Execute a tool with parameter validation, security checks, and database audit logging."""
        tool = self.get_tool(tool_name)
        if not tool:
            result = ToolResult(
                tool_name=tool_name,
                success=False,
                error=f"Tool '{tool_name}' is not registered in the tool registry.",
            )
            return result

        logger.info(f"Dispatching tool '{tool_name}' for task '{context.task_id}'")
        raw_args = arguments if isinstance(arguments, dict) else arguments.model_dump()

        # Check if the tool is dangerous and requires approval
        if tool.is_dangerous and context.settings.require_human_approval_for_destructive_actions:
            logger.warning(
                f"Action '{tool_name}' marked as dangerous. Creating approval request for task '{context.task_id}'."
            )
            if context.repository:
                await context.repository.create_approval_request(
                    approval_id=f"appr_{context.task_id}_{tool_name}",
                    task_id=context.task_id,
                    action_type="tool_execution",
                    tool_name=tool_name,
                    action_payload=raw_args,
                )
            return ToolResult(
                tool_name=tool_name,
                success=False,
                requires_approval=True,
                approval_status=ApprovalStatus.PENDING,
                error=f"Action '{tool_name}' requires human approval before execution.",
            )

        # Run tool
        result = await tool.execute(arguments, context)

        # Audit log in database
        if context.repository:
            try:
                await context.repository.record_tool_call(
                    task_id=context.task_id,
                    call_id=result.call_id,
                    tool_name=result.tool_name,
                    input_args=raw_args,
                    output=result.output,
                    error=result.error,
                    exit_code=result.exit_code,
                    execution_time_ms=result.execution_time_ms,
                    requires_approval=result.requires_approval,
                    approval_status=result.approval_status,
                )
            except Exception as audit_err:
                logger.error(f"Failed to record tool call audit log: {audit_err}")

        return result


from app.tools.github_tools import (
    AddPullRequestCommentTool,
    CreatePullRequestTool,
    GetPullRequestTool,
)


def create_default_tool_registry() -> ToolRegistry:
    """Factory helper creating the standard suite of software engineering tools."""
    registry = ToolRegistry()

    # Repository Tools
    registry.register(ListFilesTool())
    registry.register(ReadFileTool())
    registry.register(SearchCodeTool())
    registry.register(InspectDirectoryTool())

    # Editing Tools
    registry.register(CreateFileTool())
    registry.register(ModifyFileTool())
    registry.register(DeleteFileTool())

    # Execution Tools
    registry.register(RunCommandTool())
    registry.register(RunTestsTool())

    # Git Tools
    registry.register(GitStatusTool())
    registry.register(GitDiffTool())
    registry.register(GitCommitTool())

    # GitHub Tools
    registry.register(CreatePullRequestTool())
    registry.register(GetPullRequestTool())
    registry.register(AddPullRequestCommentTool())

    return registry
