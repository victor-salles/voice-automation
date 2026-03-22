# Backlog

## Next up

- [ ] **Claude Code post-response hook** — Automatically speak Claude Code responses via TTS. Set up a post-response hook in `.claude/settings.json` that pipes the response to `speak.sh`. Needs de-risking: determine max text length, handle code blocks (skip or summarize), handle streaming responses.

- [ ] **Chrome extension for reading webpages** — Read articles, selected text, or full pages in Chrome via Kokoro. A Chrome extension already exists at `~/kokoro-chrome-ext/` from a previous session but was never loaded. Evaluate if it works, fix if needed, or rebuild.

## Ideas

- [ ] Integration with Apple Notes — speak the current note
- [ ] Voice selection popup — Hammerspoon chooser (⌥⇧V) to pick a voice before speaking
- [ ] Reading speed control — hotkeys to adjust speed on the fly (⌥+ / ⌥-)
- [ ] PDF reading — pipe PDF text extraction into speak.sh
- [ ] True resume — sentence-level position tracking for resuming mid-text

## Done

- [x] Queue mode — ⌥S while speaking adds to queue, auto-advances
- [x] History/bookmark — stopped items saved in menu bar history, click to replay
- [x] Toggle hotkey — ⌥S starts or stops (single shortcut)
- [x] Menu bar dropdown — native dropdown with now-playing, queue, history, clear
- [x] Streaming TTS — mp3 streaming via ffplay
- [x] Auto language detection — PT/EN heuristic
- [x] Menu bar status indicator — colored dot (green/blue/red)
