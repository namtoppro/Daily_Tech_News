#!/usr/bin/env python3
from dotenv import dotenv_values

cfg = dotenv_values('.env')
print('=== TTS PROBE ===')
print('GEMINI_TTS_MODEL =', cfg.get('GEMINI_TTS_MODEL') or '(not set)')
print('STATUS = probe only; actual Gemini TTS integration pending SDK/model validation')
