#!/bin/bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
PRIMARY_SRC="$BASE_DIR/launchd/com.namtop.daily-tech-news.plist"
PRIMARY_DST="$HOME/Library/LaunchAgents/com.namtop.daily-tech-news.plist"
PRIMARY_LABEL="com.namtop.daily-tech-news"
RECOVERY_SRC="$BASE_DIR/launchd/com.namtop.daily-tech-news-recovery.plist"
RECOVERY_DST="$HOME/Library/LaunchAgents/com.namtop.daily-tech-news-recovery.plist"
RECOVERY_LABEL="com.namtop.daily-tech-news-recovery"

mkdir -p "$HOME/Library/LaunchAgents"
cp "$PRIMARY_SRC" "$PRIMARY_DST"
cp "$RECOVERY_SRC" "$RECOVERY_DST"

launchctl bootout "gui/$(id -u)/$PRIMARY_LABEL" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$PRIMARY_DST"
launchctl enable "gui/$(id -u)/$PRIMARY_LABEL" >/dev/null 2>&1 || true

launchctl bootout "gui/$(id -u)/$RECOVERY_LABEL" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$RECOVERY_DST"
launchctl enable "gui/$(id -u)/$RECOVERY_LABEL" >/dev/null 2>&1 || true

launchctl print "gui/$(id -u)/$PRIMARY_LABEL"
printf '\n'
launchctl print "gui/$(id -u)/$RECOVERY_LABEL"
