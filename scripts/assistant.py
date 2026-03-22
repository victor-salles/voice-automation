#!/usr/bin/env python3
"""Voice assistant orchestrator.

Thin agent loop: user input → LLM → tool execution → response.
The model starts with discover_tools + select_tools only, then
loads additional tools as needed. Safe tools auto-execute;
dangerous tools (run_shell) require confirmation.

Usage:
    python3 assistant.py                    # Ollama backend (default)
    python3 assistant.py --backend claude   # Claude API backend
    python3 assistant.py --model qwen3:8b   # Override model
    python3 assistant.py --new              # Start fresh conversation

Session logs: ~/.config/voice-automation/logs/
"""
from __future__ import annotations

import argparse
import platform
import sys
import time
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SYSTEM_PROMPT_PATH = SCRIPT_DIR.parent / "config" / "assistant" / "system_prompt.txt"


def load_system_prompt() -> str:
    """Load and interpolate the system prompt with runtime context."""
    if SYSTEM_PROMPT_PATH.exists():
        template = SYSTEM_PROMPT_PATH.read_text().strip()
    else:
        template = "You are a helpful macOS voice assistant. Today is {date}."

    return template.format(
        date=datetime.now().strftime("%A, %B %d, %Y"),
        hostname=platform.node() or "this Mac",
    )


def create_backend(name: str, model: str | None = None):
    from assistant_backends import ClaudeBackend, OllamaBackend

    if name == "claude":
        kwargs = {"model": model} if model else {}
        return ClaudeBackend(**kwargs)
    elif name == "ollama":
        kwargs = {"model": model} if model else {}
        return OllamaBackend(**kwargs)
    else:
        print(f"Unknown backend: {name}", file=sys.stderr)
        sys.exit(1)


def confirm_tool_call(description: str) -> bool:
    """Ask user to confirm a dangerous tool execution."""
    print(f"\n  ⚠ {description}")
    try:
        response = input("  Execute? [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    return response in ("y", "yes")


def run_agent_loop(backend, memory, logger) -> None:
    """Main agent loop: get input, call LLM, execute tools, repeat."""
    from assistant_tools import (
        ToolSession, execute_tool, describe_tool_call, requires_confirmation,
    )

    tool_session = ToolSession()

    print(f"\nVoice Assistant ({backend.name()})")
    print(f"Session log: {logger.path}")
    print("Type a message, 'clear' to reset, or 'quit' to exit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            logger.log_session_end()
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Bye.")
            logger.log_session_end()
            break
        if user_input.lower() == "clear":
            memory.clear()
            print("Conversation cleared.\n")
            continue

        memory.add_user(user_input)
        logger.log_user_input(user_input)

        while True:
            active_tools = tool_session.active_tools
            llm_start = logger.log_llm_request(
                message_count=len(memory.messages),
                tool_count=len(active_tools),
            )

            try:
                response = backend.chat(memory.messages, active_tools)
            except ConnectionError as e:
                print(f"\nError: {e}\n")
                logger.log_error(str(e), context="llm_request")
                break

            logger.log_llm_response(
                start_time=llm_start,
                text=response["text"],
                tool_calls=response["tool_calls"],
                stop_reason=response["stop_reason"],
            )

            if response["tool_calls"]:
                content_blocks = []
                if response["text"]:
                    content_blocks.append({
                        "type": "text",
                        "text": response["text"],
                    })
                for tc in response["tool_calls"]:
                    content_blocks.append({
                        "type": "tool_use",
                        "id": tc["id"],
                        "name": tc["name"],
                        "input": tc["arguments"],
                    })
                memory.add_assistant_tool_calls(content_blocks)

                for tc in response["tool_calls"]:
                    description = describe_tool_call(tc["name"], tc["arguments"])
                    needs_confirm = requires_confirmation(tc["name"])

                    if needs_confirm:
                        approved = confirm_tool_call(description)
                    else:
                        approved = True

                    tool_start = time.monotonic()
                    if approved:
                        result = execute_tool(
                            tc["name"], tc["arguments"], tool_session
                        )
                        # Show non-silent tool executions
                        if tc["name"] not in ("speak", "discover_tools", "select_tools"):
                            print(f"  ✓ {description}")
                        elif tc["name"] == "select_tools":
                            print(f"  ✓ {result}")
                    else:
                        result = "User denied this action."
                        print(f"  ✗ {description} (denied)")

                    tool_duration = int((time.monotonic() - tool_start) * 1000)

                    logger.log_tool_execution(
                        name=tc["name"],
                        arguments=tc["arguments"],
                        result=result,
                        approved=approved,
                        duration_ms=tool_duration,
                    )

                    memory.add_tool_result(tc["id"], result)

                continue

            else:
                if response["text"]:
                    print(f"\nAssistant: {response['text']}\n")
                    memory.add_assistant_text(response["text"])
                break


def main():
    parser = argparse.ArgumentParser(description="Voice Assistant")
    parser.add_argument(
        "--backend",
        choices=["claude", "ollama"],
        default="ollama",
        help="LLM backend (default: ollama)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Override model name (e.g. qwen2.5:14b, claude-sonnet-4-20250514)",
    )
    parser.add_argument(
        "--new",
        action="store_true",
        help="Start a fresh conversation (ignore saved history)",
    )
    args = parser.parse_args()

    sys.path.insert(0, str(SCRIPT_DIR))

    from assistant_logger import SessionLogger
    from assistant_memory import Memory

    system_prompt = load_system_prompt()
    memory = Memory(system_prompt)

    if not args.new:
        if memory.load():
            print("(Resumed previous conversation. Use 'clear' to reset.)")

    try:
        backend = create_backend(args.backend, model=args.model)
    except (ImportError, ConnectionError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    logger = SessionLogger(
        backend_name=backend.name(),
        model=backend._model,
    )

    run_agent_loop(backend, memory, logger)


if __name__ == "__main__":
    main()
