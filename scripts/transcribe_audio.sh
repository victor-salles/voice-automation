#!/bin/bash
# transcribe_audio.sh — transcribes audio files using mlx-whisper
# Usage: transcribe_audio.sh /path/to/file.m4a
#   Outputs transcript to stdout. Pipe or redirect as needed.

export PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin:$PATH"

FILE="$1"

if [ -z "$FILE" ] || [ ! -f "$FILE" ]; then
  echo "Usage: transcribe_audio.sh /path/to/audio_file" >&2
  exit 1
fi

BASENAME=$(basename "$FILE" | sed 's/\.[^.]*$//')
OUTPUT_DIR=$(mktemp -d)

/Library/Frameworks/Python.framework/Versions/3.13/bin/mlx_whisper "$FILE" \
  --model mlx-community/whisper-turbo \
  --output-format txt \
  --output-dir "$OUTPUT_DIR" \
  --verbose False

cat "$OUTPUT_DIR/${BASENAME}.txt"
rm -rf "$OUTPUT_DIR"
