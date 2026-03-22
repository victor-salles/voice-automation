import pytest
import json
from pathlib import Path
from assistant_memory import Memory, MAX_TURNS


def test_memory_starts_with_system_message():
    memory = Memory("You are helpful", persist=False)
    messages = memory.messages

    assert len(messages) == 1
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "You are helpful"


def test_add_user_appends_user_message():
    memory = Memory("System", persist=False)
    memory.add_user("Hello")

    messages = memory.messages
    assert len(messages) == 2
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "Hello"


def test_add_assistant_text_appends_assistant_message():
    memory = Memory("System", persist=False)
    memory.add_assistant_text("Hi there")

    messages = memory.messages
    assert len(messages) == 2
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Hi there"


def test_add_assistant_tool_calls_stores_content_blocks():
    memory = Memory("System", persist=False)
    content_blocks = [
        {"type": "text", "text": "Let me help"},
        {"type": "tool_use", "id": "123", "name": "speak", "input": {"text": "hi"}},
    ]
    memory.add_assistant_tool_calls(content_blocks)

    messages = memory.messages
    assert len(messages) == 2
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == content_blocks


def test_add_tool_result_appends_tool_result():
    memory = Memory("System", persist=False)
    memory.add_tool_result("tool_123", "Tool output")

    messages = memory.messages
    assert len(messages) == 2
    assert messages[1]["role"] == "user"
    assert isinstance(messages[1]["content"], list)
    assert len(messages[1]["content"]) == 1
    assert messages[1]["content"][0]["type"] == "tool_result"
    assert messages[1]["content"][0]["tool_use_id"] == "tool_123"
    assert messages[1]["content"][0]["content"] == "Tool output"


def test_clear_keeps_only_system_message():
    memory = Memory("System", persist=False)
    memory.add_user("Message 1")
    memory.add_assistant_text("Response 1")
    memory.add_user("Message 2")

    assert len(memory.messages) == 4

    memory.clear()

    messages = memory.messages
    assert len(messages) == 1
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "System"


def test_messages_returns_copy_not_reference():
    memory = Memory("System", persist=False)
    memory.add_user("Test")

    messages1 = memory.messages
    messages2 = memory.messages

    assert messages1 is not messages2
    messages1.append({"role": "user", "content": "Modified"})
    assert len(memory.messages) == 2


def test_trim_keeps_messages_within_max_turns():
    memory = Memory("System", persist=False)

    # Add messages exceeding MAX_TURNS * 2
    for i in range(MAX_TURNS * 2 + 10):
        memory.add_user(f"Message {i}")

    messages = memory.messages
    # System message + at most MAX_TURNS * 2 non-system messages
    assert len(messages) <= MAX_TURNS * 2 + 1


def test_memory_with_persistence_saves_to_file(tmp_path, monkeypatch):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()

    # Monkeypatch the history path
    from assistant_memory import DEFAULT_HISTORY_FILE

    monkeypatch.setattr(
        "assistant_memory.DEFAULT_HISTORY_DIR", memory_dir
    )

    memory = Memory("System prompt", persist=True)
    memory.add_user("Test message")
    memory.add_assistant_text("Response")

    history_file = memory_dir / DEFAULT_HISTORY_FILE
    assert history_file.exists()

    with open(history_file) as f:
        saved = json.load(f)

    assert len(saved) == 3
    assert saved[0]["role"] == "system"
    assert saved[1]["role"] == "user"
    assert saved[2]["role"] == "assistant"


def test_memory_load_restores_previous_conversation(tmp_path, monkeypatch):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()

    from assistant_memory import DEFAULT_HISTORY_FILE

    monkeypatch.setattr(
        "assistant_memory.DEFAULT_HISTORY_DIR", memory_dir
    )

    # Create initial memory and save
    memory1 = Memory("System prompt", persist=True)
    memory1.add_user("Message 1")
    memory1.add_assistant_text("Response 1")

    # Create new memory and load
    memory2 = Memory("Different prompt", persist=True)
    loaded = memory2.load()

    assert loaded is True
    messages = memory2.messages
    assert len(messages) == 3
    assert messages[0]["content"] == "System prompt"
    assert messages[1]["content"] == "Message 1"


def test_memory_load_returns_false_when_no_file_exists(tmp_path, monkeypatch):
    memory_dir = tmp_path / "empty"
    memory_dir.mkdir()

    from assistant_memory import DEFAULT_HISTORY_FILE

    monkeypatch.setattr(
        "assistant_memory.DEFAULT_HISTORY_DIR", memory_dir
    )

    memory = Memory("System", persist=True)
    loaded = memory.load()

    assert loaded is False


def test_memory_load_returns_false_on_corrupted_json(tmp_path, monkeypatch):
    memory_dir = tmp_path / "corrupted"
    memory_dir.mkdir()

    from assistant_memory import DEFAULT_HISTORY_FILE

    monkeypatch.setattr(
        "assistant_memory.DEFAULT_HISTORY_DIR", memory_dir
    )

    # Write corrupted JSON
    history_file = memory_dir / DEFAULT_HISTORY_FILE
    history_file.write_text("{ invalid json }")

    memory = Memory("System", persist=True)
    loaded = memory.load()

    assert loaded is False


def test_memory_persistence_disabled_no_save(tmp_path, monkeypatch):
    memory_dir = tmp_path / "no_persist"
    memory_dir.mkdir()

    from assistant_memory import DEFAULT_HISTORY_FILE

    monkeypatch.setattr(
        "assistant_memory.DEFAULT_HISTORY_DIR", memory_dir
    )

    memory = Memory("System", persist=False)
    memory.add_user("Message")

    history_file = memory_dir / DEFAULT_HISTORY_FILE
    assert not history_file.exists()
