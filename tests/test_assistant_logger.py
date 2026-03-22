import pytest
import json
import os
from pathlib import Path
from datetime import datetime
from assistant_logger import SessionLogger


def test_logger_creates_session_file(tmp_path, monkeypatch):
    monkeypatch.setenv("VOICE_AGENT_LOG_DIR", str(tmp_path))

    # Reload module to pick up env var
    import importlib
    import assistant_logger

    importlib.reload(assistant_logger)
    logger = assistant_logger.SessionLogger("test_backend", "test_model")

    assert logger.path.exists()
    assert logger.path.suffix == ".jsonl"
    assert "session_" in logger.path.name


def test_logger_writes_session_start_event(tmp_path, monkeypatch):
    monkeypatch.setenv("VOICE_AGENT_LOG_DIR", str(tmp_path))

    import importlib
    import assistant_logger

    importlib.reload(assistant_logger)
    logger = assistant_logger.SessionLogger("claude_backend", "claude-3")

    lines = logger.path.read_text().strip().split("\n")
    assert len(lines) >= 1

    first_event = json.loads(lines[0])
    assert first_event["event"] == "session_start"
    assert first_event["data"]["backend"] == "claude_backend"
    assert first_event["data"]["model"] == "claude-3"
    assert "timestamp" in first_event


def test_log_user_input_writes_event(tmp_path, monkeypatch):
    monkeypatch.setenv("VOICE_AGENT_LOG_DIR", str(tmp_path))

    import importlib
    import assistant_logger

    importlib.reload(assistant_logger)
    logger = assistant_logger.SessionLogger("backend", "model")
    logger.log_user_input("Hello assistant")

    lines = logger.path.read_text().strip().split("\n")
    user_event = json.loads(lines[-1])

    assert user_event["event"] == "user_input"
    assert user_event["data"]["text"] == "Hello assistant"
    assert "timestamp" in user_event


def test_log_llm_request_returns_start_time(tmp_path, monkeypatch):
    monkeypatch.setenv("VOICE_AGENT_LOG_DIR", str(tmp_path))

    import importlib
    import assistant_logger

    importlib.reload(assistant_logger)
    logger = assistant_logger.SessionLogger("backend", "model")
    start_time = logger.log_llm_request(5, 3)

    assert isinstance(start_time, float)
    assert start_time > 0

    lines = logger.path.read_text().strip().split("\n")
    llm_event = json.loads(lines[-1])

    assert llm_event["event"] == "llm_request"
    assert llm_event["data"]["message_count"] == 5
    assert llm_event["data"]["tool_count"] == 3


def test_log_llm_response_includes_duration_ms(tmp_path, monkeypatch):
    monkeypatch.setenv("VOICE_AGENT_LOG_DIR", str(tmp_path))

    import importlib
    import assistant_logger

    importlib.reload(assistant_logger)
    logger = assistant_logger.SessionLogger("backend", "model")

    import time

    start = logger.log_llm_request(1, 0)
    time.sleep(0.01)  # Sleep for 10ms
    logger.log_llm_response(
        start, "Response text", [{"name": "tool1", "arguments": {}}], "tool_use"
    )

    lines = logger.path.read_text().strip().split("\n")
    response_event = json.loads(lines[-1])

    assert response_event["event"] == "llm_response"
    assert "duration_ms" in response_event
    assert response_event["duration_ms"] >= 10
    assert response_event["data"]["text_length"] == len("Response text")
    assert response_event["data"]["text_preview"] == "Response text"
    assert len(response_event["data"]["tool_calls"]) == 1
    assert response_event["data"]["stop_reason"] == "tool_use"


def test_log_llm_response_truncates_long_text(tmp_path, monkeypatch):
    monkeypatch.setenv("VOICE_AGENT_LOG_DIR", str(tmp_path))

    import importlib
    import assistant_logger

    importlib.reload(assistant_logger)
    logger = assistant_logger.SessionLogger("backend", "model")

    long_text = "a" * 500
    start = logger.log_llm_request(1, 0)
    logger.log_llm_response(start, long_text, [], "end_turn")

    lines = logger.path.read_text().strip().split("\n")
    response_event = json.loads(lines[-1])

    assert response_event["data"]["text_length"] == 500
    preview = response_event["data"]["text_preview"]
    assert preview.endswith("...")
    assert len(preview) <= 203


