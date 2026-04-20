#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/$(date +%F).log"
REPORT_FILE="$LOG_DIR/$(date +%F)-report.txt"
REPORT_CHANNEL="${REPORT_CHANNEL:-telegram}"
REPORT_TARGET="${REPORT_TARGET:-5548753399}"
mkdir -p "$LOG_DIR"
START_TS="$(date '+%Y-%m-%d %H:%M:%S')"
FINAL_STATUS="RUNNING"
FINAL_NOTE=""
LATEST_COMMIT=""
COLLECTED_COUNT=""
YOUTUBE_UPLOAD_URL=""
YOUTUBE_UPLOAD_VIDEO_ID=""
YOUTUBE_UPLOAD_PRIVACY=""
OPTIONAL_FAILURES=0
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

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

extract_collected_count() {
  COLLECTED_COUNT="$(grep '총 .*개 기사 수집 완료' "$LOG_FILE" 2>/dev/null | tail -n 1 | sed -E 's/.*총 ([0-9]+)개 기사 수집 완료.*/\1/' || true)"
}

write_report() {
  local end_ts
  end_ts="$(date '+%Y-%m-%d %H:%M:%S')"
  extract_collected_count
  local receipt_file="$SCRIPT_DIR/archive/$(date +%F)-youtube-upload.json"
  if [ -f "$receipt_file" ]; then
    YOUTUBE_UPLOAD_URL="$(python3 - <<PY
import json
from pathlib import Path
p = Path(r'''$receipt_file''')
d = json.loads(p.read_text(encoding='utf-8'))
print(d.get('url',''))
PY
)"
    YOUTUBE_UPLOAD_VIDEO_ID="$(python3 - <<PY
import json
from pathlib import Path
p = Path(r'''$receipt_file''')
d = json.loads(p.read_text(encoding='utf-8'))
print(d.get('videoId',''))
PY
)"
    YOUTUBE_UPLOAD_PRIVACY="$(python3 - <<PY
import json
from pathlib import Path
p = Path(r'''$receipt_file''')
d = json.loads(p.read_text(encoding='utf-8'))
print(d.get('privacyStatus',''))
PY
)"
  fi
  {
    printf '[Daily Tech News 자동 실행 리포트]\n'
    printf -- '- 시작: %s\n' "$START_TS"
    printf -- '- 종료: %s\n' "$end_ts"
    printf -- '- 최종 상태: %s\n' "$FINAL_STATUS"
    if [ -n "$FINAL_NOTE" ]; then
      printf -- '- 메모: %s\n' "$FINAL_NOTE"
    fi
    if [ -n "$COLLECTED_COUNT" ]; then
      printf -- '- 수집 기사 수: %s건\n' "$COLLECTED_COUNT"
    fi
    if [ -n "$LATEST_COMMIT" ]; then
      printf -- '- 커밋: %s\n' "$LATEST_COMMIT"
    fi
    if [ -n "$YOUTUBE_UPLOAD_VIDEO_ID" ]; then
      printf -- '- 유튜브 videoId: %s\n' "$YOUTUBE_UPLOAD_VIDEO_ID"
    fi
    if [ -n "$YOUTUBE_UPLOAD_PRIVACY" ]; then
      printf -- '- 유튜브 공개상태: %s\n' "$YOUTUBE_UPLOAD_PRIVACY"
    fi
    if [ -n "$YOUTUBE_UPLOAD_URL" ]; then
      printf -- '- 유튜브 링크: %s\n' "$YOUTUBE_UPLOAD_URL"
    fi
    printf '\n[단계별 결과]\n'
    for item in "${STEP_RESULTS[@]}"; do
      local name="${item%%|*}"
      local status="${item##*|}"
      printf -- '- %s: %s\n' "$name" "$status"
    done
  } > "$REPORT_FILE"
  log "리포트 저장: $REPORT_FILE"
}

