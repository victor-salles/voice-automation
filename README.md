# Voice Automation — Fully Local Voice I/O for macOS (Apple Silicon)

A complete, offline voice automation stack for macOS. Select text anywhere, press `Option+S`, and hear it spoken aloud in seconds. Built with Kokoro-82M (CPU-based TTS), Hammerspoon (hotkeys + menu bar), and a CLI control interface.

## What It Does

- **Text-to-speech (TTS)**: Select text in any app → press `Option+S` → Kokoro speaks it (streaming playback starts in <1s)
- **Auto language detection**: Detects Portuguese vs English text and uses the appropriate voice automatically
- **Queueing and playback control**: Stack multiple texts, play/pause/stop via hotkeys or menu bar
- **Menu bar status indicator**: Colored dot shows server status (green=ready, blue=speaking, yellow=paused, red=offline)
- **HTTP control server**: CLI tool and Raycast integration for scripting voice automation

## Architecture Diagram

```
VOICE OUTPUT (TTS)
  Text source: selected text, clipboard, hotkey, or HTTP API
    ↓
  Hammerspoon (control plane, hotkeys, menu bar)
    ↓
  voice-ctl CLI / speak.sh (engine)
    ├─ Language detection (PT/EN)
    ├─ Text cleaning (markdown, code, URLs, symbols)
    ↓
  POST http://localhost:8880/v1/audio/speech (streaming mp3)
    ↓
  Kokoro-82M TTS server
    ↓
  ffplay (streaming playback) or afplay (fallback)

HTTP CONTROL
  Hammerspoon runs control server on localhost:18880
  ├─ GET /status        → JSON status (state, current text, queue length)
  ├─ POST /speak [text] → Queue text for playback
  ├─ POST /stop         → Stop playback and clear queue
  └─ POST /pause        → Toggle pause/resume

VOICE INPUT (STT) — future feature
  Audio file → mlx-whisper (Whisper Turbo, local)
```

## Prerequisites

- **macOS 13+** with **Apple Silicon** (M1/M2/M3+)
- **Homebrew** (for formula installation)
- **Python 3.9+** (for text cleaning and language detection)
- **FFmpeg** (provides `ffplay` for streaming audio)
- **Hammerspoon** (hotkeys + menu bar indicator)
- **Kokoro-FastAPI** (local TTS server at `~/.kokoro-fastapi/`)

## Quick Start

### 1. Install Dependencies

```bash
# Install Homebrew packages
brew install hammerspoon ffmpeg espeak-ng

# Install Kokoro-FastAPI TTS server
git clone https://github.com/remsky/Kokoro-FastAPI.git ~/.kokoro-fastapi
cd ~/.kokoro-fastapi
pip install -r requirements.txt

# Download the Kokoro-82M model (runs once, ~350MB)
python3 -c "from kokoro import build_model; build_model('v0_19.pth')"
```

### 2. Set Up Kokoro as a Launch Agent (Auto-Start on Login)

```bash
# Copy the startup script
cp config/launchd/start.sh ~/.kokoro-fastapi/start.sh
chmod +x ~/.kokoro-fastapi/start.sh

# Install and load the LaunchAgent (substitutes $HOME automatically)
sed "s|__HOME__|$HOME|g" config/launchd/com.local.kokoro.plist \
  > ~/Library/LaunchAgents/com.local.kokoro.plist

# Load it (starts immediately + on every login)
launchctl load ~/Library/LaunchAgents/com.local.kokoro.plist

# Verify it's running
curl http://localhost:8880/v1/audio/voices
```

### 3. Install Hammerspoon and Configure Hotkeys

```bash
# Already installed via Homebrew, or use the cask:
brew install --cask hammerspoon
```

Edit `~/.hammerspoon/init.lua` and add:

```lua
package.path = os.getenv("HOME") .. "/code/voice-automation/config/hammerspoon/?.lua;" .. package.path
require("kokoro")
```

Then grant Hammerspoon **Accessibility** access:
- System Settings → Privacy & Security → Accessibility
- Find and enable Hammerspoon

Reload Hammerspoon config: Press `Cmd+Option+Ctrl+U` or click menu → Reload Config.

### 4. (Optional) Set Up Raycast Integration

```bash
# Copy Raycast script commands
cp config/raycast/*.sh ~/.config/raycast/scripts/
chmod +x ~/.config/raycast/scripts/*.sh
```

