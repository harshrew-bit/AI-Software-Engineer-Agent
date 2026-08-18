"""SQLAlchemy database models for persistence."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import json

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""
    pass


class TaskModel(Base):
    """Database representation of an agent engineering task."""
    __tablename__ = "tasks"

    id = Column(String(64), primary_key=True, index=True)
    repository_url = Column(String(512), nullable=False)
    user_instruction = Column(Text, nullable=False)
    status = Column(String(32), default="pending", index=True, nullable=False)
    current_phase = Column(String(32), default="initialized", nullable=False)
    base_branch = Column(String(128), default="main", nullable=False)
    working_branch = Column(String(128), nullable=False)
    workspace_path = Column(String(512), nullable=False)

    commit_sha = Column(String(64), nullable=True)
    pull_request_url = Column(String(512), nullable=True)
    review_summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    plan_json = Column(Text, nullable=True)
    modified_files_json = Column(Text, nullable=True)
    test_results_json = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=5, nullable=False)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )

    # Relationships
    steps = relationship("StepModel", back_populates="task", cascade="all, delete-orphan")
    tool_calls = relationship("ToolCallModel", back_populates="task", cascade="all, delete-orphan")
    approval_requests = relationship(
        "ApprovalRequestModel", back_populates="task", cascade="all, delete-orphan"
    )


class StepModel(Base):
    """Step/Node execution record in the workflow."""
    __tablename__ = "task_steps"

    id = Column(String(64), primary_key=True, index=True)
    task_id = Column(String(64), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    node_name = Column(String(64), nullable=False)
    phase = Column(String(32), nullable=False)
    step_index = Column(Integer, nullable=False)
    state_snapshot = Column(Text, nullable=True)
    started_at = Column(DateTime, default=utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    task = relationship("TaskModel", back_populates="steps")


class ToolCallModel(Base):
    """Audit log of individual tool executions."""
    __tablename__ = "tool_calls"

    id = Column(String(64), primary_key=True, index=True)
    task_id = Column(String(64), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_name = Column(String(64), nullable=False, index=True)
    input_parameters = Column(Text, nullable=False)  # JSON serialized
    output_result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    exit_code = Column(Integer, nullable=True)
    execution_time_ms = Column(Float, default=0.0, nullable=False)
    requires_approval = Column(Boolean, default=False, nullable=False)
    approval_status = Column(String(32), default="not_required", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    task = relationship("TaskModel", back_populates="tool_calls")


class ApprovalRequestModel(Base):
    """Human-in-the-loop approval record."""
    __tablename__ = "approval_requests"

    id = Column(String(64), primary_key=True, index=True)
    task_id = Column(String(64), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type = Column(String(64), nullable=False)
    tool_name = Column(String(64), nullable=False)
    action_payload = Column(Text, nullable=False)  # JSON serialized
    status = Column(String(32), default="pending", index=True, nullable=False)
    reviewer_feedback = Column(Text, nullable=True)
    requested_at = Column(DateTime, default=utc_now, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    task = relationship("TaskModel", back_populates="approval_requests")
