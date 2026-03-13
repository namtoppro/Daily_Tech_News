#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

run_test() {
  local name="$1"
  echo
  echo "===== RUN: $name ====="
  case "$name" in
    test_01_env.py|test_02_rss.py|test_03_gemini_basic.py|test_04_generate_html.py|test_05_generate_post.py|test_06_write_outputs.py)
      python3 "$name"
      ;;
    test_07_git_status.sh|test_08_pipeline_check.sh)
      bash "$name"
      ;;
    *)
      echo "Unknown test: $name" >&2
      exit 1
      ;;
  esac
}

for test_name in \
  test_01_env.py \
  test_02_rss.py \
  test_03_gemini_basic.py \
  test_04_generate_html.py \
  test_05_generate_post.py \
  test_06_write_outputs.py \
  test_07_git_status.sh \
  test_08_pipeline_check.sh
  do
    run_test "$test_name"
  done

echo
echo 'ALL STEP TESTS PASSED'
