#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo '=== PIPELINE CHECK ==='
echo '1) test files existence'
ls -1 test_0* generator2.py run_daily_news.sh requirements.txt .env.example >/dev/null

echo '2) venv check'
if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi
python3 --version

echo '3) git writable check'
git status --short >/dev/null

echo 'OK'
