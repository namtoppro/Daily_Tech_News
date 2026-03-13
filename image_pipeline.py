#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Image generation pipeline for Daily Tech News.
- Selects top stories from today's briefing
- Generates image prompts
- Creates images serially with rate-limit-aware pacing
"""

import os
import re
import time
import base64
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError

load_dotenv()

TODAY = datetime.now().strftime('%Y-%m-%d')
ARCHIVE_DIR = os.getenv('ARCHIVE_DIR', 'archive')
IMAGE_MODEL = os.getenv('GEMINI_IMAGE_MODEL', 'gemini-3.1-flash-image-preview')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
IMAGE_MAX_COUNT = int(os.getenv('IMAGE_MAX_COUNT', '6'))
IMAGE_SLEEP_SEC = int(os.getenv('IMAGE_SLEEP_SEC', '5'))
IMAGE_RETRY_COUNT = int(os.getenv('IMAGE_RETRY_COUNT', '2'))
IMAGE_RETRY_BACKOFF_SEC = int(os.getenv('IMAGE_RETRY_BACKOFF_SEC', '8'))

if not GEMINI_API_KEY:
    raise RuntimeError('GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.')

client = genai.Client(api_key=GEMINI_API_KEY)


def load_briefing() -> str:
    p = Path('post.md')
    if not p.exists():
        raise RuntimeError('post.md가 없습니다. 먼저 텍스트 발행을 완료하세요.')
    return p.read_text(encoding='utf-8', errors='replace')


def extract_story_blocks(text: str):
    blocks = []
    pattern = re.compile(r'^###\s+\d+\.\s+(.+)$', re.MULTILINE)
    matches = list(pattern.finditer(text))
    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else text.find('## 오늘의 인사이트') if '## 오늘의 인사이트' in text[start:] else len(text)
        body = text[start:end].strip()
        if title and body:
            blocks.append({'title': title, 'body': body})
    return blocks[:IMAGE_MAX_COUNT]


def generate_image_prompt(title: str, body: str) -> str:
    prompt = f"""
당신은 기술 뉴스용 시각 콘셉트 아티스트다.
아래 기사 내용을 바탕으로 뉴스 썸네일/배경용 이미지 프롬프트를 작성하라.

규칙:
- 실제 기사 핵심을 반영하되 텍스트를 이미지 안에 직접 넣지 마라.
- 로고, 워터마크, 과한 글자, 브랜드명 직접 표기 금지
- 선정적 표현 금지
- 뉴스 브리핑 영상 배경에 어울리는 고품질 시네마틱 정지 이미지
- 장면 설명 + 분위기 + 색감 + 구도 + 금지 요소 포함
- 출력은 프롬프트 문장만

제목:
{title}

기사 요약:
{body[:1200]}
"""
    response = client.models.generate_content(model=os.getenv('AUDIO_SCRIPT_MODEL', os.getenv('GEMINI_MODEL', 'gemini-3.1-pro-preview')), contents=prompt)
    return (response.text or '').strip()


def _generate_image_once(prompt: str):
    response = client.models.generate_content(
        model=IMAGE_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(response_modalities=['IMAGE'])
    )
    candidates = getattr(response, 'candidates', None) or []
    for cand in candidates:
        content = getattr(cand, 'content', None)
        if not content:
            continue
        for part in getattr(content, 'parts', []) or []:
            inline_data = getattr(part, 'inline_data', None)
            if not inline_data:
                continue
            mime = getattr(inline_data, 'mime_type', None) or 'image/png'
            data = getattr(inline_data, 'data', None)
            if not data:
                continue
            raw = base64.b64decode(data) if isinstance(data, str) else data
            return raw, mime
    raise RuntimeError('이미지 응답 inline_data를 찾지 못했습니다.')


def generate_image_bytes(prompt: str):
    last_error = None
    for attempt in range(1, IMAGE_RETRY_COUNT + 2):
        try:
            return _generate_image_once(prompt)
        except (ServerError, ClientError) as e:
            last_error = e
            msg = str(e)
            retryable = ('500' in msg or '429' in msg or 'INTERNAL' in msg or 'RESOURCE_EXHAUSTED' in msg)
            if not retryable or attempt > IMAGE_RETRY_COUNT + 0:
                break
            sleep_sec = IMAGE_RETRY_BACKOFF_SEC * attempt
            print(f'IMAGE_RETRY attempt={attempt} sleep={sleep_sec}s reason={e}')
            time.sleep(sleep_sec)
        except Exception as e:
            last_error = e
            break
    raise RuntimeError(f'이미지 생성 실패: {last_error}')


def save_image(raw: bytes, mime: str, idx: int) -> Path:
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    ext = '.png'
    if 'jpeg' in mime or 'jpg' in mime:
        ext = '.jpg'
    out = Path(ARCHIVE_DIR) / f'{TODAY}-img-{idx:02d}{ext}'
    out.write_bytes(raw)
    return out


def main():
    briefing = load_briefing()
    stories = extract_story_blocks(briefing)
    print(f'STORY_COUNT={len(stories)}')
    for idx, story in enumerate(stories, start=1):
        print(f'GENERATE_PROMPT {idx}: {story["title"]}')
        prompt = generate_image_prompt(story['title'], story['body'])
        prompt_path = Path(ARCHIVE_DIR) / f'{TODAY}-img-{idx:02d}-prompt.txt'
        prompt_path.write_text(prompt, encoding='utf-8')
        print(f'PROMPT_SAVED={prompt_path}')
        try:
            raw, mime = generate_image_bytes(prompt)
            out = save_image(raw, mime, idx)
            print(f'IMAGE_SAVED={out} mime={mime} bytes={len(raw)}')
        except Exception as e:
            print(f'IMAGE_FAILED idx={idx} error={e}')
        if idx < len(stories):
            time.sleep(IMAGE_SLEEP_SEC)


if __name__ == '__main__':
    main()
