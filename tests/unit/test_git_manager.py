"""Unit tests for Git Workspace Manager."""

from pathlib import Path
import pytest
from app.repository.git_manager import GitWorkspaceError, GitWorkspaceManager


def test_git_manager_init_and_commit(tmp_path):
    """Test local git repo initialization, branching, and committing."""
    manager = GitWorkspaceManager(task_id="task-git-1", workspace_path=tmp_path / "repo")
    repo = manager.init_local_empty_repo(default_branch="main")

    assert repo.active_branch.name == "main"

    # Create a test file
    test_file = manager.workspace_path / "app.py"
    test_file.write_text("print('Hello SWE Agent')")

    status = manager.get_status()
    assert "app.py" in status["untracked"]

    # Commit the change
    commit_sha = manager.commit(message="Initial commit")
    assert commit_sha != ""
    assert len(commit_sha) == 40

    log = manager.get_commit_log(max_count=5)
    assert len(log) == 1
    assert log[0]["message"] == "Initial commit"


def test_git_manager_branch_and_diff(tmp_path):
    """Test branch creation and diff computation."""
    manager = GitWorkspaceManager(task_id="task-git-2", workspace_path=tmp_path / "repo")
    manager.init_local_empty_repo(default_branch="main")

    # Initial commit on main
    (manager.workspace_path / "main.txt").write_text("v1")
    manager.commit("v1 commit")

    # Create feature branch
    new_branch = manager.repo.create_head("feature/jwt-auth")
    new_branch.checkout()
    assert manager.repo.active_branch.name == "feature/jwt-auth"

    # Modify file
    (manager.workspace_path / "main.txt").write_text("v2 with JWT")
    diff = manager.get_diff()
    assert "+v2 with JWT" in diff
    assert "-v1" in diff

    manager.commit("v2 commit with JWT")
    diff_against_main = manager.get_diff(against_branch="main")
    assert "+v2 with JWT" in diff_against_main


def test_git_manager_path_traversal_protection(tmp_path):
    """Verify that path traversal attempts outside workspace are strictly blocked."""
    manager = GitWorkspaceManager(task_id="task-git-3", workspace_path=tmp_path / "safe_zone")
    manager.workspace_path.mkdir(parents=True, exist_ok=True)

    # Valid paths
    safe_path = manager.validate_safe_path("src/core/app.py")
    assert safe_path == (manager.workspace_path / "src/core/app.py").resolve()

    # Path traversal attack attempts
    with pytest.raises(GitWorkspaceError, match="Path traversal detected"):
        manager.validate_safe_path("../../etc/passwd")

    with pytest.raises(GitWorkspaceError, match="Path traversal detected"):
        manager.validate_safe_path("/etc/shadow")


def test_git_manager_cleanup(tmp_path):
    """Test cleanup removes workspace directory."""
    manager = GitWorkspaceManager(task_id="task-git-4", workspace_path=tmp_path / "to_delete")
    manager.init_local_empty_repo()
    assert manager.workspace_path.exists()

    manager.cleanup()
    assert not manager.workspace_path.exists()


def test_git_manager_push_success(tmp_path):
    """Test A: Verify successful push of working branch to remote repository."""
    import git

    # 1. Setup a bare remote repository
    remote_dir = tmp_path / "remote.git"
    remote_repo = git.Repo.init(str(remote_dir), bare=True)

    # 2. Seed initial commit in the remote bare repo
    seed_dir = tmp_path / "seed"
    seed_repo = git.Repo.init(str(seed_dir))
    (seed_dir / "README.md").write_text("# Initial Repo")
    seed_repo.git.add(A=True)
    seed_repo.index.commit("Initial seed commit")
    seed_repo.create_head("main")
    seed_repo.create_remote("origin", str(remote_dir))
    seed_repo.git.push("origin", "main:main")

    # 3. Use GitWorkspaceManager to clone and push working branch
    manager = GitWorkspaceManager(task_id="task-push-1", workspace_path=tmp_path / "workspace")
    manager.initialize_workspace(
        repository_url=str(remote_dir),
        base_branch="main",
        working_branch="agent-fix/task-push-1",
    )

    (manager.workspace_path / "solution.py").write_text("def solve(): return True\n")
    manager.commit("feat: implement solution")

    pushed_branch = manager.push(branch_name="agent-fix/task-push-1")
    assert pushed_branch == "agent-fix/task-push-1"

    # 4. Verify branch exists in the remote repository
    remote_branches = [h.name for h in remote_repo.heads]
    assert "agent-fix/task-push-1" in remote_branches


