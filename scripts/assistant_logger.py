#!/usr/bin/env python3
"""Session logger for the voice assistant.

Writes structured JSON logs to ~/.config/voice-automation/logs/.
One file per session, named by timestamp.

Log format per entry:
{
    "timestamp": "2026-03-22T19:30:00",
    "event": "user_input" | "llm_request" | "llm_response" | "tool_exec" | "error",
    "data": { ... event-specific data ... },
    "duration_ms": 1234  (optional, for timed events)
}
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path


LOG_DIR = Path(
    os.environ.get(
        "VOICE_AGENT_LOG_DIR",
        str(Path.home() / ".config" / "voice-automation" / "logs"),
    )
)


class SessionLogger:
    """Append-only JSON-lines logger for a single assistant session."""

    def __init__(self, backend_name: str, model: str):
        try:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._path = LOG_DIR / f"session_{timestamp}.jsonl"
        self._start = time.monotonic()
        self._write({
            "event": "session_start",
            "data": {"backend": backend_name, "model": model},
        })

    @property
    def path(self) -> Path:
        return self._path

    def log_user_input(self, text: str) -> None:
        self._write({"event": "user_input", "data": {"text": text}})

    def log_llm_request(self, message_count: int, tool_count: int) -> float:
        """Log that we're about to call the LLM. Returns start time."""
        self._write({
            "event": "llm_request",
            "data": {
                "message_count": message_count,
                "tool_count": tool_count,
            },
        })
        return time.monotonic()

    def log_llm_response(
        self,
        start_time: float,
        text: str | None,
        tool_calls: list,
        stop_reason: str,
    ) -> None:
        duration_ms = int((time.monotonic() - start_time) * 1000)
        self._write({
            "event": "llm_response",
            "data": {
                "text_length": len(text) if text else 0,
                "text_preview": (text[:200] + "...") if text and len(text) > 200 else text,
                "tool_calls": [
                    {"name": tc["name"], "arguments": tc["arguments"]}
                    for tc in tool_calls
                ],
                "stop_reason": stop_reason,
            },
            "duration_ms": duration_ms,
        })

    def log_tool_execution(
        self,
        name: str,
        arguments: dict,
        result: str,
        approved: bool,
        duration_ms: int,
    ) -> None:
        self._write({
            "event": "tool_exec",
            "data": {
                "tool": name,
                "arguments": arguments,
                "approved": approved,
                "result_length": len(result),
                "result_preview": (result[:300] + "...") if len(result) > 300 else result,
            },
            "duration_ms": duration_ms,
        })

    def log_error(self, error: str, context: str = "") -> None:
        self._write({
            "event": "error",
            "data": {"error": error, "context": context},
        })

    def log_session_end(self) -> None:
        total_ms = int((time.monotonic() - self._start) * 1000)
        self._write({
            "event": "session_end",
            "data": {"total_duration_ms": total_ms},
        })

    def _write(self, entry: dict) -> None:
        entry["timestamp"] = datetime.now().isoformat(timespec="seconds")
        try:
            with open(self._path, "a") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError:
            pass
