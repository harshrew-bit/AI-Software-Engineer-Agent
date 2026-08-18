"""Enumeration definitions for tasks, statuses, and workflow phases."""

from enum import Enum


class TaskStatus(str, Enum):
    """Lifecycle status of an engineering task."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED_FOR_APPROVAL = "paused_for_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowPhase(str, Enum):
    """Specific phase inside the LangGraph workflow."""
    INITIALIZED = "initialized"
    REPOSITORY_ANALYSIS = "repository_analysis"
    PLANNING = "planning"
    CODING = "coding"
    TESTING = "testing"
    DEBUGGING = "debugging"
    REVIEW = "review"
    COMMIT = "commit"
    PULL_REQUEST = "pull_request"
    FINISHED = "finished"


class ToolCategory(str, Enum):
    """Category classification for agent tools."""
    REPOSITORY = "repository"
    EDITING = "editing"
    EXECUTION = "execution"
    GIT = "git"
    GITHUB = "github"


class ApprovalStatus(str, Enum):
    """Status for human-in-the-loop action approval."""
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
