"""Git Workspace Manager for isolated repository operations."""

import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
import git
from git import Repo

from app.config import get_settings

logger = logging.getLogger(__name__)


class GitWorkspaceError(Exception):
    """Exception raised for errors during Git workspace management."""
    pass


class GitWorkspaceManager:
    """Manages cloning, branch isolation, diffing, and committing for an engineering task."""

    def __init__(self, task_id: str, workspace_path: Optional[Path] = None):
        self.task_id = task_id
        settings = get_settings()
        self.workspace_path = workspace_path or (settings.workspaces_root / task_id).resolve()
        self._repo: Optional[Repo] = None

    @property
    def repo(self) -> Repo:
        """Access the underlying GitPython Repo instance."""
        if self._repo is None:
            if not (self.workspace_path / ".git").exists():
                raise GitWorkspaceError(
                    f"No git repository initialized at {self.workspace_path}"
                )
            self._repo = Repo(str(self.workspace_path))
        return self._repo

    def validate_safe_path(self, relative_or_abs_path: str | Path) -> Path:
        """Validate and normalize a file path, ensuring it stays strictly inside the workspace."""
        path = Path(relative_or_abs_path)
        if not path.is_absolute():
            resolved = (self.workspace_path / path).resolve()
        else:
            resolved = path.resolve()

        # Guard against directory traversal attacks (e.g. ../../etc/passwd)
        try:
            resolved.relative_to(self.workspace_path.resolve())
        except ValueError:
            raise GitWorkspaceError(
                f"Path traversal detected: '{relative_or_abs_path}' escapes workspace '{self.workspace_path}'"
            )
        return resolved

    def initialize_workspace(
        self,
        repository_url: str,
        base_branch: str = "main",
        working_branch: Optional[str] = None,
        shallow_clone: bool = True,
    ) -> str:
        """Clone remote repository or initialize local repo and create working branch."""
        # Ensure fresh directory
        if self.workspace_path.exists():
            shutil.rmtree(self.workspace_path, ignore_errors=True)
        self.workspace_path.mkdir(parents=True, exist_ok=True)

        branch_name = working_branch or f"agent-fix/{self.task_id}"

        try:
            logger.info(f"Cloning {repository_url} into {self.workspace_path}")
            clone_kwargs: Dict[str, Any] = {"no_single_branch": False}
            if shallow_clone:
                clone_kwargs["depth"] = 1

            # Support local file path or remote Git URL
            if os.path.exists(repository_url):
                self._repo = Repo.clone_from(repository_url, str(self.workspace_path))
            else:
                self._repo = Repo.clone_from(repository_url, str(self.workspace_path), **clone_kwargs)

            # Ensure we are on the base branch or checkout base
            try:
                self._repo.git.checkout(base_branch)
            except git.GitCommandError:
                # If remote default branch is master/other, stay on current head
                base_branch = self._repo.active_branch.name

            # Create and switch to working branch
            new_branch = self._repo.create_head(branch_name)
            new_branch.checkout()

            logger.info(f"Created and checked out working branch '{branch_name}' from '{base_branch}'")
            return branch_name

        except Exception as e:
            logger.error(f"Failed to initialize workspace for {repository_url}: {e}")
            raise GitWorkspaceError(f"Failed to clone/initialize repository: {e}") from e

    def init_local_empty_repo(self, default_branch: str = "main") -> Repo:
        """Initialize a fresh Git repo locally for testing or new project bootstrapping."""
        if self.workspace_path.exists():
            shutil.rmtree(self.workspace_path, ignore_errors=True)
        self.workspace_path.mkdir(parents=True, exist_ok=True)

        self._repo = Repo.init(str(self.workspace_path), initial_branch=default_branch)
        return self._repo

    def get_status(self) -> Dict[str, List[str]]:
        """Return categorized git status (untracked, modified, staged, deleted)."""
        repo = self.repo
        staged_files: List[str] = []
        modified_files: List[str] = []
        deleted_files: List[str] = []

        try:
            diff_unstaged = repo.index.diff(None)
            modified_files = [item.a_path for item in diff_unstaged if item.change_type == "M"]
            deleted_files = [item.a_path for item in diff_unstaged if item.change_type == "D"]
        except Exception:
            pass

        if repo.head.is_valid():
            try:
                staged_files = [item.a_path for item in repo.index.diff("HEAD") if item.a_path]
            except Exception:
                pass

        status_info: Dict[str, List[str]] = {
            "untracked": repo.untracked_files,
            "modified": modified_files,
            "deleted": deleted_files,
            "staged": staged_files,
        }
        return status_info

    def get_diff(self, against_branch: Optional[str] = None) -> str:
        """Get git diff output either working-tree vs HEAD or against a base branch."""
        repo = self.repo
        try:
            if against_branch:
                return repo.git.diff(against_branch)
            return repo.git.diff("HEAD") if repo.head.is_valid() else repo.git.diff()
        except git.GitCommandError as e:
            logger.warning(f"Error fetching git diff: {e}")
            return ""

    def stage_all(self) -> None:
        """Stage all tracked and untracked changes."""
        self.repo.git.add(A=True)

    def commit(
        self,
        message: str,
        author_name: str = "AI Software Engineer Agent",
        author_email: str = "agent@autonomous-swe.local",
    ) -> str:
        """Stage all modifications and create a commit, returning the commit SHA."""
        repo = self.repo
        self.stage_all()

        if not repo.is_dirty() and not repo.untracked_files:
            logger.warning("No changes to commit.")
            if repo.head.is_valid():
                return repo.head.commit.hexsha
            return ""

        author = git.Actor(author_name, author_email)
        commit = repo.index.commit(message, author=author, committer=author)
        logger.info(f"Created commit {commit.hexsha[:7]}: {message.splitlines()[0]}")
        return commit.hexsha

    def get_commit_log(self, max_count: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent commit history."""
        repo = self.repo
        commits = []
        try:
            for commit in repo.iter_commits(max_count=max_count):
                commits.append({
                    "sha": commit.hexsha,
                    "short_sha": commit.hexsha[:7],
                    "message": commit.message.strip(),
                    "author": commit.author.name,
                    "authored_datetime": commit.authored_datetime.isoformat(),
                })
        except ValueError:
            # Empty repository without commits
            pass
        return commits

    def cleanup(self) -> None:
        """Remove the workspace directory from disk."""
        if self._repo:
            self._repo.close()
            self._repo = None
        if self.workspace_path.exists():
            shutil.rmtree(self.workspace_path, ignore_errors=True)
            logger.info(f"Cleaned up workspace at {self.workspace_path}")
