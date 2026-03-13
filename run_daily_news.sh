#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/$(date +%F).log"
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

log "=========================================="
log "Daily Tech News 자동 수집 시작"
log "작업 디렉터리: $SCRIPT_DIR"
log "=========================================="

log "Step 1: 뉴스 수집 및 HTML 생성"
python3 generator2.py 2>&1 | tee -a "$LOG_FILE"

log "Step 2: Git 변경사항 확인"
GIT_STATUS="$(git status --porcelain)"
if [ -z "$GIT_STATUS" ]; then
  log "변경사항 없음. 작업 종료."
  exit 0
fi
printf '%s\n' "$GIT_STATUS" | tee -a "$LOG_FILE"

log "Step 3: Git add"
git add .

log "Step 4: Git commit"
COMMIT_MESSAGE="Auto-update news - $(date '+%Y-%m-%d %H:%M')"
if git commit -m "$COMMIT_MESSAGE"; then
  log "Git commit 성공: $COMMIT_MESSAGE"
else
  log "Git commit 실패"
  exit 1
fi

log "Step 5: Git push"
git push
log "Git push 성공"

log "=========================================="
log "SUCCESS: 모든 작업 완료"
log "=========================================="
