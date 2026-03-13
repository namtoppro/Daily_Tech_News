#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import os

checks = {
    'metadata_json': Path('archive/2026-03-13-youtube-metadata.json').exists(),
    'video_mp4': Path('archive/2026-03-13.mp4').exists(),
    'client_secret_env_or_file': bool(os.getenv('YOUTUBE_CLIENT_SECRET_FILE')) or Path('youtube_client_secret.json').exists(),
    'token_file': Path('youtube_token.json').exists(),
}

for k, v in checks.items():
    print(f'{k}={v}')
