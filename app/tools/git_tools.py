"""Git inspection and management tools."""

from typing import Optional
from pydantic import BaseModel, Field

from app.models.enums import ToolCategory
from app.tools.base import BaseTool, ToolExecutionContext, ToolResult


# --- Git Status Tool ---
class GitStatusInput(BaseModel):
    pass


class GitStatusTool(BaseTool):
    name = "git_status"
    description = "Inspect modified, untracked, staged, and deleted files in the working branch."
    category = ToolCategory.GIT
    args_schema = GitStatusInput
    is_dangerous = False

    async def _run(self, args: GitStatusInput, context: ToolExecutionContext) -> ToolResult:
        try:
            status = context.git_manager.get_status()
            lines = [f"Branch: {context.git_manager.repo.active_branch.name}"]

            for cat, files in status.items():
                if files:
                    lines.append(f"{cat.upper()}:")
                    for f in files:
                        lines.append(f"  - {f}")

            output = "\n".join(lines) if len(lines) > 1 else "Working tree clean. No changes detected."
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=output,
                metadata=status,
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=str(e))


# --- Git Diff Tool ---
class GitDiffInput(BaseModel):
    against_branch: Optional[str] = Field(
        default=None,
        description="Optional base branch name to diff against (e.g. 'main'). If omitted, diffs working tree vs HEAD.",
    )


class GitDiffTool(BaseTool):
    name = "git_diff"
    description = "View the unified git diff of all modifications."
    category = ToolCategory.GIT
    args_schema = GitDiffInput
    is_dangerous = False

    async def _run(self, args: GitDiffInput, context: ToolExecutionContext) -> ToolResult:
        try:
            diff_text = context.git_manager.get_diff(against_branch=args.against_branch)
            output = diff_text if diff_text.strip() else "(No diff detected)"
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=output,
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=str(e))


# --- Git Commit Tool ---
class GitCommitInput(BaseModel):
    message: str = Field(..., description="Descriptive commit message detailing the changes")


class GitCommitTool(BaseTool):
    name = "git_commit"
    description = "Stage all changes and create a Git commit on the current working branch."
    category = ToolCategory.GIT
    args_schema = GitCommitInput
    is_dangerous = False

    async def _run(self, args: GitCommitInput, context: ToolExecutionContext) -> ToolResult:
        try:
            commit_sha = context.git_manager.commit(message=args.message)
            if not commit_sha:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    error="Nothing to commit; working directory is clean.",
                )

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=f"Committed changes with SHA: {commit_sha[:7]} ('{args.message.splitlines()[0]}')",
                metadata={"commit_sha": commit_sha},
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=str(e))
