# Voice Automation — Project Instructions

## Design Philosophy

Simple is better than complex. Explicit is better than implicit.
Follow SOLID principles, test-driven development, and the Zen of Python.
Ship the simple version first, iterate only when real feedback demands it.

## Code Conventions

- Small, focused files. One responsibility per module.
- Verbose, self-documenting names over comments.
- Test files: one per function/module, pytest with plain functions.
- Test names describe the scenario: `test_strip_code_blocks_preserves_text_outside_code_blocks`
- No docstrings on test functions — the name is the documentation.

## Architecture

- **Hammerspoon** is the central control plane (HTTP server on localhost:18880)
- **speak.sh** is the low-level TTS engine (direct Kokoro API)
- **voice-ctl** is the user-facing CLI (routes through Hammerspoon)
- All entry points (hotkey, Raycast, terminal) go through Hammerspoon for queue/state sync

## Open Source Readiness

- No personal information in code. Use `$HOME` and env vars for user-specific paths.
- Environment variables for configuration: `KOKORO_CONTROL_PORT`, `KOKORO_SPEED`, `KOKORO_PT_VOICE`, `KOKORO_EN_VOICE`
- Keep `.claude/settings.local.json` in `.gitignore` (user-specific Claude Code permissions)

## Testing

- Run tests: `/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 -m pytest tests/ -v`
- All Python modules in `scripts/` are testable via pytest
- Hammerspoon/Lua code is tested manually (reload with `hs.reload()`)

## Key Files

- `scripts/speak.sh` — TTS engine (streaming via curl | ffplay)
- `scripts/clean_for_tts.py` — Text preprocessing pipeline
- `scripts/detect_lang.py` — PT/EN language detection
- `scripts/voice-ctl` — CLI control wrapper
- `config/hammerspoon/kokoro.lua` — Hammerspoon integration + HTTP server
- `config/raycast/` — Raycast script commands
- `config/launchd/` — LaunchAgent for Kokoro auto-start
