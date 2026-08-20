# AI Software Engineer Agent

A production-ready autonomous software engineering agent built with **LangGraph**, **FastAPI**, **Docker Sandbox**, **Google Gemini / OpenAI**, and a modern **React + Vite + Tailwind CSS** dashboard. It features strict security guardrails, full observability, self-healing test loops, and human-in-the-loop approval checkpoints.

---

## Architecture Overview

```
User Prompt & Repo URL
         │
         ▼
┌────────────────────────────────────────────────────────┐
│             LangGraph Deterministic State Machine      │
│                                                        │
│  [1. Analysis] ──► [2. Planning] ──► [3. Coding Tools] │
│                                             │          │
│  [6. Review]   ◄── [5. Debug Loop] ◄── [4. Tests]      │
│         │                                              │
│         ▼                                              │
│  [7. Git Commit] ──► [8. Push Branch & Create PR]     │
└────────────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────┐
│               Frontend Dashboard (React + Vite)        │
│  • Visual Workflow Tracker  • Live SSE Event Stream    │
│  • Expandable Tool History  • Unified Git Diff Viewer  │
│  • Test Run Diagnostics     • Human Approval Actions   │
└────────────────────────────────────────────────────────┘
```

---

## Key Features

- **Isolated Execution Plane**: Untrusted repository scripts and test commands execute strictly within an ephemeral Docker sandbox (non-root, cap-dropped, timeout-guarded, with secure local fallback).
- **LangGraph State Orchestrator**: Deterministic workflow progression with iterative Test & Debug self-healing loops (`repository_analysis` -> `planning` -> `coding` -> `testing` -> `debugging` -> `review` -> `commit` -> `pull_request`).
- **Provider-Agnostic LLM Layer**: First-class support for **Gemini 2.5 / 3.6** (Google GenAI Interactions API) and **OpenAI** (GPT-4o, GPT-4o-mini with structured outputs) alongside mockable abstractions for reproducible testing.
- **Traceable Tool Auditing**: Every tool call, exit code, execution time, input arguments, and line-level file diff is recorded in SQLite / SQLAlchemy persistence.
- **Human-In-The-Loop (HITL) Checkpoints**: Safety gates pausing execution before destructive operations (file deletions, dependency installs, git pushes, PR submissions) with real-time UI approval & rejection actions.
- **Real-Time Progress Streaming**: Dual-mode real-time sync with SSE (Server-Sent Events) live streaming and automated polling fallback.
- **Modern Developer Dashboard**: Dark-themed React dashboard built with Tailwind CSS, Lucide icons, and responsive layouts.

---

## Project Structure

```
AI-Software-Engineer-Agent/
├── app/
│   ├── main.py                     # FastAPI server application & CORS
│   ├── config/                     # Pydantic Settings & environment config
│   ├── models/                     # LangGraph state, API DTOs & SQLAlchemy entities
│   ├── database/                   # Async session management & CRUD repositories
│   ├── llm/                        # Gemini, OpenAI & Mock LLM clients
│   ├── repository/                 # Git workspace manager (clone, branch, diff, commit, push)
│   ├── sandbox/                    # Docker & local subprocess sandboxes with policies
│   ├── tools/                      # Repository, Editing, Execution, Git & GitHub tools
│   ├── agents/                     # Specialized prompts & structured schemas
│   ├── graph/                      # LangGraph state machine (nodes, edges, builder)
│   ├── github/                     # GitHub PR and issue API client
│   ├── services/                   # Task orchestrator, EventBus, Workspace manager
│   └── api/                        # REST endpoints & SSE streaming routes
├── frontend/
│   ├── src/
│   │   ├── api/                    # Typed API client & SSE subscriber
│   │   ├── components/
│   │   │   ├── common/             # StatusBadge, CodeBlock
│   │   │   ├── layout/             # Navbar
│   │   │   ├── dashboard/          # CreateTaskForm, TaskListTable
│   │   │   └── task/               # TaskHeader, PipelineTracker, ToolHistoryList,
│   │   │                           # ModifiedFilesView, TestResultsView, ApprovalCard, ErrorCard
│   │   ├── hooks/                  # useTaskList, useTaskDetail
│   │   ├── pages/                  # DashboardPage, TaskDetailPage
│   │   ├── types/                  # TypeScript definitions mirroring backend Pydantic models
│   │   ├── App.tsx                 # Root application component
│   │   └── main.tsx                # React DOM entrypoint
│   ├── package.json
│   ├── tailwind.config.js
│   ├── vite.config.ts
│   └── tsconfig.json
├── tests/
│   ├── unit/                       # Unit tests for config, models, db, sandbox, tools, graph, llm
│   └── integration/                # API and multi-turn workflow integration tests
├── pyproject.toml
├── .env.example
└── README.md
```

---

## Quickstart

### 1. Environment Setup

```bash
# Create and activate Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python backend dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy `.env.example` to `.env` and set your API keys:

```bash
cp .env.example .env
```

Key environment variables:
```env
LLM_PROVIDER=gemini                # "gemini" or "openai"
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
GITHUB_TOKEN=your_github_token
```

### 3. Run Backend Test Suite

```bash
.venv/bin/pytest -v
```

### 4. Start the Backend API Server

```bash
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir app --reload-exclude "temp_workspaces/*"
```
- Interactive API Swagger docs: `http://localhost:8000/docs`
- ReDoc documentation: `http://localhost:8000/redoc`

### 5. Start the Frontend Dashboard

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## Frontend Dashboard Features

1. **Dashboard Home**:
   - Quick launch form with preset templates (e.g. *Hello World Endpoint*, *Health Check*, *Validation Fix*).
   - Advanced options for base branch, custom working branch, and max test retries.
   - Recent tasks table with status badges, live phases, and GitHub PR links.

2. **Task Execution View**:
   - **Task Header**: Repository link, branches, commit SHA, PR button, and task cancellation.
   - **Pipeline Tracker**: Visual step-by-step state tracker showing active (pulsing), completed, failed, and debugging retry stages.
   - **Tool Execution Trail**: Monospace expandable cards showing input arguments, sandbox outputs, exit codes, execution durations, and error logs.
   - **Modified Files & Diff**: Side-by-side tabs for file catalog and live unified Git diff viewer.
   - **Test Suite Results**: Passed/failed indicators, test metrics (failures/errors), and full stdout/stderr logs.
   - **Human-in-the-Loop Approval Banner**: Interactive approval and rejection cards for gated safety operations.
   - **Live Event Stream**: Real-time SSE logs of agent thoughts and state machine transitions.

---

## API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/tasks` | Create and launch an autonomous engineering task |
| `GET` | `/api/v1/tasks` | List recent tasks and statuses |
| `GET` | `/api/v1/tasks/{task_id}` | Get task summary and active implementation plan |
| `GET` | `/api/v1/tasks/{task_id}/detail` | Get full task history (tool calls, test results, approval) |
| `GET` | `/api/v1/tasks/{task_id}/events` | Stream real-time execution events via SSE |
| `GET` | `/api/v1/tasks/{task_id}/diff` | View active unified git diff against base branch |
| `POST` | `/api/v1/tasks/{task_id}/approve` | Submit human approval or rejection decision |
| `POST` | `/api/v1/tasks/{task_id}/cancel` | Cancel an ongoing task run |
