#!/usr/bin/env python3
"""LLM backend abstraction for the voice assistant.

All backends return a unified response format:
{
    "text": "optional text response",
    "tool_calls": [{"id": "...", "name": "...", "arguments": {...}}],
    "stop_reason": "end_turn" | "tool_use",
}
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class LLMBackend(ABC):
    """Base class for LLM backends."""

    @abstractmethod
    def chat(self, messages: list, tools: list) -> dict:
        """Send messages + tools, return unified response dict."""
        ...

    @abstractmethod
    def name(self) -> str:
        """Human-readable backend name."""
        ...


class ClaudeBackend(LLMBackend):
    """Anthropic Claude API backend."""

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "Install the Anthropic SDK: pip3 install anthropic"
            )
        self._client = anthropic.Anthropic()
        self._model = model

    def name(self) -> str:
        return f"Claude ({self._model.split('-')[1]})"

    def chat(self, messages: list, tools: list) -> dict:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=_extract_system(messages),
            messages=_strip_system(messages),
            tools=tools,
        )

        text_parts = []
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "arguments": block.input,
                })

        return {
            "text": "\n".join(text_parts) if text_parts else None,
            "tool_calls": tool_calls,
            "stop_reason": response.stop_reason,
        }


class OllamaBackend(LLMBackend):
    """Ollama backend via OpenAI-compatible chat API (no external deps).

    Configure via environment variables:
        OLLAMA_MODEL    Model name (default: qwen2.5:7b)
        OLLAMA_BASE_URL API base URL (default: http://localhost:11434/v1)
    """

    def __init__(self, model: str | None = None, base_url: str | None = None):
        import os
        self._model = model or os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
        self._base_url = (
            base_url
            or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        ).rstrip("/")

    def name(self) -> str:
        return f"Ollama ({self._model})"

    def chat(self, messages: list, tools: list) -> dict:
        import json
        import urllib.request

        openai_tools = _to_openai_tools(tools)
        openai_messages = _to_openai_messages(messages)

        body = {
            "model": self._model,
            "messages": openai_messages,
        }
        if openai_tools:
            body["tools"] = openai_tools

        req = urllib.request.Request(
            f"{self._base_url}/chat/completions",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
        except urllib.error.URLError as e:
            raise ConnectionError(
                f"Cannot reach Ollama at {self._base_url} — "
                f"is 'ollama serve' running? ({e})"
            )

        choice = data["choices"][0]
        message = choice["message"]
        text = message.get("content")
        tool_calls = []

        for tc in message.get("tool_calls") or []:
            args = tc["function"]["arguments"]
            if isinstance(args, str):
                args = json.loads(args)
            tool_calls.append({
                "id": tc.get("id", f"call_{len(tool_calls)}"),
                "name": tc["function"]["name"],
                "arguments": args,
            })

        return {
            "text": text,
            "tool_calls": tool_calls,
            "stop_reason": "tool_use" if tool_calls else "end_turn",
        }


# ── Message format converters ──

def _extract_system(messages: list) -> str:
    """Extract system message content for Claude API."""
    for msg in messages:
        if msg.get("role") == "system":
            return msg["content"]
    return ""


def _strip_system(messages: list) -> list:
    """Remove system messages (Claude takes system separately)."""
    return [m for m in messages if m.get("role") != "system"]


def _to_openai_messages(messages: list) -> list:
    """Convert our message format to OpenAI format."""
    result = []
    for msg in messages:
        role = msg["role"]
        content = msg.get("content", "")

        if role == "system":
            result.append({"role": "system", "content": content})
        elif role == "user":
            result.append({"role": "user", "content": content})
        elif role == "assistant":
            if isinstance(content, str):
                result.append({"role": "assistant", "content": content})
            elif isinstance(content, list):
                # Claude-style content blocks → OpenAI format
                text_parts = []
                tool_calls = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            text_parts.append(block["text"])
                        elif block.get("type") == "tool_use":
                            import json
                            tool_calls.append({
                                "id": block["id"],
                                "type": "function",
                                "function": {
                                    "name": block["name"],
                                    "arguments": json.dumps(block["input"]),
                                },
                            })
                msg_out = {"role": "assistant"}
                if text_parts:
                    msg_out["content"] = "\n".join(text_parts)
                if tool_calls:
                    msg_out["tool_calls"] = tool_calls
                result.append(msg_out)
        elif role == "tool":
            result.append({
                "role": "tool",
                "tool_call_id": msg.get("tool_use_id", ""),
                "content": content,
            })
    return result


def _to_openai_tools(tools: list) -> list:
    """Convert Anthropic tool format to OpenAI function format."""
    result = []
    for tool in tools:
        result.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("input_schema", {}),
            },
        })
    return result
