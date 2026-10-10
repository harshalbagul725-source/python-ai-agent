import json
import inspect
from typing import Callable, Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    success: bool
    output: str
    error: Optional[str] = None

    def __str__(self) -> str:
        if self.success:
            return self.output
        return f"Error: {self.error or 'Unknown error occurred'}\nDetails: {self.output}"


class BaseTool:
    """Abstract Base Class for Agent Tools"""

    name: str = ""
    description: str = ""
    parameters_schema: Dict[str, Any] = {}

    def run(self, **kwargs) -> ToolResult:
        raise NotImplementedError("Tool execution logic must be implemented in subclass.")

    def get_schema_prompt(self) -> str:
        """Returns readable schema representation for LLM prompts."""
        params_str = json.dumps(self.parameters_schema, indent=2)
        return f"- **{self.name}**: {self.description}\n  Parameters JSON Schema:\n{params_str}"


class FunctionTool(BaseTool):
    """Wrapper tool for custom python functions."""

    def __init__(self, func: Callable, name: str = "", description: str = ""):
        self.func = func
        self.name = name or func.__name__
        self.description = description or (func.__doc__.strip() if func.__doc__ else "No description provided.")
        self.parameters_schema = self._build_schema_from_func(func)

    def _build_schema_from_func(self, func: Callable) -> Dict[str, Any]:
        sig = inspect.signature(func)
        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            param_type = "string"
            if param.annotation == int:
                param_type = "integer"
            elif param.annotation == float:
                param_type = "number"
            elif param.annotation == bool:
                param_type = "boolean"
            elif param.annotation in (dict, Dict):
                param_type = "object"
            elif param.annotation in (list, List):
                param_type = "array"

            properties[param_name] = {
                "type": param_type,
                "description": f"Parameter {param_name}"
            }
            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        return {
            "type": "object",
            "properties": properties,
            "required": required
        }

    def run(self, **kwargs) -> ToolResult:
        try:
            result = self.func(**kwargs)
            return ToolResult(success=True, output=str(result))
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


class ToolRegistry:
    """Registry to manage tools accessible by the Agent."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool instance."""
        if not tool.name:
            raise ValueError("Tool must have a valid name.")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        return list(self._tools.values())

    def execute(self, name: str, kwargs: Dict[str, Any]) -> ToolResult:
        tool_instance = self.get(name)
        if not tool_instance:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool '{name}' is not registered in ToolRegistry. Available tools: {list(self._tools.keys())}"
            )
        return tool_instance.run(**kwargs)

    def get_prompt_description(self) -> str:
        """Formats available tools for the System Prompt."""
        descriptions = [tool.get_schema_prompt() for tool in self._tools.values()]
        return "\n\n".join(descriptions)


def tool(name: str = "", description: str = ""):
    """Decorator to easily convert a function into a BaseTool."""
    def decorator(func: Callable) -> FunctionTool:
        return FunctionTool(func, name=name, description=description)
    return decorator
