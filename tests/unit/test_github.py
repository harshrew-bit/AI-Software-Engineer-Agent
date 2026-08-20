"""Unit tests for GitHub Client, Pull Request Tools, and HITL Checkpoints."""

import pytest
from app.config.settings import Settings
from app.database.repository import TaskRepository
from app.github.client import GitHubError, GitHubManager
from app.models.enums import ApprovalStatus
from app.repository.git_manager import GitWorkspaceManager
from app.sandbox.local import LocalSubprocessSandbox
from app.tools.base import ToolExecutionContext
from app.tools.github_tools import (
    AddPullRequestCommentTool,
    CreatePullRequestTool,
    GetPullRequestTool,
)
from app.tools.registry import create_default_tool_registry


def test_github_url_parsing():
    """Verify repo name parsing across multiple URL formats."""
    assert (
        GitHubManager.extract_repo_full_name("https://github.com/fastapi/fastapi.git")
        == "fastapi/fastapi"
    )
    assert (
        GitHubManager.extract_repo_full_name("https://github.com/torvalds/linux")
        == "torvalds/linux"
    )
    assert (
        GitHubManager.extract_repo_full_name("git@github.com:pydantic/pydantic.git")
        == "pydantic/pydantic"
    )
    assert (
        GitHubManager.extract_repo_full_name("psf/black")
        == "psf/black"
    )

    with pytest.raises(GitHubError, match="Could not parse"):
        GitHubManager.extract_repo_full_name("invalid_url_without_slashes")


@pytest.mark.asyncio
async def test_github_manager_dry_run():
    """Verify GitHubManager operations in dry-run mode without real tokens."""
    gh = GitHubManager(token="")

    # 1. Create PR
    pr_result = await gh.create_pull_request(
        repository_url="https://github.com/example/demo-app",
        title="feat: Add JWT auth",
        body="Added login endpoints",
        head_branch="agent-fix/task-1",
        base_branch="main",
        dry_run=True,
    )
    assert pr_result["is_dry_run"] is True
    assert pr_result["html_url"] is None
    assert pr_result["pr_number"] is None

    # 2. Get PR
    pr_info = await gh.get_pull_request("https://github.com/example/demo-app", 999)
    assert pr_info["pr_number"] == 999
    assert pr_info["is_dry_run"] is True

    # 3. Add Comment
    comment_info = await gh.add_pull_request_comment(
        "https://github.com/example/demo-app", 999, "Automated tests passed."
    )
    assert comment_info["is_dry_run"] is True
    assert comment_info["comment_id"] == 12345


@pytest.mark.asyncio
async def test_create_pull_request_tool_approval_gate(tmp_path, async_db_session):
    """Verify CreatePullRequestTool triggers dangerous action safety gate."""
    ws = tmp_path / "workspace"
    git_manager = GitWorkspaceManager(task_id="task-pr-gate", workspace_path=ws)
    git_manager.init_local_empty_repo()

    repo = TaskRepository(async_db_session)
    await repo.create_task(
        task_id="task-pr-gate",
        repository_url="https://github.com/example/demo",
        user_instruction="Create PR for new feature",
        workspace_path=str(ws),
    )

    context = ToolExecutionContext(
        task_id="task-pr-gate",
        workspace_path=ws,
        git_manager=git_manager,
        sandbox=LocalSubprocessSandbox(workspace_path=ws),
        settings=Settings(
            workspaces_root=tmp_path / "workspaces",
            require_human_approval_for_destructive_actions=True,
        ),
        repository=repo,
    )

    registry = create_default_tool_registry()

    # Dispatch create_pull_request tool -> should be paused for human approval!
    res = await registry.dispatch(
        "create_pull_request",
        {
            "title": "feat: new feature",
            "body": "PR description",
            "base_branch": "main",
        },
        context,
    )
    assert res.requires_approval is True
    assert res.approval_status == ApprovalStatus.PENDING
    assert "requires human approval" in res.error
