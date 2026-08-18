"""GitHub Pull Request and Comment tools."""

from typing import Optional
from pydantic import BaseModel, Field

from app.github.client import GitHubManager
from app.models.enums import ToolCategory
from app.tools.base import BaseTool, ToolExecutionContext, ToolResult


# --- Create Pull Request Tool ---
class CreatePullRequestInput(BaseModel):
    title: str = Field(..., description="Pull Request title")
    body: str = Field(..., description="Detailed description of changes, motivation, and tests")
    base_branch: Optional[str] = Field(default="main", description="Target base branch")


class CreatePullRequestTool(BaseTool):
    name = "create_pull_request"
    description = "Create a remote GitHub Pull Request for the completed changes. This is a protected action."
    category = ToolCategory.GITHUB
    args_schema = CreatePullRequestInput
    is_dangerous = True  # Triggers HITL approval checkpoint

    async def _run(self, args: CreatePullRequestInput, context: ToolExecutionContext) -> ToolResult:
        try:
            gh = GitHubManager(token=context.settings.github_token)
            working_branch = context.git_manager.repo.active_branch.name

            pr_info = await gh.create_pull_request(
                repository_url=context.git_manager.repo.remotes.origin.url
                if hasattr(context.git_manager.repo.remotes, "origin")
                else "https://github.com/example/repo",
                title=args.title,
                body=args.body,
                head_branch=working_branch,
                base_branch=args.base_branch or "main",
                dry_run=not bool(context.settings.github_token),
            )

            output = (
                f"Successfully created Pull Request #{pr_info['pr_number']}\n"
                f"URL: {pr_info['html_url']}\n"
                f"Branches: {working_branch} -> {args.base_branch or 'main'}"
            )

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=output,
                metadata=pr_info,
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=str(e))


# --- Get Pull Request Tool ---
class GetPullRequestInput(BaseModel):
    pr_number: int = Field(..., description="The GitHub Pull Request number")
    repository_url: Optional[str] = Field(default=None, description="Optional GitHub repo URL")


class GetPullRequestTool(BaseTool):
    name = "get_pull_request"
    description = "Fetch details and status of an existing GitHub Pull Request."
    category = ToolCategory.GITHUB
    args_schema = GetPullRequestInput
    is_dangerous = False

    async def _run(self, args: GetPullRequestInput, context: ToolExecutionContext) -> ToolResult:
        try:
            gh = GitHubManager(token=context.settings.github_token)
            repo_url = args.repository_url or (
                context.git_manager.repo.remotes.origin.url
                if hasattr(context.git_manager.repo.remotes, "origin")
                else "https://github.com/example/repo"
            )

            pr_info = await gh.get_pull_request(
                repository_url=repo_url,
                pr_number=args.pr_number,
            )

            output = (
                f"Pull Request #{pr_info['pr_number']}: {pr_info.get('title', 'N/A')}\n"
                f"State: {pr_info.get('state', 'N/A')}\n"
                f"URL: {pr_info.get('html_url', 'N/A')}\n"
                f"Description:\n{pr_info.get('body', '')}"
            )

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=output,
                metadata=pr_info,
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=str(e))


# --- Add Pull Request Comment Tool ---
class AddPullRequestCommentInput(BaseModel):
    pr_number: int = Field(..., description="The GitHub Pull Request number")
    comment_body: str = Field(..., description="Comment text to post")
    repository_url: Optional[str] = Field(default=None, description="Optional GitHub repo URL")


class AddPullRequestCommentTool(BaseTool):
    name = "add_pull_request_comment"
    description = "Add a comment to a GitHub Pull Request or Issue."
    category = ToolCategory.GITHUB
    args_schema = AddPullRequestCommentInput
    is_dangerous = False

    async def _run(self, args: AddPullRequestCommentInput, context: ToolExecutionContext) -> ToolResult:
        try:
            gh = GitHubManager(token=context.settings.github_token)
            repo_url = args.repository_url or (
                context.git_manager.repo.remotes.origin.url
                if hasattr(context.git_manager.repo.remotes, "origin")
                else "https://github.com/example/repo"
            )

            comment_info = await gh.add_pull_request_comment(
                repository_url=repo_url,
                pr_number=args.pr_number,
                comment_body=args.comment_body,
                dry_run=not bool(context.settings.github_token),
            )

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=f"Added comment to PR #{args.pr_number}.",
                metadata=comment_info,
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=str(e))
