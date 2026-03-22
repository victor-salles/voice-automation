# Voice Automation

Local voice I/O stack for macOS (Apple Silicon). Fully offline STT + TTS with global hotkeys.

## What it does

- **TTS**: Select text in any app → press `⌥S` → Kokoro speaks it aloud
- **STT**: Right-click any audio file → transcribe with mlx-whisper
- **Auto language detection**: Portuguese text uses `pf_dora`, English text uses `af_heart`

## Architecture

```
VOICE OUTPUT (TTS)
  Text source: selected text, clipboard, or CLI argument
    → speak.sh (auto-detects PT/EN)
      → POST http://localhost:8880/v1/audio/speech (Kokoro FastAPI)
        → afplay output.wav

VOICE INPUT (STT)
  Audio file → transcribe_audio.sh
    → mlx-whisper (whisper-turbo, local)
      → plain text to stdout

KOKORO SERVER
  Model: Kokoro-82M (CPU, Apple Silicon)
  Repo:  ~/.kokoro-fastapi (remsky/Kokoro-FastAPI)
  Port:  8880
  Auto-start: LaunchAgent (com.local.kokoro)
```

## Setup

### 1. Kokoro TTS Server

The server is managed by a LaunchAgent that starts on login:

```bash
# Copy the LaunchAgent and start script
cp config/launchd/com.local.kokoro.plist ~/Library/LaunchAgents/
cp config/launchd/start.sh ~/.kokoro-fastapi/start.sh

# Load it (starts immediately + on every login)
launchctl load ~/Library/LaunchAgents/com.local.kokoro.plist

# Verify
curl http://localhost:8880/v1/audio/voices
```

### 2. Hammerspoon (global hotkeys)

```bash
brew install --cask hammerspoon
```

Add to `~/.hammerspoon/init.lua`:

```lua
package.path = os.getenv("HOME") .. "/code/voice-automation/config/hammerspoon/?.lua;" .. package.path
require("kokoro")
```

Grant Hammerspoon **Accessibility** access in System Settings → Privacy & Security.

| Hotkey | Action |
|--------|--------|
| `⌥S`  | Speak selected text |
| `⌥⇧S` | Stop speaking |

### 3. Raycast (optional)

```bash
# Point Raycast Script Commands directory to:
~/.config/raycast/scripts/

# Copy scripts there
cp config/raycast/*.sh ~/.config/raycast/scripts/
chmod +x ~/.config/raycast/scripts/speak-selection.sh
chmod +x ~/.config/raycast/scripts/stop-speaking.sh
```

## Usage

```bash
# Speak text directly
./scripts/speak.sh "Hello, this is a test"
./scripts/speak.sh "Olá, isso é um teste"

# Force a specific voice
KOKORO_VOICE=bf_emma ./scripts/speak.sh "British accent"

# Change default voices
export KOKORO_EN_VOICE=am_adam   # American male
export KOKORO_PT_VOICE=pm_alex   # Brazilian male

# Transcribe audio
./scripts/transcribe_audio.sh ~/Downloads/recording.m4a
```

## Available voices

| Prefix | Language | Voices |
|--------|----------|--------|
| `af_` | 🇺🇸 American English (F) | heart, nova, bella, sarah, sky, river, nicole, alloy, jessica, kore, aoede, jadzia |
| `am_` | 🇺🇸 American English (M) | adam, echo, eric, liam, michael, onyx, puck, fenrir |
| `bf_` | 🇬🇧 British English (F) | emma, alice, lily |
| `bm_` | 🇬🇧 British English (M) | george, daniel, fable, lewis |
| `pf_` | 🇧🇷 Brazilian Portuguese (F) | dora |
| `pm_` | 🇧🇷 Brazilian Portuguese (M) | alex |

## Dependencies

- [Kokoro-FastAPI](https://github.com/remsky/Kokoro-FastAPI) at `~/.kokoro-fastapi/`
- [espeak-ng](https://github.com/espeak-ng/espeak-ng): `brew install espeak-ng`
- [mlx-whisper](https://github.com/ml-explore/mlx-examples): for STT
- [Hammerspoon](https://www.hammerspoon.org/): for global hotkeys
