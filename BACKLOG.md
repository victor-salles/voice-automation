# Backlog

## Next up

- [ ] **Claude Code post-response hook** — Automatically speak Claude Code responses via TTS. Set up a post-response hook in `.claude/settings.json` that pipes the response to `speak.sh`. Needs de-risking: determine max text length, handle code blocks (skip or summarize), handle streaming responses.

- [ ] **Chrome extension for reading webpages** — Read articles, selected text, or full pages in Chrome via Kokoro. A Chrome extension already exists at `~/kokoro-chrome-ext/` from a previous session but was never loaded. Evaluate if it works, fix if needed, or rebuild.

## Ideas

- [ ] **Screen reading (no selection)** — Read visible window content without selecting text first. Use macOS Accessibility APIs (`AXUIElement`) via Hammerspoon's `hs.axuielement` to extract text from the frontmost window. Needs research on app compatibility, permissions, and fallback OCR via Vision framework.

- [ ] **Auto-captioning videos with STT** — Use mlx-whisper to automatically generate subtitle files (.srt/.vtt) from local video files. Could integrate with ffmpeg for audio extraction and batch processing.

- [ ] **Auto-transcription for accessibility** — Transcribe audio files (meetings, voice memos, podcasts) using mlx-whisper. Output as timestamped text or structured notes.

- [ ] **Voice assistant (STT → LLM → OS → TTS)** — Siri-like local assistant: mlx-whisper captures voice input → routes to LLM agent → agent executes OS-level actions → Kokoro speaks the response. Full voice I/O loop, entirely local.

- [ ] Integration with Apple Notes — speak the current note
- [ ] Reading speed control — hotkeys to adjust speed on the fly (⌥+ / ⌥-)
- [ ] PDF reading — pipe PDF text extraction into speak.sh
- [ ] Quick resume — paragraph-level position tracking for resuming mid-reading (Books, Articles, webpages, etc.)

## Done

- [x] Voice selection popup — Hammerspoon chooser (⌥⇧V) to pick a voice before speaking
- [x] Queue mode — ⌥S while speaking adds to queue, auto-advances
- [x] History/bookmark — stopped items saved in menu bar history, click to replay
- [x] Toggle hotkey — ⌥S starts or stops (single shortcut)
- [x] Menu bar dropdown — native dropdown with now-playing, queue, history, clear
- [x] Streaming TTS — mp3 streaming via ffplay
- [x] Auto language detection — PT/EN heuristic
- [x] Menu bar status indicator — colored dot (green/blue/red)
