"""File editing tools with safety verification and diff tracking."""

from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

from app.models.enums import ToolCategory
from app.tools.base import BaseTool, ToolExecutionContext, ToolResult


# --- Create File Tool ---
class CreateFileInput(BaseModel):
    file_path: str = Field(..., description="Relative path for the new file")
    content: str = Field(..., description="Exact content to write into the file")
    overwrite: bool = Field(default=False, description="Whether to overwrite if file already exists")


class CreateFileTool(BaseTool):
    name = "create_file"
    description = "Create a new file in the workspace, automatically creating any parent directories."
    category = ToolCategory.EDITING
    args_schema = CreateFileInput
    is_dangerous = False

    async def _run(self, args: CreateFileInput, context: ToolExecutionContext) -> ToolResult:
        try:
            target_path = context.git_manager.validate_safe_path(args.file_path)
            if target_path.exists() and not args.overwrite:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    error=f"File '{args.file_path}' already exists. Set overwrite=True to replace it.",
                )

            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(args.content, encoding="utf-8")

            line_count = len(args.content.splitlines())
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=f"Successfully created '{args.file_path}' ({line_count} lines).",
                metadata={"file_path": args.file_path, "line_count": line_count},
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=str(e))


# --- Modify File Tool ---
class ReplacementChunk(BaseModel):
    old_content: str = Field(..., description="Exact string in the file to be replaced")
    new_content: str = Field(..., description="Replacement text")
    start_line: Optional[int] = Field(default=None, description="Optional starting line hint (1-indexed)")
    end_line: Optional[int] = Field(default=None, description="Optional ending line hint (1-indexed)")


class ModifyFileInput(BaseModel):
    file_path: str = Field(..., description="Relative path of file to modify")
    replacements: List[ReplacementChunk] = Field(
        ..., description="List of search and replacement chunks"
    )


class ModifyFileTool(BaseTool):
    name = "modify_file"
    description = (
        "Modify an existing file using precise replacement chunks. "
        "old_content must match the file content exactly."
    )
    category = ToolCategory.EDITING
    args_schema = ModifyFileInput
    is_dangerous = False

    async def _run(self, args: ModifyFileInput, context: ToolExecutionContext) -> ToolResult:
        try:
            target_path = context.git_manager.validate_safe_path(args.file_path)
            if not target_path.exists() or not target_path.is_file():
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    error=f"File '{args.file_path}' does not exist or is not a file.",
                )

            current_content = target_path.read_text(encoding="utf-8")
            updated_content = current_content

            for idx, chunk in enumerate(args.replacements, start=1):
                if chunk.old_content not in updated_content:
                    return ToolResult(
                        tool_name=self.name,
                        success=False,
                        error=(
                            f"Replacement chunk #{idx} failed: old_content was not found in '{args.file_path}'. "
                            f"Make sure whitespace, indentation, and characters match the file exactly."
                        ),
                    )

                count = updated_content.count(chunk.old_content)
                if count > 1:
                    return ToolResult(
                        tool_name=self.name,
                        success=False,
                        error=(
                            f"Replacement chunk #{idx} matched {count} times in '{args.file_path}'. "
                            f"Include more surrounding context lines in old_content to make the match unique."
                        ),
                    )

                updated_content = updated_content.replace(chunk.old_content, chunk.new_content, 1)

            target_path.write_text(updated_content, encoding="utf-8")

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=f"Successfully applied {len(args.replacements)} replacement(s) to '{args.file_path}'.",
                metadata={"file_path": args.file_path, "replacements_count": len(args.replacements)},
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=str(e))


# --- Delete File Tool ---
class DeleteFileInput(BaseModel):
    file_path: str = Field(..., description="Relative path of file to delete")


class DeleteFileTool(BaseTool):
    name = "delete_file"
    description = "Delete a file from the repository. This is a protected action."
    category = ToolCategory.EDITING
    args_schema = DeleteFileInput
    is_dangerous = True  # Triggers HITL approval checkpoint

    async def _run(self, args: DeleteFileInput, context: ToolExecutionContext) -> ToolResult:
        try:
            target_path = context.git_manager.validate_safe_path(args.file_path)
            if not target_path.exists():
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    error=f"File '{args.file_path}' does not exist.",
                )

            if target_path.is_file():
                target_path.unlink()
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    output=f"Successfully deleted file '{args.file_path}'.",
                )
            else:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    error=f"'{args.file_path}' is a directory, not a file.",
                )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=str(e))
