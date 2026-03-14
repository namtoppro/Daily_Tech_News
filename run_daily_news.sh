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

STEP_RESULTS=()

record_step_result() {
  local step_name="$1"
  local status="$2"
  STEP_RESULTS+=("${step_name}|${status}")
}

print_step_summary() {
  log "=========================================="
  log "STEP SUMMARY"
  for item in "${STEP_RESULTS[@]}"; do
    local name="${item%%|*}"
    local status="${item##*|}"
    log "- ${name}: ${status}"
  done
  log "=========================================="
}

run_required_step() {
  local step_name="$1"
  shift

  log "$step_name"
  if "$@" 2>&1 | tee -a "$LOG_FILE"; then
    record_step_result "$step_name" "SUCCESS"
    log "$step_name 성공"
  else
    record_step_result "$step_name" "FAILED"
    log "$step_name 실패 - 필수 단계 실패로 중단"
    print_step_summary
    exit 1
  fi
}

run_optional_step() {
  local step_name="$1"
  local script_path="$2"

  log "$step_name"
  if "$script_path" 2>&1 | tee -a "$LOG_FILE"; then
    record_step_result "$step_name" "SUCCESS"
    log "$step_name 성공"
  else
    record_step_result "$step_name" "FAILED"
    log "$step_name 실패 - 텍스트 발행은 유지하고 다음 단계로 진행"
  fi
}

run_required_step "Step 1: 뉴스 수집 및 HTML 생성" python3 generator2.py

run_optional_step "Step 2: 오디오 파이프라인" "$SCRIPT_DIR/run_audio_pipeline.sh"
run_optional_step "Step 3: 이미지 파이프라인" "$SCRIPT_DIR/run_image_pipeline.sh"
run_optional_step "Step 4: 비디오 파이프라인" "$SCRIPT_DIR/run_video_pipeline.sh"
run_optional_step "Step 5: 유튜브 메타데이터 생성" "$SCRIPT_DIR/run_youtube_metadata.sh"

log "Step 6: Git 변경사항 확인"
GIT_STATUS="$(git status --porcelain)"
if [ -z "$GIT_STATUS" ]; then
  record_step_result "Step 6: Git 변경사항 확인" "NO_CHANGES"
  log "변경사항 없음. 작업 종료."
  print_step_summary
  exit 0
fi
record_step_result "Step 6: Git 변경사항 확인" "SUCCESS"
printf '%s\n' "$GIT_STATUS" | tee -a "$LOG_FILE"

log "Step 7: Git add"
if git add .; then
  record_step_result "Step 7: Git add" "SUCCESS"
else
  record_step_result "Step 7: Git add" "FAILED"
  log "Git add 실패"
  print_step_summary
  exit 1
fi

log "Step 8: Git commit"
COMMIT_MESSAGE="Auto-update news - $(date '+%Y-%m-%d %H:%M')"
if git commit -m "$COMMIT_MESSAGE"; then
  record_step_result "Step 8: Git commit" "SUCCESS"
  log "Git commit 성공: $COMMIT_MESSAGE"
else
  record_step_result "Step 8: Git commit" "FAILED"
  log "Git commit 실패"
  print_step_summary
  exit 1
fi

log "Step 9: Git push"
if git push; then
  record_step_result "Step 9: Git push" "SUCCESS"
  log "Git push 성공"
else
  record_step_result "Step 9: Git push" "FAILED"
  log "Git push 실패"
  print_step_summary
  exit 1
fi

print_step_summary
log "SUCCESS: 모든 작업 완료"
log "=========================================="
