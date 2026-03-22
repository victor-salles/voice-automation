#!/usr/bin/env python3
"""Voice assistant orchestrator.

Thin agent loop: user input → LLM → tool execution → response.
Runs in terminal for P0 (typed input), voice input added in P1.

Usage:
    python3 assistant.py                    # Claude backend (default)
    python3 assistant.py --backend ollama   # Ollama backend
    python3 assistant.py --no-confirm       # Skip tool confirmations
    python3 assistant.py --new              # Start fresh conversation
"""
import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SYSTEM_PROMPT_PATH = SCRIPT_DIR.parent / "config" / "assistant" / "system_prompt.txt"


def load_system_prompt() -> str:
    if SYSTEM_PROMPT_PATH.exists():
        return SYSTEM_PROMPT_PATH.read_text().strip()
    return "You are a helpful macOS voice assistant."


def create_backend(name: str):
    from assistant_backends import ClaudeBackend, OllamaBackend

    if name == "claude":
        return ClaudeBackend()
    elif name == "ollama":
        return OllamaBackend()
    else:
        print(f"Unknown backend: {name}", file=sys.stderr)
        sys.exit(1)


def confirm_tool_call(description: str, auto_approve: bool) -> bool:
    """Ask user to confirm a tool execution. Returns True if approved."""
    if auto_approve:
        return True

    print(f"\n  → {description}")
    try:
        response = input("  Execute? [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    return response in ("y", "yes")


def run_agent_loop(backend, memory, tools_module, auto_approve: bool) -> None:
    """Main agent loop: get input, call LLM, execute tools, repeat."""
    from assistant_tools import TOOLS, execute_tool, describe_tool_call

    print(f"\nVoice Assistant ({backend.name()})")
    print("Type a message, 'clear' to reset, or 'quit' to exit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Bye.")
            break
        if user_input.lower() == "clear":
            memory.clear()
            print("Conversation cleared.\n")
            continue

        memory.add_user(user_input)

        while True:
            response = backend.chat(memory.messages, TOOLS)

            if response["tool_calls"]:
                # Build content blocks for memory
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

                # Execute each tool call
                for tc in response["tool_calls"]:
                    description = describe_tool_call(tc["name"], tc["arguments"])

                    # Speak tool is always auto-approved
                    is_speak = tc["name"] == "speak"
                    approved = is_speak or confirm_tool_call(
                        description, auto_approve
                    )

                    if approved:
                        result = execute_tool(tc["name"], tc["arguments"])
                        if not is_speak:
                            print(f"  ✓ {description}")
                    else:
                        result = "User denied this action."
                        print(f"  ✗ {description} (denied)")

                    memory.add_tool_result(tc["id"], result)

                # Continue loop — LLM may want to make more tool calls
                continue

            else:
                # Text-only response (no tool calls)
                if response["text"]:
                    print(f"\nAssistant: {response['text']}\n")
                    memory.add_assistant_text(response["text"])
                break


def main():
    parser = argparse.ArgumentParser(description="Voice Assistant")
    parser.add_argument(
        "--backend",
        choices=["claude", "ollama"],
        default="claude",
        help="LLM backend to use (default: claude)",
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip tool execution confirmations",
    )
    parser.add_argument(
        "--new",
        action="store_true",
        help="Start a fresh conversation (ignore saved history)",
    )
    args = parser.parse_args()

    # Add scripts dir to path for imports
    sys.path.insert(0, str(SCRIPT_DIR))

    from assistant_memory import Memory

    system_prompt = load_system_prompt()
    memory = Memory(system_prompt)

    if not args.new:
        if memory.load():
            print("(Resumed previous conversation. Use 'clear' to reset.)")

    try:
        backend = create_backend(args.backend)
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    run_agent_loop(backend, memory, None, auto_approve=args.no_confirm)


if __name__ == "__main__":
    main()