send_report() {
  local openclaw_bin
  openclaw_bin="$(command -v openclaw 2>/dev/null || true)"
  if [ -z "$openclaw_bin" ] && [ -x "/opt/homebrew/bin/openclaw" ]; then
    openclaw_bin="/opt/homebrew/bin/openclaw"
  fi
  if [ -z "$openclaw_bin" ]; then
    log "리포트 전송 스킵: openclaw CLI 없음"
    return 0
  fi

  local report_message
  report_message="$(cat "$REPORT_FILE")"
  if [ -z "$report_message" ]; then
    log "리포트 전송 스킵: 리포트 내용 비어 있음"
    return 0
  fi

  log "리포트 전송 시도: ${REPORT_CHANNEL}:${REPORT_TARGET}"
  if "$openclaw_bin" message send --channel "$REPORT_CHANNEL" --target "$REPORT_TARGET" --message "$report_message"; then
    log "리포트 전송 성공"
  else
    log "리포트 전송 실패"
  fi
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
    FINAL_STATUS="FAILED"
    FINAL_NOTE="$step_name 실패"
    log "$step_name 실패 - 필수 단계 실패로 중단"
    print_step_summary
    write_report
    send_report
    exit 1
  fi
}

run_optional_step() {
  local step_name="$1"
  shift

  log "$step_name"
  if "$@" 2>&1 | tee -a "$LOG_FILE"; then
    record_step_result "$step_name" "SUCCESS"
    log "$step_name 성공"
  else
    record_step_result "$step_name" "FAILED"
    OPTIONAL_FAILURES=1
    log "$step_name 실패 - 텍스트 발행은 유지하고 다음 단계로 진행"
  fi
}

run_required_step "Step 1: 뉴스 수집 및 HTML 생성" python3 generator2.py
STORY_PACK_PATH="archive/$(date '+%Y-%m-%d')-story-pack.json"
STORY_PACK_READY=0
log "Step 2: 유튜브 story pack 생성"
if python3 "$SCRIPT_DIR/story_pack.py" 2>&1 | tee -a "$LOG_FILE"; then
  if [ -f "$STORY_PACK_PATH" ]; then
    STORY_PACK_READY=1
    record_step_result "Step 2: 유튜브 story pack 생성" "SUCCESS"
    log "Step 2: 유튜브 story pack 생성 성공"
  else
    record_step_result "Step 2: 유튜브 story pack 생성" "FAILED"
    OPTIONAL_FAILURES=1
    log "Step 2: 유튜브 story pack 생성 실패 - 산출물 없음"
  fi
else
  record_step_result "Step 2: 유튜브 story pack 생성" "FAILED"
  OPTIONAL_FAILURES=1
  log "Step 2: 유튜브 story pack 생성 실패 - generic fallback 모드"
fi
run_optional_step "Step 3: 오디오 파이프라인" "$SCRIPT_DIR/run_audio_pipeline.sh"
run_optional_step "Step 4: 이미지 파이프라인" "$SCRIPT_DIR/run_image_pipeline.sh"

TODAY_STR="$(date '+%Y-%m-%d')"
VIDEO_PATH="archive/${TODAY_STR}.mp4"
YOUTUBE_METADATA_PATH="archive/${TODAY_STR}-youtube-metadata.json"
METADATA_READY=0

if ls archive/${TODAY_STR}-img-* >/dev/null 2>&1; then
  run_optional_step "Step 5: 비디오 파이프라인" "$SCRIPT_DIR/run_video_pipeline.sh"
else
  record_step_result "Step 5: 비디오 파이프라인" "SKIPPED"
  OPTIONAL_FAILURES=1
  log "Step 5: 비디오 파이프라인 스킵 - 오늘자 이미지가 없어 비디오를 만들지 않음"
fi

log "Step 6: 유튜브 메타데이터 생성"
if "$SCRIPT_DIR/run_youtube_metadata.sh" 2>&1 | tee -a "$LOG_FILE"; then
  if [ -f "$YOUTUBE_METADATA_PATH" ] && [ "$YOUTUBE_METADATA_PATH" -nt "$LOG_FILE" -o "$YOUTUBE_METADATA_PATH" -nt "$VIDEO_PATH" ]; then
    METADATA_READY=1
    record_step_result "Step 6: 유튜브 메타데이터 생성" "SUCCESS"
    log "Step 6: 유튜브 메타데이터 생성 성공"
  else
    record_step_result "Step 6: 유튜브 메타데이터 생성" "FAILED"
    OPTIONAL_FAILURES=1
    log "Step 6: 유튜브 메타데이터 생성 실패 - 오늘자 fresh metadata 확인 불가"
  fi
