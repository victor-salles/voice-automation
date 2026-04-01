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
- **TextProcessor.swift** — cleaning, segmentation, heuristics when AX returns glued paragraphs
- **TextExtractor.swift** — selected text and focused text area via Accessibility API
- **VoiceFlowLogging.swift** / **SpeechPipelineDiagnostics.swift** — optional speech pipeline file log (see README)

## Building

```bash
cd VoiceFlow
make install
```

Requires Xcode Command Line Tools (`xcode-select --install`).

## Operator-facing docs

**Single source:** [README.md](README.md) — setup, Accessibility, env vars, Kokoro, debugging, Makefile targets.

## Kokoro Server

Local FastAPI wrapper; see `config/launchd/` for LaunchAgent.
