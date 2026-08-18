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
