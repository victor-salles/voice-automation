#!/bin/bash
set -euo pipefail

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Stop Speaking
# @raycast.mode silent
# @raycast.packageName Kokoro TTS

# Optional parameters:
# @raycast.icon 🔇
# @raycast.description Stop Kokoro TTS playback

"$HOME/code/voice-automation/scripts/voice-ctl" stop
