import pytest
from assistant_backends import (
    _extract_system,
    _strip_system,
    _to_ollama_messages,
    _to_ollama_tools,
)


def test_extract_system_returns_system_content():
    messages = [
        {"role": "system", "content": "You are helpful"},
        {"role": "user", "content": "Hello"},
    ]
    result = _extract_system(messages)
    assert result == "You are helpful"


def test_extract_system_returns_empty_when_no_system():
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
    ]
    result = _extract_system(messages)
    assert result == ""


def test_extract_system_ignores_system_after_first():
    messages = [
        {"role": "system", "content": "First system"},
        {"role": "user", "content": "Hello"},
        {"role": "system", "content": "Second system"},
    ]
    result = _extract_system(messages)
    assert result == "First system"


def test_strip_system_removes_system_messages():
    messages = [
        {"role": "system", "content": "You are helpful"},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
    ]
    result = _strip_system(messages)

    assert len(result) == 2
    assert all(m["role"] != "system" for m in result)
    assert result[0]["role"] == "user"
    assert result[1]["role"] == "assistant"


def test_strip_system_returns_empty_list_when_only_system():
    messages = [{"role": "system", "content": "You are helpful"}]
    result = _strip_system(messages)
    assert result == []


def test_to_ollama_messages_converts_user_messages():
    messages = [
        {"role": "system", "content": "System"},
        {"role": "user", "content": "Hello"},
    ]
    result = _to_ollama_messages(messages)

    user_msgs = [m for m in result if m["role"] == "user"]
    assert len(user_msgs) == 1
    assert user_msgs[0]["content"] == "Hello"


def test_to_ollama_messages_converts_assistant_text():
    messages = [
        {"role": "system", "content": "System"},
        {"role": "assistant", "content": "Hello there"},
    ]
    result = _to_ollama_messages(messages)

    assistant_msgs = [m for m in result if m["role"] == "assistant"]
    assert len(assistant_msgs) == 1
    assert assistant_msgs[0]["content"] == "Hello there"


def test_to_ollama_messages_converts_assistant_tool_calls():
    messages = [
        {"role": "system", "content": "System"},
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Let me help"},
                {
                    "type": "tool_use",
                    "id": "123",
                    "name": "speak",
                    "input": {"text": "hello"},
                },
            ],
        },
    ]
    result = _to_ollama_messages(messages)

    assistant_msgs = [m for m in result if m["role"] == "assistant"]
    assert len(assistant_msgs) == 1

    msg = assistant_msgs[0]
    assert msg["content"] == "Let me help"
    assert "tool_calls" in msg
    assert len(msg["tool_calls"]) == 1
    assert msg["tool_calls"][0]["function"]["name"] == "speak"
    assert msg["tool_calls"][0]["function"]["arguments"] == {"text": "hello"}


def test_to_ollama_messages_converts_tool_results():
    messages = [
        {"role": "system", "content": "System"},
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "123",
                    "content": "Tool output",
                }
            ],
        },
    ]
    result = _to_ollama_messages(messages)

    tool_msgs = [m for m in result if m["role"] == "tool"]
    assert len(tool_msgs) == 1
    assert tool_msgs[0]["content"] == "Tool output"


def test_to_ollama_messages_handles_mixed_content_in_user():
    messages = [
        {"role": "system", "content": "System"},
        {"role": "user", "content": "Hello"},
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "456",
                    "content": "Result",
                }
            ],
        },
    ]
    result = _to_ollama_messages(messages)

    # One user message + one tool message
    user_msgs = [m for m in result if m["role"] == "user"]
    tool_msgs = [m for m in result if m["role"] == "tool"]

    assert len(user_msgs) == 1
    assert len(tool_msgs) == 1


def test_to_ollama_messages_handles_assistant_text_only():
    messages = [
        {
            "role": "assistant",
            "content": [{"type": "text", "text": "Response"}],
        }
    ]
    result = _to_ollama_messages(messages)

    assistant_msgs = [m for m in result if m["role"] == "assistant"]
    assert len(assistant_msgs) == 1
    assert assistant_msgs[0]["content"] == "Response"


def test_to_ollama_messages_handles_assistant_tool_calls_only():
    messages = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "789",
                    "name": "run_shell",
                    "input": {"command": "ls"},
                }
            ],
        }
    ]
    result = _to_ollama_messages(messages)

    assistant_msgs = [m for m in result if m["role"] == "assistant"]
    assert len(assistant_msgs) == 1
    assert assistant_msgs[0]["content"] == ""
    assert len(assistant_msgs[0]["tool_calls"]) == 1


def test_to_ollama_tools_converts_anthropic_format():
    tools = [
        {
            "name": "speak",
            "description": "Speak text aloud",
            "input_schema": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        }
    ]
    result = _to_ollama_tools(tools)

    assert len(result) == 1
    assert result[0]["type"] == "function"
    assert result[0]["function"]["name"] == "speak"
    assert result[0]["function"]["description"] == "Speak text aloud"


def test_to_ollama_tools_preserves_parameters_schema():
    tools = [
        {
            "name": "run_shell",
            "description": "Run a shell command",
            "input_schema": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The command"}
                },
                "required": ["command"],
            },
        }
    ]
    result = _to_ollama_tools(tools)

    schema = result[0]["function"]["parameters"]
    assert schema["type"] == "object"
    assert "command" in schema["properties"]
    assert schema["required"] == ["command"]


def test_to_ollama_tools_handles_multiple_tools():
    tools = [
        {
            "name": "tool1",
            "description": "First tool",
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "tool2",
            "description": "Second tool",
            "input_schema": {"type": "object", "properties": {}},
        },
    ]
    result = _to_ollama_tools(tools)

    assert len(result) == 2
    assert result[0]["function"]["name"] == "tool1"
    assert result[1]["function"]["name"] == "tool2"


def test_to_ollama_tools_handles_empty_tools():
    result = _to_ollama_tools([])
    assert result == []


def test_to_ollama_messages_preserves_multiple_text_blocks():
    messages = [
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "First"},
                {"type": "text", "text": "Second"},
            ],
        }
    ]
    result = _to_ollama_messages(messages)

    assistant_msgs = [m for m in result if m["role"] == "assistant"]
    assert "First" in assistant_msgs[0]["content"]
    assert "Second" in assistant_msgs[0]["content"]


def test_to_ollama_messages_handles_tool_role():
    messages = [
        {
            "role": "tool",
            "content": "Tool executed successfully",
        }
    ]
    result = _to_ollama_messages(messages)

    tool_msgs = [m for m in result if m["role"] == "tool"]
    assert len(tool_msgs) == 1
    assert tool_msgs[0]["content"] == "Tool executed successfully"


def test_to_ollama_messages_handles_tool_role_with_json_content():
    messages = [
        {
            "role": "tool",
            "content": {"status": "success"},
        }
    ]
    result = _to_ollama_messages(messages)

    tool_msgs = [m for m in result if m["role"] == "tool"]
    assert len(tool_msgs) == 1
    # JSON content should be stringified
    import json

    assert json.loads(tool_msgs[0]["content"]) == {"status": "success"}
