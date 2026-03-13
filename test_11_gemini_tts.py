#!/usr/bin/env python3
from pathlib import Path
from dotenv import dotenv_values
from google import genai
from google.genai import types
import base64

cfg = dotenv_values('.env')
api_key = cfg.get('GEMINI_API_KEY')
model = cfg.get('GEMINI_TTS_MODEL')
if not api_key:
    raise SystemExit('GEMINI_API_KEY가 없습니다.')
if not model:
    raise SystemExit('GEMINI_TTS_MODEL이 없습니다.')

client = genai.Client(api_key=api_key)
text = '안녕하세요. 이것은 Gemini TTS 연결 테스트입니다. 오디오 파일 생성 여부만 확인합니다.'

print('=== GEMINI TTS TEST ===')
print('MODEL =', model)

response = client.models.generate_content(
    model=model,
    contents=text,
    config=types.GenerateContentConfig(
        response_modalities=['AUDIO']
    )
)

print('RESPONSE_TYPE =', type(response).__name__)

candidates = getattr(response, 'candidates', None) or []
if not candidates:
    raise SystemExit('응답 candidates가 없습니다.')

parts = []
for cand in candidates:
    content = getattr(cand, 'content', None)
    if not content:
        continue
    for part in getattr(content, 'parts', []) or []:
        parts.append(part)

if not parts:
    raise SystemExit('응답 parts가 없습니다.')

saved = False
for idx, part in enumerate(parts, start=1):
    inline_data = getattr(part, 'inline_data', None)
    if not inline_data:
        continue
    mime = getattr(inline_data, 'mime_type', None) or 'audio/wav'
    data = getattr(inline_data, 'data', None)
    if not data:
        continue
    raw = base64.b64decode(data) if isinstance(data, str) else data
    ext = '.wav'
    if 'mpeg' in mime or 'mp3' in mime:
        ext = '.mp3'
    elif 'wav' in mime:
        ext = '.wav'
    elif 'ogg' in mime:
        ext = '.ogg'
    out = Path(f'tts_probe_output{ext}')
    out.write_bytes(raw)
    print('SAVED =', out)
    print('MIME =', mime)
    print('BYTES =', len(raw))
    saved = True
    break

if not saved:
    print('RAW_PART_ATTRS =', [a for a in dir(parts[0]) if not a.startswith('_')][:80])
    raise SystemExit('오디오 inline_data를 찾지 못했습니다.')

print('OK')
