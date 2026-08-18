"""Unit tests for configuration loading and validation."""

from pathlib import Path
from app.config.settings import Settings


def test_settings_default_values(tmp_path):
    """Test standard settings initialization."""
    settings = Settings(
        workspaces_root=tmp_path / "workspaces",
        database_url=f"sqlite+aiosqlite:///{tmp_path}/test.db",
    )
    assert settings.app_name == "AI Software Engineer Agent"
    assert settings.app_env in ["development", "testing", "production"]
    assert settings.sandbox_execution_timeout_seconds == 120
    assert settings.require_human_approval_for_destructive_actions is True


def test_settings_ensure_directories(tmp_path):
    """Test directory creation helper."""
    workspace_dir = tmp_path / "custom_workspaces"
    settings = Settings(
        workspaces_root=workspace_dir,
        database_url=f"sqlite+aiosqlite:///{tmp_path}/data/test.db",
    )
    settings.ensure_directories()
    assert workspace_dir.exists()
    assert (tmp_path / "data").exists()
