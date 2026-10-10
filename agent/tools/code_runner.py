import sys
import io
import traceback
import contextlib
from typing import Dict, Any
from .base import BaseTool, ToolResult


class PythonInterpreterTool(BaseTool):
    """Executes Python code dynamically and returns captured stdout, stderr, and return values."""

    name = "python_interpreter"
    description = "Executes Python 3 code snippets dynamically. Useful for data analysis, string manipulation, complex calculations, and algorithm verification."
    parameters_schema = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python code snippet to execute."
            }
        },
        "required": ["code"]
    }

    def run(self, code: str = "", **kwargs) -> ToolResult:
        if not code or not code.strip():
            return ToolResult(success=False, output="", error="No code provided for execution.")

        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        # Isolated execution namespace
        globals_dict: Dict[str, Any] = {
            "__name__": "__main__",
            "__builtins__": __builtins__,
        }
        locals_dict: Dict[str, Any] = {}

        try:
            with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
                exec(code.strip(), globals_dict, locals_dict)
            
            output = stdout_buffer.getvalue()
            errors = stderr_buffer.getvalue()

            if errors and not output:
                return ToolResult(success=False, output=errors, error="Code emitted error output.")
            
            combined_output = output
            if errors:
                combined_output += f"\n[Stderr output]:\n{errors}"
            
            if not combined_output.strip():
                combined_output = "Code executed successfully (no stdout produced)."

            return ToolResult(success=True, output=combined_output)
        except Exception:
            err_trace = traceback.format_exc()
            return ToolResult(
                success=False,
                output=stdout_buffer.getvalue(),
                error=f"Runtime Exception:\n{err_trace}"
            )
