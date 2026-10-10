import pytest
from agent.memory import ConversationMemory, PersistentLongTermMemory


def test_conversation_memory():
    mem = ConversationMemory()
    mem.add_user_message("What is 10 + 20?")
    mem.add_assistant_message("Let me calculate that.")
    mem.add_tool_message("calculator", "30")

    msgs = mem.get_messages()
    assert len(msgs) == 3
    assert msgs[0].role == "user"
    assert msgs[1].role == "assistant"
    assert msgs[2].role == "tool"

    history_str = mem.get_formatted_history()
    assert "User: What is 10 + 20?" in history_str
    assert "Tool [calculator] Result:\n30" in history_str

    mem.clear()
    assert len(mem.get_messages()) == 0


def test_persistent_long_term_memory(tmp_path):
    mem_file = tmp_path / "test_memory.json"
    memory = PersistentLongTermMemory(memory_filepath=str(mem_file))

    memory.set("user_name", "Alex")
    memory.set("preferences", {"theme": "dark"})

    assert memory.get("user_name") == "Alex"

    # Reload memory from disk
    new_memory_instance = PersistentLongTermMemory(memory_filepath=str(mem_file))
    assert new_memory_instance.get("user_name") == "Alex"
    assert new_memory_instance.get("preferences")["theme"] == "dark"

    # Delete key
    assert new_memory_instance.delete("user_name") is True
    assert new_memory_instance.get("user_name") is None