## voice-ctl CLI Reference

`voice-ctl` is the primary user-facing interface for programmatic voice automation. It communicates with the Hammerspoon HTTP control server (localhost:18880).

### Usage

```
voice-ctl <command> [args]
```

### Commands

#### `voice-ctl speak [TEXT]`

Queue text for playback. If no argument is given, reads from clipboard. Use `-` to read from stdin.

```bash
# Speak a direct string
voice-ctl speak "Hello, world"

# Read from clipboard (if COPY'd something)
voice-ctl speak

# Pipe from stdin
echo "Olá, mundo" | voice-ctl speak -

# Chain with other commands
printf "Important: Check the logs" | voice-ctl speak -
```

#### `voice-ctl stop`

Stop playback immediately and clear the queue.

```bash
voice-ctl stop
```

#### `voice-ctl pause`

Toggle pause/resume on current playback.

```bash
voice-ctl pause
# First call: pauses playback
# Second call: resumes from where it paused
```

#### `voice-ctl status`

Print JSON status of the control server.

```bash
voice-ctl status

# Output (example):
# {
#   "state": "speaking",
#   "currentText": "Hello world",
#   "queueLength": 2
# }
```

#### `voice-ctl help`

Display command help.

```bash
voice-ctl help
```

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `KOKORO_CONTROL_HOST` | `localhost` | Hostname of control server |
| `KOKORO_CONTROL_PORT` | `18880` | Port of control server |

### Examples

```bash
# Basic workflow
voice-ctl speak "Starting the deployment"
sleep 2
voice-ctl pause
voice-ctl pause  # Resume
voice-ctl stop

# Error handling
voice-ctl speak "text" || echo "Failed to queue"

# Scripting
if voice-ctl status | grep -q '"state":"ready"'; then
  echo "System is idle, safe to proceed"
fi

# Monitoring with shell loop
while true; do
  voice-ctl status | jq '.state'
  sleep 1
done
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (malformed command, empty text, server error) |
| 2 | Server unreachable (Kokoro control server not running) |

## Keyboard Shortcuts Cheat Sheet

| Shortcut | Action |
|----------|--------|
| `Option+S` | Toggle speak/stop (single hotkey: start playback, or stop if playing) |
| `Option+Shift+V` | Open voice picker popup |

### Menu Bar Dropdown

Click the colored dot (●) in the menu bar to access:

- **Now playing**: Text being spoken with pause/stop buttons
- **Queue**: Pending items (click to remove)
- **History**: Recently spoken items (click to replay)
- **Voice**: Submenu to select a specific voice or auto-detect
- **Clear History**: Wipe all queue and history

## Features Cheat Sheet

| Feature | Description |
|---------|-------------|
| **Streaming TTS** | Audio starts playing in <1s; no download wait |
| **Auto language detection** | Portuguese vs English; selects voice automatically |
| **9 voices** | US (3F, 3M), UK (2F, 2M), Brazil (1F, 1M) |
| **Queueing** | Stack texts; plays sequentially with auto-advance |
| **Play/pause/stop** | Full playback control via hotkeys and menu |
| **History with replay** | Menu bar shows recent items; click to replay |
| **Text cleaning** | Strips markdown, code blocks, URLs, emojis, keyboard symbols |
| **File extensions** | `.py` → "dot P Y", `.json` → "dot J S O N" |
| **UPPER_SNAKE_CASE expansion** | `KOKORO_DEBUG` → "Kokoro Debug", `HTTP_CODE` → "H T T P Code" |
| **Smart punctuation** | Em dashes and slashes become commas for natural pauses |
| **Menu bar status** | Colored dot: green=ready, blue=speaking, yellow=paused, red=offline |
| **HTTP control server** | Query status, queue texts, control playback via API |
| **Raycast integration** | Quick commands from Raycast command palette |

## Available Voices

| ID | Name | Language | Gender |
|----|------|----------|--------|
| `af_heart` | Heart | 🇺🇸 US English | F |
| `af_nova` | Nova | 🇺🇸 US English | F |
| `af_bella` | Bella | 🇺🇸 US English | F |
| `am_adam` | Adam | 🇺🇸 US English | M |
| `am_michael` | Michael | 🇺🇸 US English | M |
| `bf_emma` | Emma | 🇬🇧 UK English | F |
| `bm_george` | George | 🇬🇧 UK English | M |
| `pf_dora` | Dora | 🇧🇷 Brazilian Portuguese | F |
| `pm_alex` | Alex | 🇧🇷 Brazilian Portuguese | M |

### Force a Specific Voice

Use the voice picker hotkey (`Option+Shift+V`) in the menu bar, or programmatically:

```bash
# Via environment variable
KOKORO_PT_VOICE=pm_alex voice-ctl speak "Olá"

