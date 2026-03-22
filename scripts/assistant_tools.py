#!/usr/bin/env python3
"""Tool definitions and execution for the voice assistant.

Each tool is a dict with name, description, and parameters (Anthropic format).
Execution routes through Hammerspoon HTTP or local commands.
"""
import json
import subprocess
import urllib.request
import urllib.error

CONTROL_URL = "http://localhost:18880"


# ── Tool definitions (Anthropic tool_use format) ──

TOOLS = [
    {
        "name": "open_app",
        "description": "Open a macOS application by name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "Application name, e.g. 'Safari', 'Terminal', 'Finder'",
                },
            },
            "required": ["app_name"],
        },
    },
    {
        "name": "search_web",
        "description": "Search the web. Opens the default browser with a Google search.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "run_shell",
        "description": (
            "Run a shell command and return its output. "
            "Use for system info, file listings, date/time, calculations, etc. "
            "Commands run in a non-interactive shell with a 10-second timeout."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute",
                },
            },
            "required": ["command"],
        },
    },
    {
        "name": "speak",
        "description": (
            "Speak text aloud to the user via text-to-speech. "
            "Use this to deliver responses, ask questions, or confirm actions. "
            "Keep messages brief and conversational."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to speak aloud",
                },
            },
            "required": ["text"],
        },
    },
]


# ── Tool execution ──

def _post_control(path: str, body: str = "") -> str:
    """POST to the Hammerspoon control server."""
    req = urllib.request.Request(
        f"{CONTROL_URL}{path}",
        data=body.encode("utf-8"),
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.URLError as e:
        return f"Error: control server unreachable ({e})"


def execute_open_app(app_name: str) -> str:
    """Open a macOS app using the 'open' command."""
    result = subprocess.run(
        ["open", "-a", app_name],
        capture_output=True,
        text=True,
        timeout=5,
    )
    if result.returncode == 0:
        return f"Opened {app_name}"
    return f"Failed to open {app_name}: {result.stderr.strip()}"


def execute_search_web(query: str) -> str:
    """Open a web search in the default browser."""
    encoded = urllib.request.quote(query)
    url = f"https://www.google.com/search?q={encoded}"
    subprocess.run(["open", url], capture_output=True, timeout=5)
    return f"Searching for: {query}"


def execute_run_shell(command: str) -> str:
    """Run a shell command with a timeout."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = result.stdout.strip()
        if result.returncode != 0 and result.stderr.strip():
            output += f"\nError: {result.stderr.strip()}"
        return output or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: command timed out after 10 seconds"


def execute_speak(text: str) -> str:
    """Speak text via the Kokoro TTS control server."""
    return _post_control("/speak", text)


# ── Dispatcher ──

EXECUTORS = {
    "open_app": lambda args: execute_open_app(args["app_name"]),
    "search_web": lambda args: execute_search_web(args["query"]),
    "run_shell": lambda args: execute_run_shell(args["command"]),
    "speak": lambda args: execute_speak(args["text"]),
}


def execute_tool(name: str, arguments: dict) -> str:
    """Execute a tool by name with the given arguments."""
    executor = EXECUTORS.get(name)
    if not executor:
        return f"Error: unknown tool '{name}'"
    try:
        return executor(arguments)
    except Exception as e:
        return f"Error executing {name}: {e}"


def describe_tool_call(name: str, arguments: dict) -> str:
    """Human-readable description of a tool call, for confirmation prompts."""
    if name == "open_app":
        return f"Open {arguments.get('app_name', '?')}"
    if name == "search_web":
        return f"Search the web for: {arguments.get('query', '?')}"
    if name == "run_shell":
        cmd = arguments.get("command", "?")
        short = cmd[:60] + "..." if len(cmd) > 60 else cmd
        return f"Run shell command: {short}"
    if name == "speak":
        text = arguments.get("text", "?")
        short = text[:60] + "..." if len(text) > 60 else text
        return f"Speak: {short}"
    return f"Execute {name} with {arguments}"