else
  record_step_result "Step 6: 유튜브 메타데이터 생성" "FAILED"
  OPTIONAL_FAILURES=1
  log "Step 6: 유튜브 메타데이터 생성 실패 - 유튜브 업로드는 차단"
fi

run_optional_step "Step 7: 썸네일 후보 생성" python3 "$SCRIPT_DIR/thumbnail_generator.py"

if [ -f "$VIDEO_PATH" ] && [ "$METADATA_READY" -eq 1 ]; then
  run_optional_step "Step 8: 유튜브 업로드" "$SCRIPT_DIR/run_youtube_upload.sh"
else
  record_step_result "Step 8: 유튜브 업로드" "SKIPPED"
  OPTIONAL_FAILURES=1
  log "Step 8: 유튜브 업로드 스킵 - mp4 또는 fresh metadata가 없음"
fi

log "Step 9: Git 변경사항 확인"
GIT_STATUS="$(git status --porcelain)"
if [ -z "$GIT_STATUS" ]; then
  record_step_result "Step 9: Git 변경사항 확인" "NO_CHANGES"
  FINAL_STATUS="SUCCESS"
  FINAL_NOTE="변경사항 없음"
  log "변경사항 없음. 작업 종료."
  print_step_summary
  write_report
  send_report
  exit 0
fi
record_step_result "Step 9: Git 변경사항 확인" "SUCCESS"
printf '%s\n' "$GIT_STATUS" | tee -a "$LOG_FILE"

ensure_secret_files_untracked() {
  git rm --cached --ignore-unmatch youtube_client_secret.json youtube_token.json youtube_client_secret.json.bak* youtube_token.json.bak* '*.oauth.bak' >/dev/null 2>&1 || true
}

log "Step 10: Git add"
ensure_secret_files_untracked
if git add -A . && git reset -- youtube_client_secret.json youtube_token.json youtube_client_secret.json.bak* youtube_token.json.bak* '*.oauth.bak' >/dev/null 2>&1 || git add -A .; then
  record_step_result "Step 10: Git add" "SUCCESS"
else
  record_step_result "Step 10: Git add" "FAILED"
  FINAL_STATUS="FAILED"
  FINAL_NOTE="Git add 실패"
  log "Git add 실패"
  print_step_summary
  write_report
  send_report
  exit 1
fi

log "Step 11: Git commit"
COMMIT_MESSAGE="Auto-update news - $(date '+%Y-%m-%d %H:%M')"
if git commit -m "$COMMIT_MESSAGE"; then
  record_step_result "Step 11: Git commit" "SUCCESS"
  LATEST_COMMIT="$(git rev-parse --short HEAD 2>/dev/null || true)"
  log "Git commit 성공: $COMMIT_MESSAGE"
else
  record_step_result "Step 11: Git commit" "FAILED"
  FINAL_STATUS="FAILED"
  FINAL_NOTE="Git commit 실패"
  log "Git commit 실패"
  print_step_summary
  write_report
  send_report
  exit 1
fi

log "Step 12: Git push"
if git push; then
  record_step_result "Step 12: Git push" "SUCCESS"
  if [ "$OPTIONAL_FAILURES" -eq 1 ]; then
    FINAL_STATUS="PARTIAL_SUCCESS"
    FINAL_NOTE="선택 단계 일부 실패"
  else
    FINAL_STATUS="SUCCESS"
    FINAL_NOTE="모든 작업 완료"
  fi
  log "Git push 성공"
else
  record_step_result "Step 12: Git push" "FAILED"
  FINAL_STATUS="FAILED"
  FINAL_NOTE="Git push 실패"
  log "Git push 실패"
  print_step_summary
  write_report
  send_report
  exit 1
fi

print_step_summary
write_report
send_report
log "SUCCESS: 모든 작업 완료"
log "=========================================="
