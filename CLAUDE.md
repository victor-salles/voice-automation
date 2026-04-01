# VoiceFlow — Project Instructions

## Design Philosophy

Simple is better than complex. Explicit is better than implicit.
Follow SOLID principles and ship the simple version first — iterate only when real feedback demands it.

## Code Conventions

- Small, focused files. One responsibility per type.
- Verbose, self-documenting names over comments.
- No docstrings on functions whose name already describes the behaviour.

## Architecture

- **VoiceFlowApp.swift** — app entry point, `AppModel` composition root, `HotkeyState` (CGEvent tap for ⌥S)
- **StatusManager.swift** — `@Observable` status state machine (idle / processing / playing / error)
- **TTSEngine.swift** — Kokoro HTTP client + `AVAudioPlayer` queue; pre-synthesizes segment N+1 while playing N
- **LanguageInference.swift** — `NLLanguageRecognizer` → American English vs Brazilian Portuguese Kokoro voice
- **TextProcessor.swift** — text segmentation and cleaning pipeline (markdown, code, symbols)
- **TextExtractor.swift** — reads selected text from the focused app via the Accessibility API

## Building

```bash
cd VoiceFlow
make install        # build release, bundle .app, sign, copy to ~/Applications/
```

Requires Xcode Command Line Tools (`xcode-select --install`).

## Signing

The app is signed with a local self-signed certificate created in Keychain Access.
This keeps the code-signing identity stable across rebuilds so Accessibility permission is not revoked.
First install only: System Settings → Privacy & Security → Accessibility → add VoiceFlow.

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `KOKORO_HOST` | `localhost` | Kokoro server host |
| `KOKORO_PORT` | `8880` | Kokoro server port |
| `KOKORO_EN_VOICE` | `af_heart` | American English Kokoro voice ID |
| `KOKORO_PT_BR_VOICE` | `pf_dora` | Brazilian Portuguese Kokoro voice ID |

## Kokoro Server

VoiceFlow synthesizes speech by calling a local Kokoro-FastAPI server.
See `config/launchd/` for a LaunchAgent that auto-starts it on login.
