"""Workspace Service for isolated directory allocations and lifecycle."""

import logging
import shutil
from pathlib import Path
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)


class WorkspaceService:
    """Allocates, resolves, and purges local disk workspace directories."""

    def __init__(self, root_dir: Optional[Path] = None):
        settings = get_settings()
        self.root_dir = root_dir or settings.workspaces_root

    def get_task_workspace_path(self, task_id: str) -> Path:
        """Derive absolute workspace directory path for a task."""
        return (self.root_dir / task_id).resolve()

    def allocate_workspace(self, task_id: str) -> Path:
        """Create a fresh workspace directory for a task."""
        path = self.get_task_workspace_path(task_id)
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Allocated workspace at {path}")
        return path

    def purge_workspace(self, task_id: str) -> None:
        """Delete task workspace from disk."""
        path = self.get_task_workspace_path(task_id)
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
            logger.info(f"Purged workspace at {path}")
