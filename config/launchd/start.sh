#!/bin/bash
# Kokoro FastAPI startup script for LaunchAgent
set -e

export USE_GPU=false
export USE_ONNX=false
export PYTHONPATH="/Users/victorrodrigues/.kokoro-fastapi:/Users/victorrodrigues/.kokoro-fastapi/api"
export MODEL_DIR="src/models"
export VOICES_DIR="src/voices/v1_0"
export WEB_PLAYER_PATH="/Users/victorrodrigues/.kokoro-fastapi/web"
export ESPEAK_DATA_PATH="/opt/homebrew/opt/espeak-ng/lib/espeak-ng-data"

cd /Users/victorrodrigues/.kokoro-fastapi

exec /Users/victorrodrigues/.kokoro-fastapi/.venv/bin/python \
  -m uvicorn api.src.main:app \
  --host 127.0.0.1 \
  --port 8880
