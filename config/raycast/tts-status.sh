#!/bin/bash
set -euo pipefail

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title TTS Status
# @raycast.mode compact
# @raycast.packageName Kokoro TTS

# Optional parameters:
# @raycast.icon 📊
# @raycast.description Show Kokoro TTS playback status

"$HOME/code/voice-automation/scripts/voice-ctl" status
