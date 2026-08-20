"""Application Settings using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for AI Software Engineer Agent."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # General App Settings
    app_name: str = "AI Software Engineer Agent"
    app_env: Literal["development", "testing", "production"] = "development"
    debug: bool = True
    port: int = 8000
    host: str = "0.0.0.0"
    reload_dirs: list[str] = ["app"]
    reload_excludes: list[str] = ["temp_workspaces*", "tests*", "data*", "*.db*"]

    # LLM Settings
    default_llm_provider: Literal["gemini", "mock", "openai", "anthropic"] = Field(
        default="gemini", alias="LLM_PROVIDER"
    )
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-pro", alias="GEMINI_MODEL")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    openai_max_retries: int = 3
    openai_retry_delay_seconds: float = 2.0
    llm_temperature: float = 0.2
    llm_max_tokens: int = 8192
    llm_timeout_seconds: int = 60
    # Gemini API Retry Settings
    gemini_max_retries: int = 2
    gemini_retry_delay_seconds: float = 5.0

    # Database Settings
    database_url: str = "sqlite+aiosqlite:///./data/agent_tasks.db"
    db_echo: bool = False

    # Workspace & File Management
    workspaces_root: Path = Field(default=Path("./temp_workspaces"))
    max_file_read_bytes: int = 100_000  # 100 KB max to avoid overloading context
    max_search_results: int = 50

    # Execution & Sandbox
    docker_sandbox_image: str = "python:3.12-slim"
    sandbox_execution_timeout_seconds: int = 120
    sandbox_memory_limit: str = "2g"
    sandbox_cpu_limit: float = 2.0
    require_human_approval_for_destructive_actions: bool = True

    # Workflow Constraints
    max_debug_retries: int = 5

    # GitHub Settings
    github_token: Optional[str] = Field(default=None, alias="GITHUB_TOKEN")

    def ensure_directories(self) -> None:
        """Ensure necessary local directories exist."""
        self.workspaces_root.mkdir(parents=True, exist_ok=True)
        if "sqlite" in self.database_url:
            # Parse directory path from sqlite URL
            clean_url = self.database_url.split("sqlite+aiosqlite:///")[-1].split("sqlite:///")[-1]
            if clean_url and clean_url != ":memory:":
                db_file = Path(clean_url)
                if db_file.parent and str(db_file.parent) != ".":
                    db_file.parent.mkdir(parents=True, exist_ok=True)
                else:
                    Path("./data").mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """Singleton getter for configuration settings."""
    settings = Settings()
    settings.ensure_directories()
    return settings