def test_log_tool_execution_records_approval_status(tmp_path, monkeypatch):
    monkeypatch.setenv("VOICE_AGENT_LOG_DIR", str(tmp_path))

    import importlib
    import assistant_logger

    importlib.reload(assistant_logger)
    logger = assistant_logger.SessionLogger("backend", "model")
    logger.log_tool_execution("speak", {"text": "hello"}, "result", True, 100)

    lines = logger.path.read_text().strip().split("\n")
    tool_event = json.loads(lines[-1])

    assert tool_event["event"] == "tool_exec"
    assert tool_event["data"]["tool"] == "speak"
    assert tool_event["data"]["approved"] is True
    assert tool_event["data"]["arguments"] == {"text": "hello"}
    assert tool_event["duration_ms"] == 100


def test_log_tool_execution_truncates_long_result(tmp_path, monkeypatch):
    monkeypatch.setenv("VOICE_AGENT_LOG_DIR", str(tmp_path))

    import importlib
    import assistant_logger

    importlib.reload(assistant_logger)
    logger = assistant_logger.SessionLogger("backend", "model")

    long_result = "x" * 500
    logger.log_tool_execution("run_shell", {}, long_result, False, 50)

    lines = logger.path.read_text().strip().split("\n")
    tool_event = json.loads(lines[-1])

    assert tool_event["data"]["result_length"] == 500
    preview = tool_event["data"]["result_preview"]
    assert preview.endswith("...")
    assert len(preview) <= 303


def test_log_error_records_error_and_context(tmp_path, monkeypatch):
    monkeypatch.setenv("VOICE_AGENT_LOG_DIR", str(tmp_path))

    import importlib
    import assistant_logger

    importlib.reload(assistant_logger)
    logger = assistant_logger.SessionLogger("backend", "model")
    logger.log_error("Network error", "During tool execution")

    lines = logger.path.read_text().strip().split("\n")
    error_event = json.loads(lines[-1])

    assert error_event["event"] == "error"
    assert error_event["data"]["error"] == "Network error"
    assert error_event["data"]["context"] == "During tool execution"


def test_log_session_end_records_total_duration(tmp_path, monkeypatch):
    monkeypatch.setenv("VOICE_AGENT_LOG_DIR", str(tmp_path))

    import importlib
    import assistant_logger

    importlib.reload(assistant_logger)
    logger = assistant_logger.SessionLogger("backend", "model")

    import time

    time.sleep(0.01)  # Sleep for 10ms
    logger.log_session_end()

    lines = logger.path.read_text().strip().split("\n")
    end_event = json.loads(lines[-1])

    assert end_event["event"] == "session_end"
    assert "total_duration_ms" in end_event["data"]
    assert end_event["data"]["total_duration_ms"] >= 10


def test_log_entries_are_valid_jsonl(tmp_path, monkeypatch):
    monkeypatch.setenv("VOICE_AGENT_LOG_DIR", str(tmp_path))

    import importlib
    import assistant_logger

    importlib.reload(assistant_logger)
    logger = assistant_logger.SessionLogger("backend", "model")
    logger.log_user_input("Test")
    logger.log_error("Test error")

    lines = logger.path.read_text().strip().split("\n")

    for line in lines:
        entry = json.loads(line)
        assert "timestamp" in entry
        assert "event" in entry
        assert "data" in entry


def test_logger_handles_directory_creation_failure(tmp_path, monkeypatch):
    # Create a read-only parent to cause mkdir failure
    read_only = tmp_path / "readonly"
    read_only.mkdir()
    read_only.chmod(0o444)

    monkeypatch.setenv("VOICE_AGENT_LOG_DIR", str(read_only / "logs"))

    import importlib
    import assistant_logger

    importlib.reload(assistant_logger)

    # Should not raise, just silently fail
    try:
        logger = assistant_logger.SessionLogger("backend", "model")
    except Exception:
        pass

    read_only.chmod(0o755)  # Restore permissions for cleanup
