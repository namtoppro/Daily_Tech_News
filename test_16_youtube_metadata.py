#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

TODAY_FILES = [
    Path('archive') / '2026-03-13-youtube-title.txt',
    Path('archive') / '2026-03-13-youtube-description.txt',
    Path('archive') / '2026-03-13-youtube-metadata.json',
]

for path in TODAY_FILES:
    print(f'{path}: {"OK" if path.exists() else "MISSING"}')
