import sys
import os
import platform
import datetime
from .base import BaseTool, ToolResult


class SystemInfoTool(BaseTool):
    """Tool to inspect host system environment details."""

    name = "system_info"
    description = "Retrieves information about the local system environment, OS, Python version, working directory, and CPU details."
    parameters_schema = {
        "type": "object",
        "properties": {}
    }

    def run(self, **kwargs) -> ToolResult:
        info = {
            "OS": f"{platform.system()} {platform.release()} ({platform.version()})",
            "Architecture": platform.machine(),
            "Python Version": sys.version.split()[0],
            "Executable Path": sys.executable,
            "Current Directory": os.getcwd(),
            "Process ID": os.getpid(),
        }
        formatted = "\n".join([f"**{k}**: {v}" for k, v in info.items()])
        return ToolResult(success=True, output=f"System Diagnostics:\n{formatted}")


class CurrentDateTimeTool(BaseTool):
    """Tool to get the current date, time, and timestamp."""

    name = "current_date_time"
    description = "Returns the exact current date, time, day of week, and ISO timestamp."
    parameters_schema = {
        "type": "object",
        "properties": {}
    }

    def run(self, **kwargs) -> ToolResult:
        now = datetime.datetime.now()
        dt_str = (
            f"**Local Time**: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"**Day of Week**: {now.strftime('%A')}\n"
            f"**ISO Timestamp**: {now.isoformat()}\n"
            f"**UTC Timestamp**: {datetime.datetime.utcnow().isoformat()}Z"
        )
        return ToolResult(success=True, output=dt_str)
