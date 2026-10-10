import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str  # "system", "user", "assistant", "tool"
    content: str
    name: Optional[str] = None  # Tool name if role is "tool"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationMemory:
    """Manages short-term conversation context for ReAct reasoning turns."""

    def __init__(self, max_history_turns: int = 20):
        self.messages: List[Message] = []
        self.max_history_turns = max_history_turns

    def add_user_message(self, content: str) -> None:
        self.messages.append(Message(role="user", content=content))

    def add_assistant_message(self, content: str) -> None:
        self.messages.append(Message(role="assistant", content=content))

    def add_tool_message(self, name: str, output: str) -> None:
        self.messages.append(Message(role="tool", content=output, name=name))

    def add_system_message(self, content: str) -> None:
        self.messages.append(Message(role="system", content=content))

    def get_messages(self) -> List[Message]:
        return self.messages

    def get_formatted_history(self) -> str:
        """Formats conversation history into readable text for context."""
        formatted = []
        for msg in self.messages:
            if msg.role == "user":
                formatted.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                formatted.append(f"Assistant: {msg.content}")
            elif msg.role == "tool":
                formatted.append(f"Tool [{msg.name}] Result:\n{msg.content}")
        return "\n\n".join(formatted)

    def clear(self) -> None:
        self.messages.clear()


class PersistentLongTermMemory:
    """JSON-backed persistent key-value store for agent memory across restarts."""

    def __init__(self, memory_filepath: str = "agent_memory.json"):
        self.filepath = Path(memory_filepath)
        self._data: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        if self.filepath.exists():
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception:
                self._data = {}
        else:
            self._data = {}

    def save(self) -> None:
        try:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except Exception:
            pass

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        self.save()

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            self.save()
            return True
        return False

    def list_all(self) -> Dict[str, Any]:
        return dict(self._data)
