"""Unit tests for Agent Tool Suite and Registry."""

from pathlib import Path
import pytest

from app.config.settings import Settings
from app.database.repository import TaskRepository
from app.models.enums import ApprovalStatus
from app.repository.git_manager import GitWorkspaceManager
from app.sandbox.local import LocalSubprocessSandbox
from app.tools.base import ToolExecutionContext
from app.tools.edit_tools import CreateFileTool, DeleteFileTool, ModifyFileTool
from app.tools.execution_tools import RunCommandTool, RunTestsTool
from app.tools.git_tools import GitCommitTool, GitDiffTool, GitStatusTool
from app.tools.registry import ToolRegistry, create_default_tool_registry
from app.tools.repo_tools import (
    InspectDirectoryTool,
    ListFilesTool,
    ReadFileTool,
    SearchCodeTool,
)


@pytest.fixture
def tool_context(tmp_path):
    """Fixture providing an active tool execution context."""
    ws = tmp_path / "workspace"
    git_manager = GitWorkspaceManager(task_id="task-tools-1", workspace_path=ws)
    git_manager.init_local_empty_repo(default_branch="main")

    sandbox = LocalSubprocessSandbox(workspace_path=ws)
    settings = Settings(
        workspaces_root=tmp_path / "workspaces",
        require_human_approval_for_destructive_actions=True,
    )

    return ToolExecutionContext(
        task_id="task-tools-1",
        workspace_path=ws,
        git_manager=git_manager,
        sandbox=sandbox,
        settings=settings,
    )


@pytest.mark.asyncio
async def test_repo_tools(tool_context):
    """Test ListFiles, ReadFile, SearchCode, and InspectDirectory."""
    ws = tool_context.workspace_path

    # Create dummy files
    (ws / "src").mkdir(parents=True, exist_ok=True)
    (ws / "src" / "main.py").write_text("def hello():\n    return 'world'\n")
    (ws / "src" / "utils.py").write_text("def add(a, b):\n    return a + b\n")

    # 1. List Files
    list_tool = ListFilesTool()
    res = await list_tool.execute({"directory": ".", "pattern": "*.py"}, tool_context)
    assert res.success is True
    assert "src/main.py" in res.output
    assert "src/utils.py" in res.output

    # 2. Read File (Slice lines 1 to 2)
    read_tool = ReadFileTool()
    res = await read_tool.execute(
        {"file_path": "src/main.py", "start_line": 1, "end_line": 2},
        tool_context,
    )
    assert res.success is True
    assert "def hello():" in res.output
    assert "return 'world'" in res.output

    # 3. Search Code
    search_tool = SearchCodeTool()
    res = await search_tool.execute({"query": "def add"}, tool_context)
    assert res.success is True
    assert "src/utils.py:1:" in res.output

    # 4. Inspect Directory
    inspect_tool = InspectDirectoryTool()
    res = await inspect_tool.execute({"directory": "."}, tool_context)
    assert res.success is True
    assert "src/" in res.output


@pytest.mark.asyncio
async def test_edit_tools(tool_context):
    """Test CreateFile, ModifyFile, and DeleteFile."""
    ws = tool_context.workspace_path

    # 1. Create File
    create_tool = CreateFileTool()
    res = await create_tool.execute(
        {
            "file_path": "src/auth/jwt.py",
            "content": "SECRET_KEY = 'secret'\nALGORITHM = 'HS256'\n",
        },
        tool_context,
    )
    assert res.success is True
    assert (ws / "src/auth/jwt.py").exists()

    # 2. Modify File with surgical replacement
    modify_tool = ModifyFileTool()
    res = await modify_tool.execute(
        {
            "file_path": "src/auth/jwt.py",
            "replacements": [
                {
                    "old_content": "SECRET_KEY = 'secret'",
                    "new_content": "SECRET_KEY = 'env_secret_key'",
                }
            ],
        },
        tool_context,
    )
    assert res.success is True
    content = (ws / "src/auth/jwt.py").read_text()
    assert "env_secret_key" in content
    assert "HS256" in content

    # 3. Modify File Failure on mismatch
    res_fail = await modify_tool.execute(
        {
            "file_path": "src/auth/jwt.py",
            "replacements": [
                {
                    "old_content": "NON_EXISTENT_CONTENT",
                    "new_content": "foo",
                }
            ],
        },
        tool_context,
    )
    assert res_fail.success is False
    assert "not found" in res_fail.error


@pytest.mark.asyncio
async def test_execution_and_git_tools(tool_context):
    """Test RunCommand, RunTests, GitStatus, and GitCommit."""
    ws = tool_context.workspace_path

    # 1. Run Command in sandbox
    run_tool = RunCommandTool()
    res = await run_tool.execute(
        {"command": "python3 -c \"print('Sandbox execution passed')\""},
        tool_context,
    )
    assert res.success is True
    assert "Sandbox execution passed" in res.output

    # 2. Run Tests
    test_file = ws / "test_sample.py"
    test_file.write_text("def test_ok():\n    assert 1 == 1\n")

    run_tests_tool = RunTestsTool()
    res = await run_tests_tool.execute(
        {"test_command": "pytest test_sample.py -v"},
        tool_context,
    )
    assert res.success is True
    assert "PASSED" in res.output

    # 3. Git Status & Commit
    status_tool = GitStatusTool()
    res = await status_tool.execute({}, tool_context)
    assert res.success is True
    assert "test_sample.py" in res.output

    commit_tool = GitCommitTool()
    res = await commit_tool.execute({"message": "Add test_sample.py"}, tool_context)
    assert res.success is True
    assert "Committed changes with SHA:" in res.output


@pytest.mark.asyncio
async def test_tool_registry_and_dangerous_action_gate(tmp_path, async_db_session):
    """Test registry dispatch and dangerous action approval gate interception."""
    ws = tmp_path / "workspace"
    git_manager = GitWorkspaceManager(task_id="task-gate-1", workspace_path=ws)
    git_manager.init_local_empty_repo()

    target_file = ws / "critical.py"
    target_file.write_text("# Critical file")

    repo = TaskRepository(async_db_session)
    await repo.create_task(
        task_id="task-gate-1",
        repository_url="https://github.com/example/demo",
        user_instruction="Delete critical file",
        workspace_path=str(ws),
    )

    context = ToolExecutionContext(
        task_id="task-gate-1",
        workspace_path=ws,
        git_manager=git_manager,
        sandbox=LocalSubprocessSandbox(workspace_path=ws),
        settings=Settings(
            workspaces_root=tmp_path / "workspaces",
            require_human_approval_for_destructive_actions=True,
        ),
        repository=repo,
    )

    registry = create_default_tool_registry()

    # Verify tool definitions export
    defs = registry.get_tool_definitions()
    assert len(defs) >= 10
    names = [d.name for d in defs]
    assert "list_files" in names
    assert "modify_file" in names
    assert "run_tests" in names
    assert "delete_file" in names

    # Dispatch delete_file -> Should be intercepted by safety gate!
    res = await registry.dispatch(
        "delete_file",
        {"file_path": "critical.py"},
        context,
    )
    assert res.requires_approval is True
    assert res.approval_status == ApprovalStatus.PENDING
    assert target_file.exists()  # File was NOT deleted because approval is required
