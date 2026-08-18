"""Local Subprocess Sandbox with strict boundary and policy enforcement."""

import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, Optional

from app.sandbox.base import BaseSandbox, ExecutionResult
from app.sandbox.policies import (
    DEFAULT_TIMEOUT_SECONDS,
    sanitize_environment,
    truncate_output,
    validate_command_safety,
)

logger = logging.getLogger(__name__)


class LocalSubprocessSandbox(BaseSandbox):
    """Secure local execution fallback strictly bounded to the workspace directory."""

    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path.resolve()
        if not self.workspace_path.exists():
            self.workspace_path.mkdir(parents=True, exist_ok=True)

    async def run_command(
        self,
        command: str,
        working_dir: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> ExecutionResult:
        """Run command in local subprocess with security policies."""
        timeout = timeout_seconds or DEFAULT_TIMEOUT_SECONDS

        # 1. Validate against forbidden malicious patterns
        try:
            validate_command_safety(command)
        except ValueError as err:
            return ExecutionResult(
                command=command,
                exit_code=126,  # Command cannot execute
                stdout="",
                stderr=str(err),
                timed_out=False,
            )

        # 2. Determine and validate working directory
        cwd = self.workspace_path
        if working_dir:
            target_cwd = (self.workspace_path / working_dir).resolve()
            try:
                target_cwd.relative_to(self.workspace_path)
                cwd = target_cwd
            except ValueError:
                return ExecutionResult(
                    command=command,
                    exit_code=1,
                    stdout="",
                    stderr=f"Security Error: working_dir '{working_dir}' escapes workspace boundary.",
                    timed_out=False,
                )

        # 3. Sanitize environment variables
        safe_env = sanitize_environment(env)

        # 4. Execute asynchronously with strict timeout
        start_time = time.perf_counter()
        timed_out = False
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=str(cwd),
                env=safe_env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), timeout=float(timeout)
                )
                exit_code = process.returncode or 0
                stdout = stdout_bytes.decode("utf-8", errors="replace")
                stderr = stderr_bytes.decode("utf-8", errors="replace")
            except asyncio.TimeoutError:
                timed_out = True
                try:
                    process.kill()
                    await process.wait()
                except Exception as kill_err:
                    logger.warning(f"Error killing timed out process: {kill_err}")
                exit_code = 124  # Standard timeout exit code
                stdout = ""
                stderr = f"Command timed out after {timeout} seconds."

        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return ExecutionResult(
                command=command,
                exit_code=1,
                stdout="",
                stderr=f"Subprocess invocation error: {str(e)}",
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
        """Local sandbox cleanup (no container to destroy)."""
        pass
