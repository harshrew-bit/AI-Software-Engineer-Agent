"""Repository inspection and navigation tools."""

import os
import re
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

from app.models.enums import ToolCategory
from app.tools.base import BaseTool, ToolExecutionContext, ToolResult

EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
    "node_modules",
    ".idea",
    ".vscode",
    "dist",
    "build",
    ".egg-info",
}


# --- List Files Tool ---
class ListFilesInput(BaseModel):
    directory: str = Field(default=".", description="Relative directory path to list")
    recursive: bool = Field(default=True, description="Whether to search recursively")
    pattern: Optional[str] = Field(default=None, description="Glob pattern filter, e.g. '*.py'")


class ListFilesTool(BaseTool):
    name = "list_files"
    description = "List files and directories in the repository with optional glob pattern matching."
    category = ToolCategory.REPOSITORY
    args_schema = ListFilesInput
    is_dangerous = False

    async def _run(self, args: ListFilesInput, context: ToolExecutionContext) -> ToolResult:
        try:
            target_dir = context.git_manager.validate_safe_path(args.directory)
            if not target_dir.exists() or not target_dir.is_dir():
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    error=f"Directory '{args.directory}' does not exist.",
                )

            matched_files: List[str] = []
            if args.recursive:
                for root, dirs, files in os.walk(target_dir):
                    # Filter out excluded dirs in-place
                    dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not d.endswith(".egg-info")]
                    for f in files:
                        full_path = Path(root) / f
                        rel_path = full_path.relative_to(context.workspace_path).as_posix()
                        if args.pattern:
                            if full_path.match(args.pattern):
                                matched_files.append(rel_path)
                        else:
                            matched_files.append(rel_path)
            else:
                for item in target_dir.iterdir():
                    if item.name in EXCLUDED_DIRS:
                        continue
                    rel_path = item.relative_to(context.workspace_path).as_posix()
                    if args.pattern:
                        if item.match(args.pattern):
                            matched_files.append(rel_path)
                    else:
                        matched_files.append(rel_path)

            matched_files.sort()
            output = "\n".join(matched_files) if matched_files else "No matching files found."
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=output,
                metadata={"count": len(matched_files)},
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=str(e))


# --- Read File Tool ---
class ReadFileInput(BaseModel):
    file_path: str = Field(..., description="Relative path to the file to read")
    start_line: Optional[int] = Field(default=1, ge=1, description="1-indexed starting line number")
    end_line: Optional[int] = Field(default=None, ge=1, description="1-indexed ending line number")


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read contents of a file with line numbers and optional line range slicing."
    category = ToolCategory.REPOSITORY
    args_schema = ReadFileInput
    is_dangerous = False

    async def _run(self, args: ReadFileInput, context: ToolExecutionContext) -> ToolResult:
        try:
            target_file = context.git_manager.validate_safe_path(args.file_path)
            if not target_file.exists():
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    error=f"File '{args.file_path}' does not exist.",
                )
            if not target_file.is_file():
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    error=f"Path '{args.file_path}' is a directory, not a file.",
                )

            # Check file size limit
            file_size = target_file.stat().st_size
            if file_size > context.settings.max_file_read_bytes:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    error=f"File '{args.file_path}' ({file_size} bytes) exceeds read limit of {context.settings.max_file_read_bytes} bytes.",
                )

            lines = target_file.read_text(encoding="utf-8", errors="replace").splitlines()
            total_lines = len(lines)

            start = args.start_line or 1
            end = args.end_line or total_lines

            start_idx = max(0, start - 1)
            end_idx = min(total_lines, end)

            selected_lines = lines[start_idx:end_idx]
            formatted_lines = [
                f"{start_idx + i + 1:4d} | {line}"
                for i, line in enumerate(selected_lines)
            ]

            output = (
                f"File: {args.file_path} (Lines {start_idx + 1}-{end_idx} of {total_lines})\n"
                f"{'-' * 50}\n"
                + "\n".join(formatted_lines)
            )

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=output,
                metadata={"total_lines": total_lines, "sliced_lines": len(selected_lines)},
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=str(e))


