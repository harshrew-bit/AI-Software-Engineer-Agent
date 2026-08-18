"""Sandbox Factory with Docker availability check and fallback."""

import logging
from pathlib import Path
from typing import Optional

from app.sandbox.base import BaseSandbox
from app.sandbox.docker import DockerSandbox
from app.sandbox.local import LocalSubprocessSandbox

logger = logging.getLogger(__name__)


def is_docker_available() -> bool:
    """Check if Docker daemon is reachable and responding."""
    try:
        import docker
        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False


def get_sandbox(
    workspace_path: Path,
    prefer_docker: bool = True,
    image_name: Optional[str] = None,
) -> BaseSandbox:
    """Factory returning DockerSandbox if available and preferred, else LocalSubprocessSandbox."""
    if prefer_docker and is_docker_available():
        logger.info("Instantiating DockerSandbox.")
        return DockerSandbox(workspace_path=workspace_path, image_name=image_name)
    
    logger.info("Docker unavailable or disabled; falling back to LocalSubprocessSandbox.")
    return LocalSubprocessSandbox(workspace_path=workspace_path)
