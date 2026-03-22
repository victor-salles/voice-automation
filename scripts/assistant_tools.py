#!/usr/bin/env python3
"""Tool definitions, discovery, and execution for the voice assistant.

Tools are organized into a catalog. The model starts with only a
discover_tools meta-tool, then selects the tools it needs per task.
This keeps the context small and scales as we add more tools.

Safety tiers control which tools need user confirmation:
- SAFE: auto-approved (speak, search_web, open_app, discover/select)
- ASK: requires user confirmation (run_shell)
"""
from __future__ import annotations

import subprocess
import urllib.error
import urllib.request

CONTROL_URL = "http://localhost:18880"


# ── Safety tiers ──

SAFE_TOOLS = {"speak", "search_web", "open_app", "discover_tools", "select_tools"}
ASK_TOOLS = {"run_shell"}


def requires_confirmation(tool_name: str) -> bool:
    """Return True if this tool needs user approval before execution."""
    return tool_name in ASK_TOOLS


# ── Tool catalog ──
# Each entry: (name, one-line summary, full definition dict)

TOOL_CATALOG = {
    "open_app": {
        "summary": "Open a macOS application by name",
        "definition": {
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
    },
    "search_web": {
        "summary": "Search the web via the default browser",
        "definition": {
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
    },
    "run_shell": {
        "summary": "Run a shell command and return output (requires confirmation)",
        "definition": {
            "name": "run_shell",
            "description": (
                "Run a shell command and return its output. "
                "Use for system info, file operations, date/time, calculations, etc. "
                "Commands run in a non-interactive shell with a 10-second timeout. "
                "This tool requires user confirmation before execution."
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
    },
    "speak": {
        "summary": "Speak text aloud to the user via TTS",
        "definition": {
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
    },
}


# ── Meta-tools: discover and select ──

DISCOVER_TOOL = {
    "name": "discover_tools",
    "description": (
        "List all available tools with their names and short descriptions. "
        "Call this first to see what tools you can use, then call select_tools "
        "to load the ones you need for the current task."
    ),
    "input_schema": {
        "type": "object",
        "properties": {},
    },
}

SELECT_TOOL = {
    "name": "select_tools",
    "description": (
        "Load specific tools by name so you can use them. "
        "Call discover_tools first to see what's available, then select "
        "the tools you need. You can select multiple tools at once."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "tool_names": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of tool names to load, e.g. ['open_app', 'speak']",
            },
        },
        "required": ["tool_names"],
    },
}


# ── Active tool tracking ──

class ToolSession:
    """Tracks which tools are active for the current session.

    Starts with only discover_tools and select_tools.
    The model discovers and selects tools as needed.
    """

    def __init__(self, preload: bool = True):
        self._selected: set[str] = set()
        if preload:
            self._selected = set(TOOL_CATALOG.keys())

    @property
    def active_tools(self) -> list[dict]:
        """Return tool definitions for all currently active tools."""
        tools = [DISCOVER_TOOL, SELECT_TOOL]
        for name in self._selected:
            entry = TOOL_CATALOG.get(name)
            if entry:
                tools.append(entry["definition"])
        return tools

    def discover(self) -> str:
        """Return a formatted list of all available tools."""
        lines = []
        for name, entry in TOOL_CATALOG.items():
            safety = "auto-approved" if name in SAFE_TOOLS else "requires confirmation"
            lines.append(f"- {name}: {entry['summary']} ({safety})")
        return "Available tools:\n" + "\n".join(lines)

    def select(self, tool_names: list[str]) -> str:
        """Activate tools by name. Returns confirmation."""
        added = []
        unknown = []
        for name in tool_names:
            if name in TOOL_CATALOG:
                self._selected.add(name)
                added.append(name)
            else:
                unknown.append(name)

        parts = []
        if added:
            parts.append(f"Loaded: {', '.join(added)}")
        if unknown:
            parts.append(f"Unknown: {', '.join(unknown)}")
        return ". ".join(parts)


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
    result = subprocess.run(
        ["open", "-a", app_name],
        capture_output=True, text=True, timeout=5,
    )
    if result.returncode == 0:
        return f"Opened {app_name}"
    return f"Failed to open {app_name}: {result.stderr.strip()}"


def execute_search_web(query: str) -> str:
    encoded = urllib.request.quote(query)
    url = f"https://www.google.com/search?q={encoded}"
    subprocess.run(["open", url], capture_output=True, timeout=5)
    return f"Searching for: {query}"


def execute_run_shell(command: str) -> str:
    try:
        result = subprocess.run(
            command, shell=True,
            capture_output=True, text=True, timeout=10,
        )
        output = result.stdout.strip()
        if result.returncode != 0 and result.stderr.strip():
            output += f"\nError: {result.stderr.strip()}"
        return output or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: command timed out after 10 seconds"


def execute_speak(text: str) -> str:
    return _post_control("/speak", text)


# ── Dispatcher ──

EXECUTORS = {
    "open_app": lambda args: execute_open_app(args["app_name"]),
    "search_web": lambda args: execute_search_web(args["query"]),
    "run_shell": lambda args: execute_run_shell(args["command"]),
    "speak": lambda args: execute_speak(args["text"]),
}


def execute_tool(name: str, arguments: dict, tool_session: ToolSession) -> str:
    """Execute a tool by name. Handles meta-tools and regular tools."""
    if name == "discover_tools":
        return tool_session.discover()
    if name == "select_tools":
        return tool_session.select(arguments.get("tool_names", []))

    executor = EXECUTORS.get(name)
    if not executor:
        return f"Error: tool '{name}' not loaded. Call select_tools first."
    try:
        return executor(arguments)
    except Exception as e:
        return f"Error executing {name}: {e}"


def describe_tool_call(name: str, arguments: dict) -> str:
    """Human-readable description of a tool call, for confirmation prompts."""
    if name == "open_app":
        return f"Open {arguments.get('app_name', '?')}"
    if name == "search_web":
        return f"Search: {arguments.get('query', '?')}"
    if name == "run_shell":
        cmd = arguments.get("command", "?")
        short = cmd[:60] + "..." if len(cmd) > 60 else cmd
        return f"Run: {short}"
    if name == "speak":
        text = arguments.get("text", "?")
        short = text[:60] + "..." if len(text) > 60 else text
        return f"Speak: {short}"
    if name == "discover_tools":
        return "Discover available tools"
    if name == "select_tools":
        names = arguments.get("tool_names", [])
        return f"Load tools: {', '.join(names)}"
    return f"{name}({arguments})"
