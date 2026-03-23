#!/usr/bin/env python3
"""Tool executors for the voice assistant.

Each function encapsulates the full logic for a domain action.
The model picks the intent; the executor handles the how.

Design principles:
- Each executor tries the best approach first, falls back if needed
- Returns clean, speakable text — not raw command output
- Never requires the model to know macOS-specific CLI commands
"""
from __future__ import annotations

import json
import re
import subprocess
import urllib.error
import urllib.request

CONTROL_URL = "http://localhost:18880"


# ── Helpers ──

def _run(command: str, timeout: int = 10) -> tuple[str, bool]:
    """Run a shell command. Returns (output, success)."""
    try:
        result = subprocess.run(
            command, shell=True,
            capture_output=True, text=True, timeout=timeout,
        )
        output = result.stdout.strip()
        if result.returncode != 0:
            error = result.stderr.strip()
            return error or "(command failed)", False
        return output or "(no output)", True
    except subprocess.TimeoutExpired:
        return "Command timed out", False
    except Exception as e:
        return str(e), False


def _osascript(script: str) -> tuple[str, bool]:
    """Run an AppleScript snippet. Returns (output, success)."""
    return _run(f"osascript -e '{script}'")


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


# ── Domain executors ──

def execute_get_weather(city: str = "auto") -> str:
    """Get current weather. Auto-detects location from IP if city is 'auto'."""
    location = "" if city == "auto" else city
    output, ok = _run(f'curl -s "wttr.in/{location}?format=%l:+%C+%t+%h+%w"', timeout=5)
    if ok and output and "Unknown" not in output:
        return f"Weather for {output}"

    # Fallback: try with just temperature
    output, ok = _run(f'curl -s "wttr.in/{location}?format=3"', timeout=5)
    if ok and output:
        return output.strip()

    return "Could not retrieve weather information. Check your internet connection."


def execute_set_brightness(level: float) -> str:
    """Set display brightness (0.0 to 1.0)."""
    clamped = max(0.0, min(1.0, level))

    # Try the brightness CLI tool (brew install brightness)
    output, ok = _run(f"brightness {clamped}")
    if ok:
        return f"Brightness set to {int(clamped * 100)}%"

    # Fallback: AppleScript via System Events (may not work on all Macs)
    script = (
        f'tell application "System Events" to tell appearance preferences '
        f'to set dark mode to {"true" if clamped < 0.3 else "false"}'
    )
    _osascript(script)

    return (
        f"Could not set brightness directly. "
        f"Install 'brightness' via Homebrew: brew install brightness"
    )


def execute_set_volume(level: int, mute: bool = False) -> str:
    """Set system volume (0-100) or mute/unmute."""
    if mute:
        _osascript("set volume output muted true")
        return "System audio muted"

    clamped = max(0, min(100, level))
    _osascript(f"set volume output volume {clamped}")
    # Also unmute if setting volume
    _osascript("set volume output muted false")
    return f"Volume set to {clamped}%"


def execute_get_system_info(category: str) -> str:
    """Get system information by category."""
    handlers = {
        "wifi": _get_wifi_info,
        "battery": _get_battery_info,
        "disk": _get_disk_info,
        "ip": _get_ip_info,
        "system": _get_system_version,
        "memory": _get_memory_info,
        "cpu": _get_cpu_info,
    }
    handler = handlers.get(category.lower())
    if handler:
        return handler()
    available = ", ".join(sorted(handlers.keys()))
    return f"Unknown category '{category}'. Available: {available}"


def _get_wifi_info() -> str:
    airport = "/System/Library/PrivateFrameworks/Apple80211.framework/Resources/airport"
    output, ok = _run(f"{airport} -I")
    if not ok:
        # Fallback
        output, ok = _run(
            "system_profiler SPAirPortDataType 2>/dev/null | grep -A5 'Current Network'"
        )
        if ok and output:
            return f"Wi-Fi info: {output}"
        return "Could not retrieve Wi-Fi information"

    # Parse airport output for key fields
    ssid = _extract_field(output, "SSID")
    signal = _extract_field(output, "agrCtlRSSI")
    noise = _extract_field(output, "agrCtlNoise")
    channel = _extract_field(output, "channel")

    parts = []
    if ssid:
        parts.append(f"Connected to {ssid}")
    if signal:
        # Convert dBm to rough quality
        dbm = int(signal)
        if dbm >= -50:
            quality = "excellent"
        elif dbm >= -60:
            quality = "good"
        elif dbm >= -70:
            quality = "fair"
        else:
            quality = "weak"
        parts.append(f"signal {quality} ({signal} dBm)")
    if channel:
        parts.append(f"channel {channel}")

    return ". ".join(parts) if parts else "Wi-Fi information unavailable"


