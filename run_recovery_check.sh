#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/$(date +%F)-recovery.log"
REPORT_CHANNEL="${REPORT_CHANNEL:-telegram}"
REPORT_TARGET="${REPORT_TARGET:-5548753399}"
TODAY="$(date +%F)"
ARCHIVE_DIR="$SCRIPT_DIR/archive"
REPORT_FILE="$LOG_DIR/${TODAY}-report.txt"
UPLOAD_RECEIPT="$ARCHIVE_DIR/${TODAY}-youtube-upload.json"
META_FILE="$ARCHIVE_DIR/${TODAY}-youtube-metadata.json"
MP4_FILE="$ARCHIVE_DIR/${TODAY}.mp4"
mkdir -p "$LOG_DIR"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

log() {
  local msg="$1"
  printf '%s - %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$msg" | tee -a "$LOG_FILE"
}

send_message() {
  local text="$1"
  local openclaw_bin
  openclaw_bin="$(command -v openclaw 2>/dev/null || true)"
  if [ -z "$openclaw_bin" ] && [ -x "/opt/homebrew/bin/openclaw" ]; then
    openclaw_bin="/opt/homebrew/bin/openclaw"
  fi
  if [ -z "$openclaw_bin" ]; then
    log "알림 전송 스킵: openclaw CLI 없음"
    return 0
  fi
  "$openclaw_bin" message send --channel "$REPORT_CHANNEL" --target "$REPORT_TARGET" --message "$text" || log "알림 전송 실패"
}

read_json_field() {
  local file="$1"
  local field="$2"
  python3 - <<PY
import json
from pathlib import Path
p = Path(r'''$file''')
if not p.exists():
    print('')
else:
    d = json.loads(p.read_text(encoding='utf-8'))
    print(d.get('$field',''))
PY
}

status_text() {
  if [ ! -f "$REPORT_FILE" ]; then
    echo "MISSING"
    return
  fi
  grep '^- 최종 상태:' "$REPORT_FILE" | tail -n 1 | sed 's/^- 최종 상태: *//' || true
}

needs_repair=0
repair_reason=()

log "=========================================="
log "Daily Tech News 8:30 recovery check start"
log "작업 디렉터리: $SCRIPT_DIR"
log "=========================================="

if [ ! -f "$REPORT_FILE" ]; then
  needs_repair=1
  repair_reason+=("리포트 없음")
fi

FINAL_STATUS="$(status_text)"
if [ "$FINAL_STATUS" = "FAILED" ] || [ "$FINAL_STATUS" = "PARTIAL_SUCCESS" ] || [ "$FINAL_STATUS" = "MISSING" ]; then
  needs_repair=1
  repair_reason+=("최종 상태=${FINAL_STATUS}")
fi

if [ ! -f "$MP4_FILE" ]; then
  needs_repair=1
  repair_reason+=("mp4 없음")
fi

if [ ! -f "$META_FILE" ]; then
  needs_repair=1
  repair_reason+=("metadata 없음")
fi

if [ ! -f "$UPLOAD_RECEIPT" ]; then
  needs_repair=1
  repair_reason+=("업로드 receipt 없음")
else
  UPLOAD_PRIVACY="$(read_json_field "$UPLOAD_RECEIPT" privacyStatus)"
  UPLOAD_URL="$(read_json_field "$UPLOAD_RECEIPT" url)"
  if [ "$UPLOAD_PRIVACY" != "public" ]; then
    needs_repair=1
    repair_reason+=("업로드 공개상태=${UPLOAD_PRIVACY}")
  fi
  if [ -z "$UPLOAD_URL" ]; then
    needs_repair=1
    repair_reason+=("업로드 URL 없음")
  fi
fi

if [ "$needs_repair" -eq 0 ]; then
  log "복구 필요 없음 - 오늘 작업 정상"
  send_message "[Daily Tech News 8:30 점검]\n- 상태: 정상\n- 최종 상태: ${FINAL_STATUS}\n- mp4: 있음\n- 업로드: public 정상\n- 추가 조치: 없음"
  exit 0
fi

log "복구 필요 감지: ${repair_reason[*]}"

cd "$SCRIPT_DIR"
if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

if [ ! -f "post.md" ] || [ ! -f "$ARCHIVE_DIR/${TODAY}.md" ]; then
  log "텍스트 기반 산출물 부족 - 전체 파이프라인 재실행"
  bash "$SCRIPT_DIR/run_daily_news.sh" 2>&1 | tee -a "$LOG_FILE"
else
  if [ ! -f "$MP4_FILE" ]; then
    log "mp4 없음 - 비디오 파이프라인 재실행"
    bash "$SCRIPT_DIR/run_video_pipeline.sh" 2>&1 | tee -a "$LOG_FILE" || true
  fi

  if [ ! -f "$META_FILE" ] || [ ! -f "$MP4_FILE" ]; then
    log "metadata 재생성"
    zsh "$SCRIPT_DIR/run_youtube_metadata.sh" 2>&1 | tee -a "$LOG_FILE" || true
  fi

  CURRENT_PRIVACY=""
  CURRENT_URL=""
  if [ -f "$UPLOAD_RECEIPT" ]; then
    CURRENT_PRIVACY="$(read_json_field "$UPLOAD_RECEIPT" privacyStatus)"
    CURRENT_URL="$(read_json_field "$UPLOAD_RECEIPT" url)"
  fi

  if [ ! -f "$UPLOAD_RECEIPT" ] || [ "$CURRENT_PRIVACY" != "public" ] || [ -z "$CURRENT_URL" ]; then
    log "유튜브 업로드 재실행"
    zsh "$SCRIPT_DIR/run_youtube_upload.sh" 2>&1 | tee -a "$LOG_FILE" || true
  fi
fi

POST_STATUS="$(status_text)"
POST_PRIVACY=""
POST_URL=""
POST_VIDEO_ID=""
if [ -f "$UPLOAD_RECEIPT" ]; then
  POST_PRIVACY="$(read_json_field "$UPLOAD_RECEIPT" privacyStatus)"
  POST_URL="$(read_json_field "$UPLOAD_RECEIPT" url)"
  POST_VIDEO_ID="$(read_json_field "$UPLOAD_RECEIPT" videoId)"
fi

if [ -f "$MP4_FILE" ] && [ "$POST_PRIVACY" = "public" ] && [ -n "$POST_URL" ]; then
  log "복구 결과 정상"
  send_message "[Daily Tech News 8:30 복구]\n- 상태: 복구 완료\n- 원인: ${repair_reason[*]}\n- mp4: 복구됨\n- videoId: ${POST_VIDEO_ID}\n- 링크: ${POST_URL}"
  exit 0
fi

log "복구 미완료"
send_message "[Daily Tech News 8:30 복구]\n- 상태: 미완료\n- 원인: ${repair_reason[*]}\n- mp4 존재: $( [ -f "$MP4_FILE" ] && echo yes || echo no )\n- 업로드 공개상태: ${POST_PRIVACY:-none}\n- 링크: ${POST_URL:-none}\n- 수동 확인 필요"
exit 1
