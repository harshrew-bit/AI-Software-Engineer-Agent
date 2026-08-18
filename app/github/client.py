"""GitHub API Client for Pull Request and Issue Management."""

import logging
import re
from typing import Any, Dict, Optional
from github import Github, GithubException

from app.config import get_settings

logger = logging.getLogger(__name__)


class GitHubError(Exception):
    """Exception raised for GitHub API errors."""
    pass


class GitHubManager:
    """Manages remote GitHub interactions like Pull Requests and comments."""

    def __init__(self, token: Optional[str] = None):
        settings = get_settings()
        self.token = token or settings.github_token
        self._gh: Optional[Github] = None

    @property
    def gh(self) -> Github:
        """Access PyGithub client instance."""
        if not self.token:
            raise GitHubError("GITHUB_TOKEN is not configured in settings or environment.")
        if self._gh is None:
            self._gh = Github(self.token)
        return self._gh

    @staticmethod
    def extract_repo_full_name(repo_url: str) -> str:
        """Parse 'owner/repo' from various Git and GitHub URL formats."""
        # Handles https://github.com/owner/repo.git or git@github.com:owner/repo.git
        clean_url = repo_url.rstrip("/")
        if clean_url.endswith(".git"):
            clean_url = clean_url[:-4]

        # Match github.com/owner/repo or github.com:owner/repo
        match = re.search(r"github\.com[/:]([\w\.-]+)/([\w\.-]+)", clean_url)
        if match:
            return f"{match.group(1)}/{match.group(2)}"

        # If already in 'owner/repo' format
        if "/" in clean_url and len(clean_url.split("/")) == 2:
            return clean_url

        raise GitHubError(f"Could not parse GitHub repository owner/name from URL: '{repo_url}'")

    async def create_pull_request(
        self,
        repository_url: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main",
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Create a Pull Request on GitHub."""
        repo_name = self.extract_repo_full_name(repository_url)

        if dry_run or not self.token:
            logger.info(
                f"[DRY-RUN] Creating PR for {repo_name}: {head_branch} -> {base_branch} ('{title}')"
            )
            return {
                "pr_number": None,
                "html_url": None,
                "title": title,
                "head": head_branch,
                "base": base_branch,
                "is_dry_run": True,
            }

        try:
            repo = self.gh.get_repo(repo_name)
            pr = repo.create_pull(
                title=title,
                body=body,
                head=head_branch,
                base=base_branch,
            )
            logger.info(f"Created GitHub PR #{pr.number}: {pr.html_url}")
            return {
                "pr_number": pr.number,
                "html_url": pr.html_url,
                "title": pr.title,
                "head": head_branch,
                "base": base_branch,
                "is_dry_run": False,
            }
        except GithubException as e:
            logger.error(f"Failed to create PR on {repo_name}: {e}")
            raise GitHubError(f"GitHub PR creation failed: {e.data.get('message', str(e))}") from e

    async def get_pull_request(self, repository_url: str, pr_number: int) -> Dict[str, Any]:
        """Fetch metadata for an existing PR."""
        repo_name = self.extract_repo_full_name(repository_url)

        if not self.token:
            return {
                "pr_number": pr_number,
                "html_url": f"https://github.com/{repo_name}/pull/{pr_number}",
                "state": "open",
                "is_dry_run": True,
            }

        try:
            repo = self.gh.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            return {
                "pr_number": pr.number,
                "html_url": pr.html_url,
                "title": pr.title,
                "state": pr.state,
                "body": pr.body,
                "user": pr.user.login if pr.user else None,
                "is_dry_run": False,
            }
        except GithubException as e:
            raise GitHubError(f"Failed to fetch PR #{pr_number}: {e}") from e

    async def add_pull_request_comment(
        self,
        repository_url: str,
        pr_number: int,
        comment_body: str,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Add an issue/PR comment."""
        repo_name = self.extract_repo_full_name(repository_url)

        if dry_run or not self.token:
            logger.info(f"[DRY-RUN] Adding comment to {repo_name} PR #{pr_number}")
            return {
                "comment_id": 12345,
                "pr_number": pr_number,
                "body": comment_body,
                "is_dry_run": True,
            }

        try:
            repo = self.gh.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            comment = pr.create_issue_comment(comment_body)
            return {
                "comment_id": comment.id,
                "pr_number": pr_number,
                "body": comment.body,
                "is_dry_run": False,
            }
        except GithubException as e:
            raise GitHubError(f"Failed to comment on PR #{pr_number}: {e}") from e
