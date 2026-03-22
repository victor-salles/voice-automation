#!/bin/bash
# speak.sh — reads selected/clipboard text with Kokoro TTS
# Usage: speak.sh [text]           — speaks the given text (auto-detects language)
#        speak.sh                   — copies current selection via Cmd+C, then speaks it
#        KOKORO_VOICE=af_heart speak.sh "text"  — force a specific voice

SPEED="${KOKORO_SPEED:-1.1}"
WAV_FILE="${TMPDIR:-/tmp}/kokoro_speak_${UID}.wav"

PT_VOICE="${KOKORO_PT_VOICE:-pf_dora}"
EN_VOICE="${KOKORO_EN_VOICE:-af_heart}"

if [ -n "$1" ]; then
  TEXT="$1"
else
  osascript -e 'tell application "System Events" to keystroke "c" using command down'
  sleep 0.3
  TEXT=$(pbpaste)
fi

if [ -z "$TEXT" ]; then
  osascript -e 'display notification "No text selected or in clipboard" with title "Kokoro TTS"'
  exit 1
fi

# Auto-detect language unless voice is explicitly set
if [ -n "$KOKORO_VOICE" ]; then
  VOICE="$KOKORO_VOICE"
else
  DETECTED_LANG=$(echo "$TEXT" | python3 -c "
import re, sys
text = sys.stdin.read()
pt_chars = len(re.findall(r'[ãõçÃÕÇ]', text))
pt_accents = len(re.findall(r'[àáâéêíóôúÀÁÂÉÊÍÓÔÚ]', text))
pt_words = len(re.findall(
    r'\b(de|da|do|das|dos|em|na|no|nas|nos|para|por|com|uma|uns|umas'
    r'|que|não|são|está|isso|como|mais|também|você|ele|ela|esse|essa'
    r'|este|esta|já|muito|pode|seu|sua|ter|foi|havia|ou|mas|ao|aos'
    r'|até|pelo|pela|pelos|pelas)\b', text.lower()))
print('pt' if pt_chars * 3 + pt_accents * 2 + pt_words >= 2 else 'en')
")

  if [ "$DETECTED_LANG" = "pt" ]; then
    VOICE="$PT_VOICE"
  else
    VOICE="$EN_VOICE"
  fi
fi

pkill afplay 2>/dev/null

ENCODED=$(echo "$TEXT" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')

HTTP_CODE=$(curl -s \
  -o "$WAV_FILE" \
  -w "%{http_code}" \
  -X POST http://localhost:8880/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"kokoro\",\"input\":${ENCODED},\"voice\":\"${VOICE}\",\"speed\":${SPEED},\"response_format\":\"wav\"}")

if [ "$HTTP_CODE" != "200" ]; then
  osascript -e "display notification \"Kokoro error: HTTP ${HTTP_CODE} - is the server running?\" with title \"TTS Failed\""
  exit 1
fi

afplay "$WAV_FILE"
