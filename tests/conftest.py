"""Pytest configuration and shared fixtures."""

import os
import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import Settings
from app.models.db_models import Base
from app.llm.mock import MockLLMClient


@pytest.fixture
def test_settings(tmp_path) -> Settings:
    """Provide isolated test settings with temporary storage directories."""
    return Settings(
        app_name="Test AI SWE Agent",
        app_env="testing",
        debug=True,
        database_url=f"sqlite+aiosqlite:///{tmp_path}/test_agent.db",
        workspaces_root=tmp_path / "workspaces",
        default_llm_provider="mock",
        gemini_api_key="mock_key",
        github_token="",
    )


@pytest.fixture
async def async_db_session(tmp_path) -> AsyncGenerator[AsyncSession, None]:
    """Provide an in-memory or isolated SQLite async test database session."""
    db_path = tmp_path / "test_db.sqlite"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def mock_llm_client() -> MockLLMClient:
    """Provide a pre-configured Mock LLM client."""
    return MockLLMClient(default_response="Simulated AI Engineer analysis.")
