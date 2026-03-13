#!/bin/bash
set -euo pipefail

PLIST_SRC="$(cd "$(dirname "$0")" && pwd)/launchd/com.namtop.daily-tech-news.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.namtop.daily-tech-news.plist"
LABEL="com.namtop.daily-tech-news"

mkdir -p "$HOME/Library/LaunchAgents"
cp "$PLIST_SRC" "$PLIST_DST"
launchctl bootout "gui/$(id -u)/$LABEL" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_DST"
launchctl enable "gui/$(id -u)/$LABEL" >/dev/null 2>&1 || true
launchctl print "gui/$(id -u)/$LABEL"