def _get_battery_info() -> str:
    output, ok = _run("pmset -g batt")
    if not ok:
        return "Could not retrieve battery information"

    # Parse battery percentage and status
    match = re.search(r'(\d+)%;\s*(\w+)', output)
    if match:
        pct = match.group(1)
        status = match.group(2)
        return f"Battery at {pct}%, {status}"
    return output


def _get_disk_info() -> str:
    output, ok = _run("df -h / | tail -1")
    if not ok:
        return "Could not retrieve disk information"
    parts = output.split()
    if len(parts) >= 5:
        return f"Disk: {parts[3]} free of {parts[1]} total ({parts[4]} used)"
    return output


def _get_ip_info() -> str:
    local_ip, ok1 = _run("ipconfig getifaddr en0")
    public_ip, ok2 = _run("curl -s ifconfig.me", timeout=5)
    parts = []
    if ok1 and local_ip:
        parts.append(f"Local IP: {local_ip}")
    if ok2 and public_ip:
        parts.append(f"Public IP: {public_ip}")
    return ". ".join(parts) if parts else "Could not retrieve IP information"


def _get_system_version() -> str:
    output, ok = _run("sw_vers")
    if not ok:
        return "Could not retrieve system version"
    lines = output.strip().split("\n")
    info = {}
    for line in lines:
        if ":" in line:
            key, val = line.split(":", 1)
            info[key.strip()] = val.strip()
    name = info.get("ProductName", "macOS")
    version = info.get("ProductVersion", "unknown")
    build = info.get("BuildVersion", "")
    return f"{name} {version} ({build})"


def _get_memory_info() -> str:
    output, ok = _run("sysctl -n hw.memsize")
    if ok and output:
        gb = int(output) / (1024 ** 3)
        return f"Total memory: {gb:.0f} GB"
    return "Could not retrieve memory information"


def _get_cpu_info() -> str:
    output, ok = _run("sysctl -n machdep.cpu.brand_string")
    if ok and output:
        return f"CPU: {output}"
    return "Could not retrieve CPU information"


def _extract_field(text: str, field: str) -> str | None:
    """Extract a value from key: value formatted text."""
    for line in text.split("\n"):
        if field in line and ":" in line:
            return line.split(":", 1)[1].strip()
    return None


def execute_manage_app(action: str, app_name: str) -> str:
    """Open, close, or check if an application is running."""
    if action == "open":
        result = subprocess.run(
            ["open", "-a", app_name],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return f"Opened {app_name}"
        return f"Failed to open {app_name}: {result.stderr.strip()}"

    elif action == "close":
        output, ok = _osascript(f'tell application "{app_name}" to quit')
        return f"Closed {app_name}" if ok else f"Failed to close {app_name}"

    elif action == "check":
        output, ok = _run(
            f"pgrep -x '{app_name}' > /dev/null && echo running || echo not running"
        )
        return f"{app_name} is {output}"

    return f"Unknown action '{action}'. Use: open, close, or check"


def execute_search_web(query: str) -> str:
    """Open a web search in the default browser."""
    encoded = urllib.request.quote(query)
    url = f"https://www.google.com/search?q={encoded}"
    subprocess.run(["open", url], capture_output=True, timeout=5)
    return f"Searching for: {query}"


def execute_run_shell(command: str) -> str:
    """Run an arbitrary shell command (escape hatch)."""
    output, ok = _run(command)
    return output


def execute_speak(text: str) -> str:
    """Speak text via the Kokoro TTS control server."""
    return _post_control("/speak", text)
