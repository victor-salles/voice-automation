#!/usr/bin/env bash
set -euo pipefail
# Pre-synthesize TTS audio to a file for gapless paragraph transitions.
#
# Usage:
#   echo "paragraph text" | ./pre_synth.sh /tmp/voice-cache/para_4.mp3 [voice]
#
# Reads text from stdin to avoid shell-escaping issues.

OUTPUT="${1:?Usage: echo text | pre_synth.sh OUTPUT_PATH [VOICE]}"
VOICE="${2:-}"
KOKORO_HOST="${KOKORO_HOST:-localhost}"
KOKORO_PORT="${KOKORO_PORT:-8880}"

# Resolve voice via detect_lang if not provided
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEXT="$(cat)"

if [ -z "$TEXT" ]; then
    echo "Error: empty text on stdin" >&2
    exit 1
fi

if [ -z "$VOICE" ]; then
    LANG=$("$SCRIPT_DIR/detect_lang.py" <<< "$TEXT" 2>/dev/null || echo "en")
    if [ "$LANG" = "pt" ]; then
        VOICE="${KOKORO_PT_VOICE:-pf_dora}"
    else
        VOICE="${KOKORO_EN_VOICE:-af_heart}"
    fi
fi

mkdir -p "$(dirname "$OUTPUT")"

# Build JSON payload safely with jq
PAYLOAD=$(jq -n --arg t "$TEXT" --arg v "$VOICE" '{input: $t, voice: $v}')

curl -sf --max-time 30 -X POST "http://${KOKORO_HOST}:${KOKORO_PORT}/v1/audio/speech" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" \
    --output "$OUTPUT"
