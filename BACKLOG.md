# Backlog

## Next up

- [ ] **Claude Code post-response hook** — Automatically speak Claude Code responses via TTS. Set up a post-response hook in `.claude/settings.json` that pipes the response to `speak.sh`. Needs de-risking: determine max text length, handle code blocks (skip or summarize), handle streaming responses.

- [ ] **Chrome extension for reading webpages** — Read articles, selected text, or full pages in Chrome via Kokoro. A Chrome extension already exists at `~/kokoro-chrome-ext/` from a previous session but was never loaded. Evaluate if it works, fix if needed, or rebuild.

## Ideas

- [ ] Voice selection popup — Hammerspoon chooser (⌥⇧V) to pick a voice before speaking
- [ ] Reading speed control — hotkeys to adjust speed on the fly (⌥+ / ⌥-)
- [ ] Bookmark/resume — save position in long text, resume later
- [ ] Queue mode — select multiple passages, speak them in sequence
- [ ] Integration with Apple Notes — speak the current note
- [ ] PDF reading — pipe PDF text extraction into speak.sh