# Via speak.sh directly (if used without voice-ctl)
./scripts/speak.sh --voice af_heart "Hello"
```

## Configuration

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `KOKORO_EN_VOICE` | `af_heart` | Default English voice |
| `KOKORO_PT_VOICE` | `pf_dora` | Default Portuguese voice |
| `KOKORO_CONTROL_HOST` | `localhost` | Hammerspoon HTTP server host |
| `KOKORO_CONTROL_PORT` | `18880` | Hammerspoon HTTP server port |
| `KOKORO_SPEED` | `1.1` | TTS playback speed (0.5–2.0) |
| `KOKORO_DEBUG` | `0` | Set to `1` to log debug output to `/tmp/kokoro_debug.log` |

### Example: Change Default Voices

```bash
# Add to ~/.zshrc or ~/.bashrc
export KOKORO_EN_VOICE=am_adam    # American male for English
export KOKORO_PT_VOICE=pm_alex    # Brazilian male for Portuguese
```

## Project Structure

```
voice-automation/
├── README.md                              # This file
├── BACKLOG.md                             # Feature ideas and roadmap
│
├── scripts/
│   ├── voice-ctl                          # Primary CLI interface (speaks, stops, pauses, checks status)
│   ├── speak.sh                           # TTS engine (language detection, text cleaning, streaming)
│   ├── clean_for_tts.py                   # Text preprocessing (markdown, URLs, special chars, file exts)
│   ├── detect_lang.py                     # Portuguese vs English detection
│   └── transcribe_audio.sh                # STT wrapper for mlx-whisper (future)
│
├── config/
│   ├── hammerspoon/
│   │   └── kokoro.lua                     # Hotkeys, menu bar, HTTP control server, queue logic
│   │
│   ├── launchd/
│   │   ├── com.local.kokoro.plist         # LaunchAgent config (auto-start Kokoro on login)
│   │   └── start.sh                       # Startup script for TTS server
│   │
│   └── raycast/
│       ├── speak-selection.sh             # Raycast: speak selected text
│       └── stop-speaking.sh               # Raycast: stop playback
│
└── config/launchd/ → manages ~/.kokoro-fastapi/ (external, cloned from GitHub)
```

## Dependencies

All dependencies are installable via Homebrew or pip:

| Dependency | Install | Purpose |
|------------|---------|---------|
| **Hammerspoon** | `brew install --cask hammerspoon` | Hotkeys, menu bar, HTTP control server |
| **FFmpeg** | `brew install ffmpeg` | Provides `ffplay` for streaming audio playback |
| **Espeak-ng** | `brew install espeak-ng` | Phoneme synthesis (used by Kokoro) |
| **Python 3.9+** | `brew install python@3.12` | Text cleaning, language detection |
| **curl** | Pre-installed | HTTP communication |
| **jq** (optional) | `brew install jq` | JSON pretty-printing in `voice-ctl status` |
| **Kokoro-FastAPI** | GitHub (manual clone) | TTS model server |

## Contributing

### Running Tests

```bash
# Run all Python tests
python3 -m pytest scripts/

# Test text cleaning
echo "# Hello **world**" | python3 scripts/clean_for_tts.py

# Test language detection
echo "Olá, tudo bem?" | python3 scripts/detect_lang.py
```

### Code Style

- **Shell scripts**: Use `set -euo pipefail`, avoid subshells where possible
- **Python**: Follow PEP 8; use type hints in new code
- **Lua**: Follow Hammerspoon conventions; keep functions under 50 lines when possible
- **Commit messages**: Be concise; reference issue numbers if applicable

### Reporting Bugs

Include:
1. The command you ran
2. The error message (with exit code)
3. Kokoro server status (`curl http://localhost:8880/v1/audio/voices`)
4. System info (`uname -a` and `python3 --version`)

## License

MIT

---

**Built with:** Kokoro-82M, Hammerspoon, FFmpeg, Python

**Inspired by:** macOS accessibility features, local-first computing, and the goal of keeping voice automation completely offline.
