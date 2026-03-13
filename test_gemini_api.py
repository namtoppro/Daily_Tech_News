#!/usr/bin/env python3
from dotenv import dotenv_values
from google import genai

cfg = dotenv_values('.env')
api_key = cfg.get('GEMINI_API_KEY')
model = cfg.get('GEMINI_MODEL', 'gemini-3.1-pro-preview')

if not api_key:
    raise SystemExit('GEMINI_API_KEY가 .env에 없습니다.')

client = genai.Client(api_key=api_key)
response = client.models.generate_content(
    model=model,
    contents='간단한 연결 테스트입니다. 응답이 정상이면 OK 한 줄만 출력하세요.'
)

print('MODEL =', model)
print('RESPONSE =')
print((response.text or '').strip())