# --- Search Code Tool ---
class SearchCodeInput(BaseModel):
    query: str = Field(..., description="String or regex pattern to search for")
    file_pattern: Optional[str] = Field(default=None, description="Glob filter, e.g. '*.py'")
    case_sensitive: bool = Field(default=False, description="Case-sensitive search")


class SearchCodeTool(BaseTool):
    name = "search_code"
    description = "Search for text or regex patterns across files in the workspace."
    category = ToolCategory.REPOSITORY
    args_schema = SearchCodeInput
    is_dangerous = False

    async def _run(self, args: SearchCodeInput, context: ToolExecutionContext) -> ToolResult:
        try:
            flags = 0 if args.case_sensitive else re.IGNORECASE
            try:
                pattern = re.compile(args.query, flags)
            except re.error as err:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    error=f"Invalid regular expression '{args.query}': {str(err)}",
                )

            results: List[str] = []
            max_results = context.settings.max_search_results
            match_count = 0

            for root, dirs, files in os.walk(context.workspace_path):
                dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not d.endswith(".egg-info")]
                for file_name in files:
                    full_path = Path(root) / file_name
                    if args.file_pattern and not full_path.match(args.file_pattern):
                        continue

                    rel_path = full_path.relative_to(context.workspace_path).as_posix()
                    try:
                        content = full_path.read_text(encoding="utf-8", errors="replace")
                    except Exception:
                        continue

                    for line_no, line in enumerate(content.splitlines(), start=1):
                        if pattern.search(line):
                            match_count += 1
                            snippet = line.strip()
                            if len(snippet) > 120:
                                snippet = snippet[:117] + "..."
                            results.append(f"{rel_path}:{line_no}: {snippet}")
                            if match_count >= max_results:
                                break
                    if match_count >= max_results:
                        break
                if match_count >= max_results:
                    break

            if not results:
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    output=f"No matches found for query '{args.query}'.",
                    metadata={"matches": 0},
                )

            output = "\n".join(results)
            if match_count >= max_results:
                output += f"\n\n[Truncated: capped at {max_results} matches]"

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=output,
                metadata={"matches": match_count},
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=str(e))


# --- Inspect Directory Tool ---
class InspectDirectoryInput(BaseModel):
    directory: str = Field(default=".", description="Relative directory path to inspect")
    max_depth: int = Field(default=3, ge=1, le=5, description="Maximum directory depth to render")


class InspectDirectoryTool(BaseTool):
    name = "inspect_directory"
    description = "Generate an indented tree view of the directory structure."
    category = ToolCategory.REPOSITORY
    args_schema = InspectDirectoryInput
    is_dangerous = False

    async def _run(self, args: InspectDirectoryInput, context: ToolExecutionContext) -> ToolResult:
        try:
            target_dir = context.git_manager.validate_safe_path(args.directory)
            if not target_dir.exists() or not target_dir.is_dir():
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    error=f"Directory '{args.directory}' does not exist.",
                )

            lines: List[str] = [f"📂 {args.directory or '.'}"]

            def _walk(current: Path, prefix: str, depth: int):
                if depth > args.max_depth:
                    return
                try:
                    entries = sorted(
                        [e for e in current.iterdir() if e.name not in EXCLUDED_DIRS],
                        key=lambda e: (not e.is_dir(), e.name.lower()),
                    )
                except PermissionError:
                    return

                for i, entry in enumerate(entries):
                    is_last = i == len(entries) - 1
                    connector = "└── " if is_last else "├── "
                    sub_prefix = "    " if is_last else "│   "

                    if entry.is_dir():
                        lines.append(f"{prefix}{connector}📁 {entry.name}/")
                        _walk(entry, prefix + sub_prefix, depth + 1)
                    else:
                        lines.append(f"{prefix}{connector}📄 {entry.name}")

            _walk(target_dir, "", 1)
            return ToolResult(
                tool_name=self.name,
                success=True,
                output="\n".join(lines),
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=str(e))
