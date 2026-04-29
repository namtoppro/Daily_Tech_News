#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys

DATES = [
    '2026-03-13',
    '2026-03-16',
    '2026-04-10',
    '2026-04-27',
    '2026-04-28',
]

for day in DATES:
    print(f'=== UPLOAD {day} ===', flush=True)
    result = subprocess.run([sys.executable, 'youtube_upload.py', '--date', day])
    if result.returncode != 0:
        sys.exit(result.returncode)
