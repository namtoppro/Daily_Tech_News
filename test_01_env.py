#!/usr/bin/env python3
from dotenv import dotenv_values

cfg = dotenv_values('.env')
required = ['GEMINI_API_KEY', 'GEMINI_MODEL', 'ARCHIVE_DIR']
print('=== ENV CHECK ===')
for key in required:
    val = cfg.get(key)
    if key == 'GEMINI_API_KEY':
        print(f'{key}:', 'SET' if val else 'MISSING')
    else:
        print(f'{key}:', val or 'MISSING')

missing = [k for k in required if not cfg.get(k)]
if missing:
    raise SystemExit(f'누락된 환경변수: {", ".join(missing)}')
print('OK')
