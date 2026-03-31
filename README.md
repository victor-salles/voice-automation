# VoiceFlow

A native macOS menu bar app that reads selected text aloud using a local Kokoro TTS server. Select text anywhere, press `⌥S`, and hear it spoken — no internet required.

## Features

- **Global hotkey** — `⌥S` speaks the selected text, or stops playback if already speaking
- **Menu bar control** — click the speaker icon to speak, stop, or adjust speed
- **Queued playback** — long text is split into segments; the next segment is pre-synthesized while the current one plays, so transitions are near-instant
- **Playback speed** — 0.75× to 2× in the Speed submenu, applied without re-synthesis
- **Visual status** — SF Symbol in the menu bar reflects idle / processing / playing / error state
- **Works in any app** — reads selected text via the macOS Accessibility API

## Requirements

- macOS 14+
- [Kokoro-FastAPI](https://github.com/remsky/Kokoro-FastAPI) running locally on port 8880
- Xcode Command Line Tools (`xcode-select --install`)

## Setup

### 1. Start Kokoro

VoiceFlow synthesizes speech by calling a local Kokoro-FastAPI server. The easiest way to keep it running is via the included LaunchAgent:

```bash
# Install the startup script
cp config/launchd/start.sh ~/.kokoro-fastapi/start.sh
chmod +x ~/.kokoro-fastapi/start.sh

# Install and load the LaunchAgent (auto-starts on login)
sed "s|__HOME__|$HOME|g" config/launchd/com.local.kokoro.plist \
  > ~/Library/LaunchAgents/com.local.kokoro.plist
launchctl load ~/Library/LaunchAgents/com.local.kokoro.plist

# Verify it's running
curl http://localhost:8880/v1/audio/voices
```

### 2. Install VoiceFlow

```bash
cd VoiceFlow
make install
```

This builds a release binary, bundles it into `VoiceFlow.app`, signs it, and copies it to `~/Applications/`.

### 3. Grant Accessibility

Open **System Settings → Privacy & Security → Accessibility** and add VoiceFlow. This is required once — the self-signed certificate keeps the identity stable across rebuilds.

### 4. Launch

```bash
open ~/Applications/VoiceFlow.app
```

The speaker icon appears in the menu bar. Select text anywhere and press `⌥S`.

## Usage

| Action | How |
|--------|-----|
| Speak selected text | `⌥S` or menu bar → Speak Selection |
| Stop playback | `⌥S` again, or menu bar → Stop |
| Change speed | Menu bar → Speed |
| Quit | Menu bar → Quit VoiceFlow |

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `KOKORO_HOST` | `localhost` | Kokoro server host |
| `KOKORO_PORT` | `8880` | Kokoro server port |
| `KOKORO_EN_VOICE` | `af_heart` | Voice ID (see Kokoro docs for options) |

Set these in your shell profile or in a launchd plist `EnvironmentVariables` block.

## Building from Source

```bash
cd VoiceFlow
make build     # debug build only
make bundle    # build + create .app bundle
make install   # build + bundle + sign + copy to ~/Applications/
make clean     # remove build artifacts
```

## License

MIT
