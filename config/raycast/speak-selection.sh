#!/bin/bash
set -euo pipefail

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Speak Selection
# @raycast.mode silent
# @raycast.packageName Kokoro TTS

# Optional parameters:
# @raycast.icon 🔊
# @raycast.description Speak copied text aloud with Kokoro TTS (copy text first, then run)

TEXT=$(pbpaste)

if [ -z "$TEXT" ]; then
  echo "Nothing in clipboard"
  exit 1
fi

"$HOME/code/voice-automation/scripts/voice-ctl" speak "$TEXT"
