"""Sandboxed execution tools for running commands and tests."""

import re
from typing import Optional
from pydantic import BaseModel, Field

from app.models.enums import ToolCategory
from app.tools.base import BaseTool, ToolExecutionContext, ToolResult


# --- Run Command Tool ---
class RunCommandInput(BaseModel):
    command: str = Field(..., description="Shell command to execute inside the sandbox")
    working_dir: Optional[str] = Field(default=None, description="Optional relative directory")
    timeout_seconds: Optional[int] = Field(default=None, description="Optional custom timeout in seconds")


class RunCommandTool(BaseTool):
    name = "run_command"
    description = "Execute a shell command inside the secure sandbox environment."
    category = ToolCategory.EXECUTION
    args_schema = RunCommandInput
    is_dangerous = False

    async def _run(self, args: RunCommandInput, context: ToolExecutionContext) -> ToolResult:
        try:
            res = await context.sandbox.run_command(
                command=args.command,
                working_dir=args.working_dir,
                timeout_seconds=args.timeout_seconds,
            )

            output_combined = ""
            if res.stdout:
                output_combined += f"--- STDOUT ---\n{res.stdout}\n"
            if res.stderr:
                output_combined += f"--- STDERR ---\n{res.stderr}\n"

            status_str = "SUCCESS" if res.is_success else "FAILED"
            summary = (
                f"Command: `{args.command}`\n"
                f"Exit Code: {res.exit_code} ({status_str})\n"
                f"Execution Time: {res.execution_time_ms:.1f} ms\n\n"
                f"{output_combined.strip() or '(No output)'}"
            )

            return ToolResult(
                tool_name=self.name,
                success=res.is_success,
                output=summary if res.is_success else None,
                error=summary if not res.is_success else None,
                exit_code=res.exit_code,
                execution_time_ms=res.execution_time_ms,
                metadata={"timed_out": res.timed_out},
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=str(e))


# --- Run Tests Tool ---
class RunTestsInput(BaseModel):
    test_command: Optional[str] = Field(
        default=None,
        description="Explicit test command (e.g. 'pytest', 'python -m unittest', 'npm test'). If omitted, auto-detects.",
    )
    test_path: Optional[str] = Field(default=None, description="Optional specific test file or directory path")


class RunTestsTool(BaseTool):
    name = "run_tests"
    description = "Execute test suites inside the sandbox and parse test pass/fail metrics."
    category = ToolCategory.EXECUTION
    args_schema = RunTestsInput
    is_dangerous = False

    def _detect_test_command(self, context: ToolExecutionContext) -> str:
        """Inspect repository files to auto-detect test framework."""
        ws = context.workspace_path
        if (ws / "pytest.ini").exists() or (ws / "pyproject.toml").exists() or (ws / "tests").exists():
            return "pytest -v"
        if any(ws.glob("test_*.py")) or any(ws.glob("*_test.py")):
            return "pytest -v"
        req_file = ws / "requirements.txt"
        if req_file.exists():
            try:
                if "pytest" in req_file.read_text(encoding="utf-8", errors="ignore"):
                    return "pytest -v"
            except Exception:
                pass
        if (ws / "package.json").exists():
            return "npm test"
        if (ws / "Cargo.toml").exists():
            return "cargo test"
        if (ws / "go.mod").exists():
            return "go test ./..."
        return "python -m unittest discover"

    def _parse_pytest_output(self, stdout: str):
        """Extract test summary metrics from pytest output."""
        passed = 0
        failed = 0
        errors = 0

        # Regex for '5 passed, 2 failed, 1 error in 1.23s'
        match = re.search(r"=+\s*(.*?)\s+in\s+[\d\.]+s\s*=+", stdout)
        if match:
            summary_str = match.group(1)
            p_match = re.search(r"(\d+)\s+passed", summary_str)
            f_match = re.search(r"(\d+)\s+failed", summary_str)
            e_match = re.search(r"(\d+)\s+error", summary_str)

            if p_match:
                passed = int(p_match.group(1))
            if f_match:
                failed = int(f_match.group(1))
            if e_match:
                errors = int(e_match.group(1))

        return passed, failed, errors

    async def _run(self, args: RunTestsInput, context: ToolExecutionContext) -> ToolResult:
        try:
            cmd = args.test_command or self._detect_test_command(context)
            if args.test_path:
                cmd = f"{cmd} {args.test_path}"

            res = await context.sandbox.run_command(command=cmd)

            passed, failed, errors = self._parse_pytest_output(res.stdout)
            total = passed + failed + errors

            output_summary = (
                f"Test Command: `{cmd}`\n"
                f"Status: {'PASSED' if res.is_success else 'FAILED'}\n"
                f"Exit Code: {res.exit_code}\n"
                f"Metrics: {passed} passed, {failed} failed, {errors} errors (Total: {total})\n\n"
                f"--- STDOUT ---\n{res.stdout}\n"
            )
            if res.stderr:
                output_summary += f"\n--- STDERR ---\n{res.stderr}\n"

            return ToolResult(
                tool_name=self.name,
                success=res.is_success,
                output=output_summary if res.is_success else None,
                error=output_summary if not res.is_success else None,
                exit_code=res.exit_code,
                execution_time_ms=res.execution_time_ms,
                metadata={
                    "command": cmd,
                    "passed": passed,
                    "failed": failed,
                    "errors": errors,
                    "total": total,
                    "is_success": res.is_success,
                },
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=str(e))
