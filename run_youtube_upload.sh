#!/bin/zsh
set -euo pipefail

cd /Users/namtop/data/Daily_Tech_News
source .venv/bin/activate
python3 youtube_upload.py