def test_git_manager_push_failure_propagates(tmp_path):
    """Test B: Verify push failure propagates as GitWorkspaceError."""
    manager = GitWorkspaceManager(task_id="task-push-fail", workspace_path=tmp_path / "workspace")
    manager.init_local_empty_repo()
    (manager.workspace_path / "data.txt").write_text("data")
    manager.commit("initial commit")

    # 1. Remote origin does not exist
    with pytest.raises(GitWorkspaceError, match="Remote 'origin' does not exist"):
        manager.push("main")

    # 2. Inaccessible remote rejects push
    manager.repo.create_remote("origin", "https://github.com/nonexistent-org-12345/nonexistent-repo-99999.git")
    with pytest.raises(GitWorkspaceError, match="Failed to push branch"):
        manager.push("main")


def test_github_url_authentication_with_token():
    """Test C: Verify GitHub HTTPS URL authentication and credential sanitization."""
    # 1. HTTPS URL formatted with x-access-token
    auth_url = GitWorkspaceManager._get_authenticated_url(
        "https://github.com/org/private-repo.git",
        "ghp_testSecretToken12345",
    )
    assert auth_url == "https://x-access-token:ghp_testSecretToken12345@github.com/org/private-repo.git"

    # 2. Sanitized URL masks credentials
    sanitized = GitWorkspaceManager._sanitize_url(auth_url)
    assert "ghp_testSecretToken12345" not in sanitized
    assert sanitized == "https://x-access-token:***@github.com/org/private-repo.git"


def test_public_and_local_repo_authentication_unchanged():
    """Test D: Verify public and local repository URLs remain unchanged."""
    # 1. GitHub URL without token remains unmodified
    assert (
        GitWorkspaceManager._get_authenticated_url("https://github.com/org/public-repo.git", None)
        == "https://github.com/org/public-repo.git"
    )
    assert (
        GitWorkspaceManager._get_authenticated_url("https://github.com/org/public-repo.git", "")
        == "https://github.com/org/public-repo.git"
    )

    # 2. Local file path remains unmodified even if token is provided
    assert (
        GitWorkspaceManager._get_authenticated_url("/var/data/repos/local-repo", "token123")
        == "/var/data/repos/local-repo"
    )
    assert (
        GitWorkspaceManager._get_authenticated_url("file:///tmp/repo", "token123")
        == "file:///tmp/repo"
    )


@pytest.mark.asyncio
async def test_pull_request_node_aborts_on_push_failure(tmp_path, monkeypatch):
    """Test E: Verify PR creation is not attempted when push fails."""
    from unittest.mock import AsyncMock
    from app.config.settings import Settings
    from app.graph.nodes import WorkflowContext, pull_request_node
    from app.llm.mock import MockLLMClient

    ws = tmp_path / "workspace_pr_fail"
    manager = GitWorkspaceManager(task_id="task-pr-abort", workspace_path=ws)
    manager.init_local_empty_repo()

    mock_llm = MockLLMClient()
    context = WorkflowContext(llm_client=mock_llm)
    context.settings = Settings(github_token="ghp_mock_token_for_abort_test")

    # Mock git_manager.push to raise GitWorkspaceError
    def mock_push_fail(*args, **kwargs):
        raise GitWorkspaceError("Authentication failed during git push")

    monkeypatch.setattr(GitWorkspaceManager, "push", mock_push_fail)

    mock_create_pr = AsyncMock()
    monkeypatch.setattr("app.github.client.GitHubManager.create_pull_request", mock_create_pr)

    state = {
        "task_id": "task-pr-abort",
        "workspace_path": str(ws),
        "working_branch": "agent-fix/task-pr-abort",
        "base_branch": "main",
        "repository_url": "https://github.com/org/repo.git",
        "commit_sha": "sha123456",
        "user_instruction": "Fix critical bug",
    }

    # Verify push failure raises GitWorkspaceError and create_pull_request is NOT called
    with pytest.raises(GitWorkspaceError, match="Authentication failed during git push"):
        await pull_request_node(state, context)

    mock_create_pr.assert_not_called()
