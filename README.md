# Autonomous Python AI Agent 🤖

A modular, extensible, and high-performance **Autonomous AI Agent** framework written in pure Python. It uses the **ReAct (Reasoning + Acting)** paradigm to autonomously break down user requests, reason step-by-step, invoke tools, process observations, and deliver precise solutions.

---

## ✨ Features

- 🧠 **ReAct Reasoning Loop**: Step-by-step reasoning cycle (Thought ➔ Action ➔ Observation ➔ Final Answer).
- 🛠️ **Built-in Tool Ecosystem**:
  - `calculator`: AST-based safe math expression evaluator.
  - `python_interpreter`: Sandboxed dynamic Python code execution.
  - `file_system` (`read_file`, `write_file`, `list_dir`, `search_files`): Workspace file I/O operations.
  - `web_search`: Live search tool with graceful offline fallback.
  - `system_info` & `current_date_time`: Host system diagnostics and time metadata.
- 💾 **Dual Memory Architecture**:
  - **Short-Term Memory**: Conversation history for turn-based reasoning.
  - **Long-Term Memory**: Persistent JSON key-value store across sessions.
- 🔌 **Multi-LLM Support**:
  - **Google Gemini API** integration (`google-genai`).
  - **Mock / Offline Provider** mode for instant testing without API keys.
- 🎨 **Rich CLI UI**: Interactive color-coded terminal with markdown rendering and progress panels.

---

## 🚀 Quick Start

### 1. Requirements

- Python 3.10+
- Virtual environment (`.venv`) initialized via `uv` or `python -m venv`

### 2. Setup & Installation

```bash
# Clone or navigate to the project directory
cd C:\Users\ADMIN\.gemini\antigravity-ide\scratch\python_ai_agent

# Install dependencies using uv
& "C:\Users\ADMIN\.local\bin\uv.exe" pip install -r requirements.txt
```

### 3. Running the Agent

#### Interactive CLI Mode (Mock / Offline Mode)

```bash
.venv\Scripts\python main.py --mock
```

#### Interactive CLI Mode (Live Gemini API Mode)

Set your Gemini API Key and run:

```bash
$env:GEMINI_API_KEY="your-api-key-here"
.venv\Scripts\python main.py
```

#### Single Query Execution Mode

```bash
.venv\Scripts\python main.py --query "Calculate sqrt(144) + 2**10" --mock
```

---

## 🧪 Running Unit Tests

Run the complete test suite using `pytest`:

```bash
.venv\Scripts\pytest -v
```

---

## 📁 Project Architecture

```
python_ai_agent/
├── agent/
│   ├── __init__.py
│   ├── core.py           # Core ReAct loop engine
│   ├── llm_provider.py   # Gemini & Mock LLM providers
│   ├── memory.py         # Short-term history & Long-term storage
│   └── tools/            # Tool definitions
│       ├── base.py       # BaseTool & ToolRegistry
│       ├── calculator.py # Safe math evaluator
│       ├── code_runner.py# Python interpreter
│       ├── file_system.py# File I/O tools
│       ├── web_search.py # Web search tool
│       └── system_info.py# System info & datetime tools
├── tests/                # Automated pytest suite
│   ├── test_tools.py
│   ├── test_memory.py
│   └── test_agent.py
├── cli.py                # Rich terminal UI
├── main.py               # Main CLI entry point
├── requirements.txt
└── README.md
```

---

## 🛠️ Adding Custom Tools

You can register custom tools using the `@tool` decorator or subclassing `BaseTool`:

```python
from agent.tools.base import BaseTool, ToolResult

class CustomWeatherTool(BaseTool):
    name = "get_weather"
    description = "Gets current weather for a city."
    parameters_schema = {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "City name"}
        },
        "required": ["city"]
    }

    def run(self, city: str = "", **kwargs) -> ToolResult:
        return ToolResult(success=True, output=f"Weather in {city}: Sunny, 24°C")
```
