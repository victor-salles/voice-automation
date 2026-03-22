#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Stop Speaking
# @raycast.mode silent
# @raycast.packageName Kokoro TTS

# Optional parameters:
# @raycast.icon 🔇
# @raycast.description Stop Kokoro TTS playback

pkill -x ffplay 2>/dev/null
pkill -x afplay 2>/dev/null
