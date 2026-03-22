#!/usr/bin/env python3
"""Conversation memory for the voice assistant.

Manages message history with optional persistence to JSON.
"""
import json
import os
from pathlib import Path

DEFAULT_HISTORY_DIR = Path.home() / ".config" / "voice-automation"
DEFAULT_HISTORY_FILE = "conversation.json"
MAX_TURNS = 50


class Memory:
    """In-memory conversation history with optional JSON persistence."""

    def __init__(self, system_prompt: str, persist: bool = True):
        self._messages: list[dict] = [
            {"role": "system", "content": system_prompt},
        ]
        self._persist = persist
        self._history_path = DEFAULT_HISTORY_DIR / DEFAULT_HISTORY_FILE

    @property
    def messages(self) -> list[dict]:
        return list(self._messages)

    def add_user(self, text: str) -> None:
        self._messages.append({"role": "user", "content": text})
        self._trim()

    def add_assistant_text(self, text: str) -> None:
        self._messages.append({"role": "assistant", "content": text})
        self._save()

    def add_assistant_tool_calls(self, content_blocks: list) -> None:
        """Add assistant message with tool_use blocks (Claude format)."""
        self._messages.append({"role": "assistant", "content": content_blocks})

    def add_tool_result(self, tool_use_id: str, result: str) -> None:
        self._messages.append({
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": result,
                }
            ],
        })

    def clear(self) -> None:
        """Clear conversation history, keeping the system prompt."""
        system = self._messages[0]
        self._messages = [system]
        self._save()

    def _trim(self) -> None:
        """Keep conversation within MAX_TURNS to avoid context overflow."""
        system = self._messages[0]
        non_system = self._messages[1:]
        if len(non_system) > MAX_TURNS * 2:
            self._messages = [system] + non_system[-(MAX_TURNS * 2):]

    def _save(self) -> None:
        if not self._persist:
            return
        try:
            self._history_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._history_path, "w") as f:
                json.dump(self._messages, f, indent=2, ensure_ascii=False)
        except OSError:
            pass

    def load(self) -> bool:
        """Load previous conversation from disk. Returns True if loaded."""
        if not self._persist or not self._history_path.exists():
            return False
        try:
            with open(self._history_path) as f:
                loaded = json.load(f)
            if loaded and loaded[0].get("role") == "system":
                self._messages = loaded
                return True
        except (json.JSONDecodeError, OSError):
            pass
        return False
