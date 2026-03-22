#!/bin/bash
# speak.sh — reads selected/clipboard text with Kokoro TTS (streaming)
# Usage: speak.sh [text]           — speaks the given text (auto-detects language)
#        speak.sh                   — copies current selection via Cmd+C, then speaks it
#        KOKORO_VOICE=af_heart speak.sh "text"  — force a specific voice

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SPEED="${KOKORO_SPEED:-1.1}"
FFPLAY="/opt/homebrew/bin/ffplay"
KOKORO_URL="http://localhost:8880/v1/audio/speech"
WAV_FILE="${TMPDIR:-/tmp}/kokoro_speak_${UID}.wav"
LOG_FILE="${TMPDIR:-/tmp}/kokoro_debug.log"

PT_VOICE="${KOKORO_PT_VOICE:-pf_dora}"
EN_VOICE="${KOKORO_EN_VOICE:-af_heart}"

debug() {
  if [ "${KOKORO_DEBUG:-0}" = "1" ]; then
    echo "[$(date '+%H:%M:%S')] $*" >> "$LOG_FILE"
  fi
}

notify_error() {
  local msg="$1"
  debug "ERROR: $msg"
  echo "TTS: $msg" >&2
  # Play system error sound (non-blocking, unobtrusive)
  afplay /System/Library/Sounds/Basso.aiff &
}

# Parse optional flags
while [[ "${1:-}" == --* ]]; do
  case "$1" in
    --voice) KOKORO_VOICE="$2"; shift 2 ;;
    --speed) SPEED="$2"; shift 2 ;;
    *) shift ;;
  esac
done

if [ -n "$1" ]; then
  TEXT="$1"
  debug "source=argument"
else
  osascript -e 'tell application "System Events" to keystroke "c" using command down'
  sleep 0.3
  TEXT=$(pbpaste)
  debug "source=clipboard"
fi

debug "raw_text=$(echo "$TEXT" | head -c 200)"

if [ -z "$TEXT" ]; then
  notify_error "No text selected or in clipboard"
  exit 1
fi

# Clean text for TTS (strip markdown, code blocks, URLs, etc.)
TEXT=$(echo "$TEXT" | python3 "$SCRIPT_DIR/clean_for_tts.py")
debug "cleaned_text=$(echo "$TEXT" | head -c 200)"

# Auto-detect language unless voice is explicitly set
if [ -n "$KOKORO_VOICE" ]; then
  VOICE="$KOKORO_VOICE"
  debug "voice=explicit override=$VOICE"
else
  DETECTED_LANG=$(echo "$TEXT" | python3 "$SCRIPT_DIR/detect_lang.py")
  VOICE=$([ "$DETECTED_LANG" = "pt" ] && echo "$PT_VOICE" || echo "$EN_VOICE")
  debug "detected_lang=$DETECTED_LANG voice=$VOICE"
fi

# Kill any previous playback
pkill -x ffplay 2>/dev/null
pkill -x afplay 2>/dev/null

ENCODED=$(echo "$TEXT" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read(), ensure_ascii=False))')

PAYLOAD="{\"model\":\"kokoro\",\"input\":${ENCODED},\"voice\":\"${VOICE}\",\"speed\":${SPEED},\"response_format\":\"mp3\",\"stream\":true}"

# Streaming mode: pipe audio directly to ffplay
if [ -x "$FFPLAY" ]; then
  curl -s -N \
    -X POST "$KOKORO_URL" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" \
    | "$FFPLAY" -nodisp -autoexit -loglevel quiet -i pipe:0

  if [ "${PIPESTATUS[0]}" -ne 0 ]; then
    notify_error "Kokoro server is not running"
    exit 1
  fi
else
  # Fallback: download full wav then play with afplay
  HTTP_CODE=$(curl -s \
    -o "$WAV_FILE" \
    -w "%{http_code}" \
    -X POST "$KOKORO_URL" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"kokoro\",\"input\":${ENCODED},\"voice\":\"${VOICE}\",\"speed\":${SPEED},\"response_format\":\"wav\"}")

  if [ "$HTTP_CODE" != "200" ]; then
    notify_error "Kokoro error: HTTP ${HTTP_CODE} - is the server running?"
    exit 1
  fi

  afplay "$WAV_FILE"
fi
