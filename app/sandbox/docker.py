"""Docker-based Sandbox for Isolated Execution."""

import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, Optional

from app.config import get_settings
from app.sandbox.base import BaseSandbox, ExecutionResult
from app.sandbox.policies import (
    DEFAULT_TIMEOUT_SECONDS,
    sanitize_environment,
    truncate_output,
    validate_command_safety,
)

logger = logging.getLogger(__name__)


class DockerSandbox(BaseSandbox):
    """Containerized sandbox executing commands inside an isolated Docker container."""

    def __init__(
        self,
        workspace_path: Path,
        image_name: Optional[str] = None,
        memory_limit: Optional[str] = None,
        cpu_limit: Optional[float] = None,
    ):
        self.workspace_path = workspace_path.resolve()
        settings = get_settings()
        self.image_name = image_name or settings.docker_sandbox_image
        self.memory_limit = memory_limit or settings.sandbox_memory_limit
        self.cpu_limit = cpu_limit or settings.sandbox_cpu_limit
        self.container_id: Optional[str] = None
        self._docker_client = None

    def _get_docker_client(self):
        """Retrieve Docker client."""
        if self._docker_client is None:
            import docker
            self._docker_client = docker.from_env()
        return self._docker_client

    def _ensure_container_running(self) -> str:
        """Create and start container if not already active."""
        client = self._get_docker_client()

        if self.container_id:
            try:
                container = client.containers.get(self.container_id)
                if container.status == "running":
                    return self.container_id
            except Exception:
                self.container_id = None

        # Create new ephemeral container with dropped capabilities and isolated volume
        nano_cpus = int(self.cpu_limit * 1e9)
        container = client.containers.run(
            image=self.image_name,
            command="tail -f /dev/null",  # Keep container alive
            detach=True,
            working_dir="/workspace",
            volumes={
                str(self.workspace_path): {
                    "bind": "/workspace",
                    "mode": "rw",
                }
            },
            mem_limit=self.memory_limit,
            nano_cpus=nano_cpus,
            cap_drop=["ALL"],
            security_opt=["no-new-privileges:true"],
            network_mode="bridge",
        )
        self.container_id = container.id
        logger.info(f"Spawned Docker sandbox container: {self.container_id[:12]}")
        return self.container_id

    async def run_command(
        self,
        command: str,
        working_dir: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> ExecutionResult:
        """Execute command inside the Docker container with timeout and policy checks."""
        timeout = timeout_seconds or DEFAULT_TIMEOUT_SECONDS

        # Validate command against dangerous host/kernel attacks
        try:
            validate_command_safety(command)
        except ValueError as err:
            return ExecutionResult(
                command=command,
                exit_code=126,
                stdout="",
                stderr=str(err),
                timed_out=False,
            )

        safe_env = sanitize_environment(env, allow_safe_system_paths=False)
        workdir = "/workspace" if not working_dir else f"/workspace/{working_dir.lstrip('/')}"

        start_time = time.perf_counter()
        try:
            # Run docker operations in a thread pool to avoid blocking the event loop
            container_id = await asyncio.to_thread(self._ensure_container_running)
            client = self._get_docker_client()
            container = client.containers.get(container_id)

            # Exec run
            def _exec():
                return container.exec_run(
                    cmd=["/bin/sh", "-c", command],
                    workdir=workdir,
                    environment=safe_env,
                    demux=True,
                )

            exec_task = asyncio.to_thread(_exec)
            exec_res = await asyncio.wait_for(exec_task, timeout=float(timeout))
            exit_code = exec_res.exit_code

            stdout_bytes, stderr_bytes = exec_res.output
            stdout = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
            stderr = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""
            timed_out = False

        except asyncio.TimeoutError:
            exit_code = 124
            stdout = ""
            stderr = f"Command timed out after {timeout} seconds inside Docker sandbox."
            timed_out = True
            # Recreate container to clean up any stuck processes
            await self.cleanup()

        except Exception as e:
            logger.error(f"Docker sandbox execution error: {e}")
            return ExecutionResult(
                command=command,
                exit_code=1,
                stdout="",
                stderr=f"Docker sandbox error: {str(e)}",
                timed_out=False,
            )

        execution_time_ms = (time.perf_counter() - start_time) * 1000.0

        return ExecutionResult(
            command=command,
            exit_code=exit_code,
            stdout=truncate_output(stdout),
            stderr=truncate_output(stderr),
            execution_time_ms=execution_time_ms,
            timed_out=timed_out,
        )

    async def cleanup(self) -> None:
        """Stop and remove the Docker sandbox container."""
        if self.container_id:
            try:
                client = self._get_docker_client()
                container = client.containers.get(self.container_id)
                await asyncio.to_thread(container.remove, force=True)
                logger.info(f"Removed Docker sandbox container: {self.container_id[:12]}")
            except Exception as e:
                logger.warning(f"Error removing container {self.container_id}: {e}")
            finally:
                self.container_id = None
