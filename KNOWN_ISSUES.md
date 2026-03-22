# Known Issues

## Open

### Streaming playback latency is not instant
- **Symptom**: Playback starts faster than the old wav approach but still takes a few seconds, not <1s as expected.
- **Likely cause**: Kokoro needs to generate the first audio chunk before anything streams. For longer text, the model processes the first sentence before yielding. The ffplay mp3 decoder also needs enough data to start decoding.
- **Possible fixes**: Pre-split text into sentences and send the first sentence immediately; investigate if Kokoro supports a smaller initial chunk size; try raw PCM format instead of mp3 to reduce decoder buffering.

### Language detection is heuristic-based
- **Symptom**: Short text without obvious Portuguese markers (accents, common words) defaults to English even if it's Portuguese.
- **Workaround**: Set `KOKORO_VOICE=pf_dora` explicitly for ambiguous text.
- **Possible fix**: Use a proper language detection library (e.g., `langdetect` or `lingua`).

## Resolved

### speak.sh was reading file paths aloud instead of selected text
- **Root cause**: Apple Shortcuts serializes clipboard/selection as an RTF temp file in `~/Library/Group Containers/...` and passes the file path (not the text) as `$1`. Additionally, the wav output file at `/tmp/kokoro_speak.wav` was owned by `root` (created by the LaunchAgent), so curl couldn't overwrite it — `afplay` kept playing the same stale audio file containing a spoken Library path.
- **Fix**: Moved to Hammerspoon for hotkeys (bypasses Shortcuts entirely). Changed wav output to user-scoped path `$TMPDIR/kokoro_speak_$UID.wav`. Then moved to streaming mp3 via ffplay (no temp files at all).

### Portuguese accents escaped to Unicode in TTS payload
- **Root cause**: `json.dumps()` in speak.sh defaults to `ensure_ascii=True`, converting characters like `ç`, `ã`, `ó` to `\u00e7`, `\u00e3`, `\u00f3`. The Kokoro API received escaped sequences instead of raw UTF-8, causing the Brazilian Portuguese voice to mispronounce accented words (opção, nós, código).
- **Fix**: Added `ensure_ascii=False` to the `json.dumps()` call so accented characters are sent as raw UTF-8 in the JSON payload.

### osascript error notification crashed on em dash
- **Root cause**: The `—` (em dash) character in the osascript notification string caused an AppleScript syntax error, silently swallowing the "server not running" error.
- **Fix**: Replaced em dash with regular hyphen.
