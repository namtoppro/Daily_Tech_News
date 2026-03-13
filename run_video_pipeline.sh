#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/$(date +%F)-video.log"
mkdir -p "$LOG_DIR"

log() {
  local msg="$1"
  printf '%s - %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$msg" | tee -a "$LOG_FILE"
}

cd "$SCRIPT_DIR"
if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

log 'Video pipeline start'
python3 video_pipeline.py 2>&1 | tee -a "$LOG_FILE"
log 'Video pipeline end'
