import os
import glob
from pathlib import Path
from typing import Optional
from .base import BaseTool, ToolResult


class ReadFileTool(BaseTool):
    """Tool to read text content from a file."""

    name = "read_file"
    description = "Reads text contents of a file at the given relative or absolute file path."
    parameters_schema = {
        "type": "object",
        "properties": {
            "filepath": {
                "type": "string",
                "description": "Path to the file to read."
            },
            "max_lines": {
                "type": "integer",
                "description": "Optional maximum lines to read (default: 500)."
            }
        },
        "required": ["filepath"]
    }

    def run(self, filepath: str = "", max_lines: Optional[int] = 500, **kwargs) -> ToolResult:
        if not filepath:
            return ToolResult(success=False, output="", error="Filepath parameter is required.")
        
        path = Path(filepath)
        if not path.exists():
            return ToolResult(success=False, output="", error=f"File not found: {filepath}")
        if not path.is_file():
            return ToolResult(success=False, output="", error=f"Path is not a file: {filepath}")
        
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            
            limit = max_lines or 500
            truncated = len(lines) > limit
            content_lines = lines[:limit]
            
            result_str = "".join(content_lines)
            if truncated:
                result_str += f"\n... [Truncated {len(lines) - limit} lines]"
            
            return ToolResult(success=True, output=result_str)
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


class WriteFileTool(BaseTool):
    """Tool to write or append content to a file."""

    name = "write_file"
    description = "Writes or appends text content to a file at the specified path."
    parameters_schema = {
        "type": "object",
        "properties": {
            "filepath": {
                "type": "string",
                "description": "Path to the target file."
            },
            "content": {
                "type": "string",
                "description": "Text content to write."
            },
            "append": {
                "type": "boolean",
                "description": "If true, appends content; otherwise overwrites file."
            }
        },
        "required": ["filepath", "content"]
    }

    def run(self, filepath: str = "", content: str = "", append: bool = False, **kwargs) -> ToolResult:
        if not filepath:
            return ToolResult(success=False, output="", error="Filepath parameter is required.")
        
        path = Path(filepath)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            mode = "a" if append else "w"
            with open(path, mode, encoding="utf-8") as f:
                f.write(content)
            
            action_desc = "appended to" if append else "written to"
            return ToolResult(
                success=True,
                output=f"Successfully {action_desc} {filepath} ({len(content)} characters)."
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


class ListDirTool(BaseTool):
    """Tool to list files and subdirectories."""

    name = "list_dir"
    description = "Lists directory contents for a given directory path."
    parameters_schema = {
        "type": "object",
        "properties": {
            "dir_path": {
                "type": "string",
                "description": "Directory path to list (defaults to current directory '.')."
            }
        }
    }

    def run(self, dir_path: str = ".", **kwargs) -> ToolResult:
        target = Path(dir_path or ".")
        if not target.exists():
            return ToolResult(success=False, output="", error=f"Directory path does not exist: {dir_path}")
        if not target.is_dir():
            return ToolResult(success=False, output="", error=f"Path is not a directory: {dir_path}")
        
        try:
            entries = sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            items = []
            for entry in entries:
                prefix = "[DIR] " if entry.is_dir() else "[FILE]"
                size = f" ({entry.stat().st_size} bytes)" if entry.is_file() else ""
                items.append(f"{prefix} {entry.name}{size}")
            
            out = f"Directory contents of '{dir_path}':\n" + "\n".join(items) if items else f"Directory '{dir_path}' is empty."
            return ToolResult(success=True, output=out)
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


class SearchFilesTool(BaseTool):
    """Tool to search for text inside files in a workspace."""

    name = "search_files"
    description = "Searches for a specific query string within files inside a directory."
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search text pattern."
            },
            "root_dir": {
                "type": "string",
                "description": "Root directory to search in (defaults to '.')."
            },
            "file_pattern": {
                "type": "string",
                "description": "File glob pattern e.g. '*.py' or '*.md' (defaults to '*')."
            }
        },
        "required": ["query"]
    }

    def run(self, query: str = "", root_dir: str = ".", file_pattern: str = "*", **kwargs) -> ToolResult:
        if not query:
            return ToolResult(success=False, output="", error="Query parameter is required.")
        
        results = []
        try:
            search_path = os.path.join(root_dir, "**", file_pattern)
            for file_path in glob.glob(search_path, recursive=True):
                if os.path.isfile(file_path):
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            for idx, line in enumerate(f, 1):
                                if query.lower() in line.lower():
                                    results.append(f"{file_path}:{idx}: {line.strip()}")
                                    if len(results) >= 50:
                                        break
                    except Exception:
                        continue
                if len(results) >= 50:
                    break
            
            if not results:
                return ToolResult(success=True, output=f"No matches found for '{query}'.")
            
            header = f"Found {len(results)} matches for '{query}':\n"
            return ToolResult(success=True, output=header + "\n".join(results))
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
