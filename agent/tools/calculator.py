import ast
import math
from typing import Any, Dict
from .base import BaseTool, ToolResult


class CalculatorTool(BaseTool):
    """Safe Math Calculator Tool evaluating mathematical expressions without using unsafe eval()."""

    name = "calculator"
    description = "Evaluates mathematical expressions safely (e.g. '2 ** 10 + sqrt(144)', 'log(100, 10)', 'sin(pi / 4)')."
    parameters_schema = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Mathematical expression to evaluate (e.g., '15 * 4 + 10', 'sqrt(256)')"
            }
        },
        "required": ["expression"]
    }

    _SAFE_FUNCTIONS: Dict[str, Any] = {
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "abs": abs,
        "round": round,
        "ceil": math.ceil,
        "floor": math.floor,
        "pi": math.pi,
        "e": math.e,
        "factorial": math.factorial,
        "pow": math.pow,
    }

    def _eval_node(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Expression):
            return self._eval_node(node.body)
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"Constant of type {type(node.value).__name__} is not allowed.")
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            elif isinstance(node.op, ast.Sub):
                return left - right
            elif isinstance(node.op, ast.Mult):
                return left * right
            elif isinstance(node.op, ast.Div):
                if right == 0:
                    raise ZeroDivisionError("Division by zero.")
                return left / right
            elif isinstance(node.op, ast.FloorDiv):
                if right == 0:
                    raise ZeroDivisionError("Floor division by zero.")
                return left // right
            elif isinstance(node.op, ast.Mod):
                return left % right
            elif isinstance(node.op, ast.Pow):
                return left ** right
            else:
                raise ValueError(f"Unsupported binary operator: {type(node.op).__name__}")
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +operand
            elif isinstance(node.op, ast.USub):
                return -operand
            else:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
        elif isinstance(node, ast.Name):
            if node.id in self._SAFE_FUNCTIONS:
                val = self._SAFE_FUNCTIONS[node.id]
                if isinstance(val, (int, float)):
                    return val
            raise ValueError(f"Undefined variable/constant: '{node.id}'")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in self._SAFE_FUNCTIONS:
                func = self._SAFE_FUNCTIONS[node.func.id]
                args = [self._eval_node(arg) for arg in node.args]
                return func(*args)
            raise ValueError(f"Function call '{ast.unparse(node.func)}' is not permitted.")
        else:
            raise ValueError(f"Unsupported expression element: {type(node).__name__}")

    def run(self, expression: str = "", **kwargs) -> ToolResult:
        if not expression or not expression.strip():
            return ToolResult(success=False, output="", error="Expression cannot be empty.")
        
        try:
            parsed = ast.parse(expression.strip(), mode="eval")
            result = self._eval_node(parsed)
            return ToolResult(success=True, output=str(result))
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Invalid mathematical expression: {str(e)}")
