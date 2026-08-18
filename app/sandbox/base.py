"""Base Sandbox Abstract Interface and Execution Results."""

from abc import ABC, abstractmethod
from typing import Dict, Optional
from pydantic import BaseModel, Field


class ExecutionResult(BaseModel):
    """Normalized output from sandboxed command execution."""
    command: str
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    execution_time_ms: float = 0.0
    timed_out: bool = False

    @property
    def is_success(self) -> bool:
        """True if the command finished with exit code 0 and did not time out."""
        return self.exit_code == 0 and not self.timed_out


class BaseSandbox(ABC):
    """Abstract interface defining the execution sandbox contract."""

    @abstractmethod
    async def run_command(
        self,
        command: str,
        working_dir: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> ExecutionResult:
        """Execute a shell command inside the sandbox."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Tear down and clean up any resources (containers, tmp files)."""
        pass
