#!/bin/bash
set -euo pipefail
cd "$(cd "$(dirname "$0")" && pwd)"
echo '=== GIT STATUS TEST ==='
git status --short
echo 'REMOTE:'
git remote -v
echo 'OK'
