"""Unit tests for Sandbox execution, policies, and isolation."""

import pytest
from app.sandbox.factory import get_sandbox, is_docker_available
from app.sandbox.local import LocalSubprocessSandbox
from app.sandbox.policies import (
    sanitize_environment,
    truncate_output,
    validate_command_safety,
)


def test_sanitize_environment():
    """Verify that sensitive host API keys and database credentials are excluded."""
    dirty_env = {
        "GEMINI_API_KEY": "test-gemini-api-key",
        "GITHUB_TOKEN": "ghp_super_secret_token",
        "DATABASE_URL": "postgresql://user:pass@host/db",
        "AWS_SECRET_ACCESS_KEY": "secret_aws",
        "CUSTOM_VAR": "safe_value",
    }
    cleaned = sanitize_environment(dirty_env)

    assert "GEMINI_API_KEY" not in cleaned
    assert "GITHUB_TOKEN" not in cleaned
    assert "DATABASE_URL" not in cleaned
    assert "AWS_SECRET_ACCESS_KEY" not in cleaned
    assert cleaned.get("CUSTOM_VAR") == "safe_value"
    assert cleaned.get("PYTHONUNBUFFERED") == "1"


def test_validate_command_safety():
    """Verify that dangerous patterns raise ValueError."""
    with pytest.raises(ValueError, match="forbidden pattern"):
        validate_command_safety("shutdown -h now")

    with pytest.raises(ValueError, match="forbidden pattern"):
        validate_command_safety("rm -rf /")

    with pytest.raises(ValueError, match="forbidden pattern"):
        validate_command_safety(":(){ :|:& };:")

    # Safe commands should not raise
    validate_command_safety("pytest tests/ -v")
    validate_command_safety("python -m unittest")


def test_truncate_output():
    """Test output length truncation."""
    short_text = "Standard output line"
    assert truncate_output(short_text, max_bytes=100) == short_text

    long_text = "A" * 500
    truncated = truncate_output(long_text, max_bytes=100)
    assert len(truncated) < 500
    assert "Output truncated by Sandbox Guard" in truncated


@pytest.mark.asyncio
async def test_local_subprocess_sandbox_success(tmp_path):
    """Test standard successful command execution."""
    sandbox = LocalSubprocessSandbox(workspace_path=tmp_path)
    result = await sandbox.run_command("python3 -c \"print('Hello from Sandbox')\"")

    assert result.is_success is True
    assert result.exit_code == 0
    assert "Hello from Sandbox" in result.stdout
    assert result.timed_out is False
    assert result.execution_time_ms > 0


@pytest.mark.asyncio
async def test_local_subprocess_sandbox_failure(tmp_path):
    """Test non-zero exit code capture."""
    sandbox = LocalSubprocessSandbox(workspace_path=tmp_path)
    result = await sandbox.run_command("python3 -c \"import sys; sys.exit(42)\"")

    assert result.is_success is False
    assert result.exit_code == 42


@pytest.mark.asyncio
async def test_local_subprocess_sandbox_timeout(tmp_path):
    """Test hard timeout enforcement."""
    sandbox = LocalSubprocessSandbox(workspace_path=tmp_path)
    result = await sandbox.run_command(
        "python3 -c \"import time; time.sleep(5)\"",
        timeout_seconds=1,
    )

    assert result.is_success is False
    assert result.timed_out is True
    assert result.exit_code == 124
    assert "timed out after 1 seconds" in result.stderr


@pytest.mark.asyncio
async def test_local_subprocess_sandbox_working_dir_escape(tmp_path):
    """Test rejection of working_dir outside workspace."""
    sandbox = LocalSubprocessSandbox(workspace_path=tmp_path)
    result = await sandbox.run_command("ls", working_dir="../../")

    assert result.is_success is False
    assert "escapes workspace boundary" in result.stderr


def test_sandbox_factory_fallback(tmp_path):
    """Test factory fallback behavior."""
    sandbox = get_sandbox(workspace_path=tmp_path, prefer_docker=False)
    assert isinstance(sandbox, LocalSubprocessSandbox)
