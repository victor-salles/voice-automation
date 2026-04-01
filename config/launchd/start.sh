#!/bin/bash
# Kokoro FastAPI startup script for LaunchAgent
set -e

KOKORO_DIR="$HOME/.kokoro-fastapi"

export USE_GPU=false
export USE_ONNX=false
export PYTHONPATH="$KOKORO_DIR:$KOKORO_DIR/api"
export MODEL_DIR="src/models"
export VOICES_DIR="src/voices/v1_0"
export WEB_PLAYER_PATH="$KOKORO_DIR/web"
export ESPEAK_DATA_PATH="/opt/homebrew/opt/espeak-ng/lib/espeak-ng-data"

cd "$KOKORO_DIR"

exec "$KOKORO_DIR/.venv/bin/python" \
  -m uvicorn api.src.main:app \
  --host 127.0.0.1 \
  --port 8880
