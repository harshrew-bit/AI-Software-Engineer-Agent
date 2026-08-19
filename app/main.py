"""Main FastAPI Application Entrypoint."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.api.sse import sse_router
from app.config import get_settings
from app.database.repository import TaskRepository
from app.database.session import get_session_factory, init_db
from app.models.enums import TaskStatus, WorkflowPhase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("Initializing database schema...")
    await init_db()
    logger.info("Database initialized successfully.")

    # Recover any orphaned tasks left in RUNNING or PENDING status across server restarts
    try:
        session_factory = get_session_factory()
        async with session_factory() as session:
            repo = TaskRepository(session)
            active_tasks = await repo.list_active_tasks()
            for t in active_tasks:
                logger.warning(
                    f"Recovering orphaned task '{t.id}' left in status '{t.status}'; marking as FAILED."
                )
                await repo.update_task_phase(
                    task_id=t.id,
                    phase=WorkflowPhase.FINISHED,
                    status=TaskStatus.FAILED,
                    error_message="Task interrupted due to server process shutdown or reload.",
                )
    except Exception as recover_err:
        logger.warning(f"Error during orphaned task recovery: {recover_err}")

    yield
    logger.info("Shutting down AI Software Engineer Agent application.")


def create_app() -> FastAPI:
    """Application factory for FastAPI server."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Autonomous AI Software Engineer Agent with Docker Sandbox, LangGraph, and Human-in-the-Loop Controls.",
        lifespan=lifespan,
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount Routes
    app.include_router(api_router)
    app.include_router(sse_router, prefix="/api/v1")

    @app.get("/health", summary="Health check")
    async def health_check():
        return {
            "status": "healthy",
            "app_name": settings.app_name,
            "env": settings.app_env,
            "version": "0.1.0",
        }

    @app.get("/", summary="Root index")
    async def root():
        return {
            "message": f"Welcome to {settings.app_name}",
            "docs_url": "/docs",
            "health_url": "/health",
        }

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        reload_dirs=settings.reload_dirs,
        reload_excludes=settings.reload_excludes,
    )
