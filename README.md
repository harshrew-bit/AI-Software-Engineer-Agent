# AI Software Engineer Agent

A production-oriented autonomous software engineering agent built with **LangGraph**, **FastAPI**, **Docker Sandbox**, and **Google Gemini**, equipped with strict security guardrails, full observability, and human-in-the-loop approval checkpoints.

---

## Key Features

- **Isolated Execution Plane**: Untrusted repository scripts and test commands execute strictly within an ephemeral Docker sandbox (non-root, cap-dropped, timeout-guarded, with secure local fallback).
- **LangGraph State Orchestrator**: Deterministic workflow progression with iterative Test & Debug self-healing loops (`repository_analysis` -> `planning` -> `coding` -> `testing` -> `debugging` -> `review` -> `commit` -> `pull_request`).
- **Provider-Agnostic LLM Layer**: First-class support for Gemini 2.5 / 3.6 alongside mockable abstractions for reproducible testing.
- **Traceable Tool Auditing**: Every tool call and line-level file diff is recorded in SQLAlchemy persistence.
- **Human-In-The-Loop (HITL) Checkpoints**: Safety gates pausing execution before destructive operations (file deletions, dependency installs, git pushes, PR submissions).
- **Real-Time Progress Streaming**: SSE (Server-Sent Events) live streaming for task step transitions, tool calls, and test results.

---

## Project Structure

```
AI-Software-Engineer-Agent/
├── app/
│   ├── main.py                     # FastAPI server application
│   ├── config/                     # Pydantic Settings & environment config
│   ├── models/                     # LangGraph state, API DTOs & SQLAlchemy entities
│   ├── database/                   # Async session management & CRUD repositories
│   ├── llm/                        # BaseLLMClient interface, Gemini & Mock client
│   ├── repository/                 # Git workspace manager (clone, branch, diff, commit)
│   ├── sandbox/                    # Docker & local subprocess sandboxes with policies
│   ├── tools/                      # Repository, Editing, Execution, Git & GitHub tools
│   ├── agents/                     # Specialized prompts & structured schemas
│   ├── graph/                      # LangGraph state machine (nodes, edges, builder)
│   ├── github/                     # GitHub PR and issue API client
│   ├── services/                   # Task orchestrator, EventBus, Workspace manager
│   └── api/                        # REST endpoints & SSE streaming routes
├── tests/
│   ├── unit/                       # Unit tests for config, models, db, sandbox, tools, graph
│   └── integration/                # API and multi-turn workflow integration tests
├── pyproject.toml
├── .env.example
└── README.md
```

---

## Quickstart

### 1. Environment Setup

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy `.env.example` to `.env` and set your API keys:

```bash
cp .env.example .env
```

### 3. Run Test Suite

```bash
.venv/bin/pytest tests/ -v
```

### 4. Start the Server

```bash
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive API documentation will be available at `http://localhost:8000/docs`.

---

## API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/tasks` | Create and launch an autonomous engineering task |
| `GET` | `/api/v1/tasks` | List recent tasks and statuses |
| `GET` | `/api/v1/tasks/{task_id}` | Get task summary and active implementation plan |
| `GET` | `/api/v1/tasks/{task_id}/detail` | Get full task history (tool calls, test results) |
| `GET` | `/api/v1/tasks/{task_id}/events` | Stream real-time execution events via SSE |
| `GET` | `/api/v1/tasks/{task_id}/diff` | View active unified git diff against base branch |
| `POST` | `/api/v1/tasks/{task_id}/approve` | Submit human approval or rejection decision |
| `POST` | `/api/v1/tasks/{task_id}/cancel` | Cancel an ongoing task run |
