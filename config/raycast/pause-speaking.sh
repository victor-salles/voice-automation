#!/bin/bash
set -euo pipefail

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Pause/Resume Speaking
# @raycast.mode silent
# @raycast.packageName Kokoro TTS

# Optional parameters:
# @raycast.icon ⏯
# @raycast.description Toggle pause/resume Kokoro TTS playback

"$HOME/code/voice-automation/scripts/voice-ctl" pause
