import os
import pytest
from pathlib import Path
from agent.tools.calculator import CalculatorTool
from agent.tools.code_runner import PythonInterpreterTool
from agent.tools.file_system import ReadFileTool, WriteFileTool, ListDirTool, SearchFilesTool
from agent.tools.system_info import SystemInfoTool, CurrentDateTimeTool


def test_calculator_tool():
    calc = CalculatorTool()
    
    # Simple addition and multiplication
    res1 = calc.run(expression="15 + 25 * 4")
    assert res1.success is True
    assert res1.output == "115"

    # Math functions: sqrt, pow
    res2 = calc.run(expression="sqrt(256) + pow(2, 3)")
    assert res2.success is True
    assert res2.output == "24.0"

    # Error handling for division by zero
    res3 = calc.run(expression="10 / 0")
    assert res3.success is False
    assert "Division by zero" in res3.error


def test_python_interpreter_tool():
    interpreter = PythonInterpreterTool()
    
    code = "x = [i**2 for i in range(5)]\nprint('RESULT:', sum(x))"
    res = interpreter.run(code=code)
    assert res.success is True
    assert "RESULT: 30" in res.output


def test_file_system_tools(tmp_path):
    test_file = tmp_path / "sample.txt"
    writer = WriteFileTool()
    reader = ReadFileTool()
    lister = ListDirTool()
    searcher = SearchFilesTool()

    # Write file
    w_res = writer.run(filepath=str(test_file), content="Hello Autonomous AI Agent!")
    assert w_res.success is True

    # Read file
    r_res = reader.run(filepath=str(test_file))
    assert r_res.success is True
    assert "Hello Autonomous AI Agent!" in r_res.output

    # List dir
    l_res = lister.run(dir_path=str(tmp_path))
    assert l_res.success is True
    assert "sample.txt" in l_res.output

    # Search file
    s_res = searcher.run(query="Autonomous", root_dir=str(tmp_path))
    assert s_res.success is True
    assert "sample.txt" in s_res.output


def test_system_info_tools():
    sys_tool = SystemInfoTool()
    time_tool = CurrentDateTimeTool()

    sys_res = sys_tool.run()
    assert sys_res.success is True
    assert "OS" in sys_res.output

    time_res = time_tool.run()
    assert time_res.success is True
    assert "ISO Timestamp" in time_res.output
