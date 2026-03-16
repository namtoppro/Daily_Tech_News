#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube metadata generator for Daily Tech News.
- Reads today's briefing/post and YouTube rules
- Generates title, description, and metadata json files
- Keeps upload preparation isolated from video upload itself
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google import genai

load_dotenv()

TODAY = datetime.now().strftime('%Y-%m-%d')
ARCHIVE_DIR = Path(os.getenv('ARCHIVE_DIR', 'archive'))
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
YOUTUBE_METADATA_MODEL = os.getenv('YOUTUBE_METADATA_MODEL', os.getenv('GEMINI_MODEL', 'gemini-3.1-pro-preview'))
DEFAULT_PRIVACY = os.getenv('YOUTUBE_DEFAULT_PRIVACY', 'private').strip().lower() or 'private'

if not GEMINI_API_KEY:
    raise RuntimeError('GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.')

client = genai.Client(api_key=GEMINI_API_KEY)


def ai_generate(prompt: str) -> str:
    response = client.models.generate_content(model=YOUTUBE_METADATA_MODEL, contents=prompt)
    return (response.text or '').strip()


def read_required_text(path: Path, error_message: str) -> str:
    if not path.exists():
        raise RuntimeError(error_message)
    return path.read_text(encoding='utf-8', errors='replace').strip()


def load_context() -> dict:
    post_path = Path('post.md')
    archive_md_path = ARCHIVE_DIR / f'{TODAY}.md'
    audio_script_path = ARCHIVE_DIR / f'{TODAY}-audio-script.md'
    video_path = ARCHIVE_DIR / f'{TODAY}.mp4'
    rules_path = Path('YOUTUBE_RULES.md')

    post_text = read_required_text(post_path, 'post.md가 없습니다. 먼저 텍스트 브리핑을 생성하세요.')
    archive_text = read_required_text(archive_md_path, f'{archive_md_path} 파일이 없습니다.')
    rules_text = read_required_text(rules_path, 'YOUTUBE_RULES.md가 없습니다.')
    audio_script_text = audio_script_path.read_text(encoding='utf-8', errors='replace').strip() if audio_script_path.exists() else ''

    return {
        'post_path': str(post_path),
        'archive_md_path': str(archive_md_path),
        'audio_script_path': str(audio_script_path),
        'video_path': str(video_path),
        'rules_text': rules_text,
        'post_text': post_text,
        'archive_text': archive_text,
        'audio_script_text': audio_script_text,
        'video_exists': video_path.exists(),
    }


def extract_json_block(text: str) -> dict:
    cleaned = text.strip()
    cleaned = cleaned.replace('```json', '').replace('```', '').strip()
    start = cleaned.find('{')
    end = cleaned.rfind('}')
    if start == -1 or end == -1 or end <= start:
        raise RuntimeError('AI 응답에서 JSON 객체를 찾지 못했습니다.')
    return json.loads(cleaned[start:end + 1])


def normalize_hashtags(items) -> list[str]:
    result = []
    for item in items or []:
        item = str(item).strip()
        if not item:
            continue
        if item.startswith('http://') or item.startswith('https://'):
            result.append(item)
            continue
        if not item.startswith('#'):
            item = '#' + item.lstrip('#')
        result.append(item)
    deduped = []
    seen = set()
    for item in result:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def ensure_brand_hashtags(hashtags: list[str]) -> list[str]:
    required = ['https://lowprice.koreall.site/', '#로프리', '#청담랩']
    merged = []
    seen = set()
    for item in required + hashtags:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
    return merged


def build_prompt(context: dict) -> str:
    return f"""
[System Role]
너는 Daily Tech News의 유튜브 편집 데스크다.
목표는 클릭베이트가 아니라 정보형·검색형 제목과 설명문을 만드는 것이다.

[Must Follow Rules]
{context['rules_text']}

[Task]
아래 입력을 바탕으로 오늘 영상의 유튜브 메타데이터를 생성하라.
반드시 JSON 객체 하나만 출력하라. 코드블록 없이 출력하라.

[Output JSON Schema]
{{
  "title": "string",
  "description": "string",
  "hashtags": ["string", "string"],
  "keywords": ["string", "string"],
  "privacyStatus": "private",
  "category": "Science & Technology",
  "playlistSuggestion": "string",
  "videoFile": "string",
  "sourceFiles": ["string", "string"],
  "notes": "string"
}}

[Output Rules]
- title: 한국어 제목 1개만
- description: 실제 유튜브 설명문 완성본
- hashtags: 브랜드 태그 + 일반 탐색 태그 포함
- keywords: 검색용 키워드 5~10개
- privacyStatus: 기본값은 {DEFAULT_PRIVACY}
- category: 기본값은 반드시 `Science & Technology`
- playlistSuggestion: 없으면 `Daily Tech News`
- videoFile: {context['video_path']}
- sourceFiles: 실제 사용한 입력 파일 경로
- notes: 한 줄 메모

[Hard Constraints]
- 제목 과장 금지
- 본문에 없는 주장 금지
- 브랜드 태그 `#로프리`, `#청담랩` 포함
- 링크 `https://lowprice.koreall.site/` 포함
- 설명문에는 오늘 핵심 이슈 3~5개를 bullet로 포함
- 설명문 첫 두 줄 안에 영상 성격이 드러나야 함

[Primary Input: post.md]
{context['post_text']}

[Secondary Input: archive markdown]
{context['archive_text']}

[Optional Audio Script]
{context['audio_script_text'] if context['audio_script_text'] else '(없음)'}
"""


def normalize_title(title: str) -> str:
    title = re.sub(r'\s+', ' ', title).strip()
    m = re.match(r'^\[(\d{4}-\d{2}-\d{2})\]\s*(.+)$', title)
    if m:
        date_part, rest = m.group(1), m.group(2).strip()
        if date_part not in rest:
            title = f'{rest} | {date_part}'
    return title


def generate_metadata(context: dict) -> dict:
    raw = ai_generate(build_prompt(context))
    data = extract_json_block(raw)

    title = str(data.get('title', '')).strip()
    if not title:
        raise RuntimeError('생성된 제목이 비어 있습니다.')
    title = normalize_title(title)

    description = str(data.get('description', '')).strip()
    if not description:
        raise RuntimeError('생성된 설명문이 비어 있습니다.')

    hashtags = ensure_brand_hashtags(normalize_hashtags(data.get('hashtags', [])))
    keywords = [str(x).strip() for x in data.get('keywords', []) if str(x).strip()]
    if not keywords:
        keywords = ['AI', 'Tech News', 'Daily Tech News', '인공지능', '기술뉴스']

    privacy = str(data.get('privacyStatus', DEFAULT_PRIVACY)).strip().lower()
    if privacy not in {'private', 'unlisted', 'public'}:
        privacy = DEFAULT_PRIVACY

    category = str(data.get('category', 'Science & Technology')).strip() or 'Science & Technology'
    playlist = str(data.get('playlistSuggestion', 'Daily Tech News')).strip() or 'Daily Tech News'
    notes = str(data.get('notes', '')).strip()

    if 'https://lowprice.koreall.site/' not in description:
        description = description.rstrip() + '\n\nhttps://lowprice.koreall.site/'

    for tag in ['#로프리', '#청담랩']:
        if tag not in description:
            description = description.rstrip() + f'\n{tag}'

    metadata = {
        'date': TODAY,
        'title': title,
        'description': description.strip(),
        'hashtags': hashtags,
        'keywords': keywords,
        'privacyStatus': privacy,
        'category': category,
        'playlistSuggestion': playlist,
        'videoFile': context['video_path'],
        'videoExists': context['video_exists'],
        'sourceFiles': [
            context['post_path'],
            context['archive_md_path'],
            context['audio_script_path'],
            'YOUTUBE_RULES.md',
        ],
        'notes': notes,
        'generatorModel': YOUTUBE_METADATA_MODEL,
    }
    return metadata


def save_outputs(metadata: dict) -> tuple[Path, Path, Path]:
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    title_path = ARCHIVE_DIR / f'{TODAY}-youtube-title.txt'
    desc_path = ARCHIVE_DIR / f'{TODAY}-youtube-description.txt'
    meta_path = ARCHIVE_DIR / f'{TODAY}-youtube-metadata.json'

    title_path.write_text(metadata['title'] + '\n', encoding='utf-8')
    desc_path.write_text(metadata['description'].rstrip() + '\n', encoding='utf-8')
    meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return title_path, desc_path, meta_path


def main():
    context = load_context()
    metadata = generate_metadata(context)
    title_path, desc_path, meta_path = save_outputs(metadata)
    print(f'YOUTUBE_TITLE={title_path}')
    print(f'YOUTUBE_DESCRIPTION={desc_path}')
    print(f'YOUTUBE_METADATA={meta_path}')
    print(f'VIDEO_EXISTS={metadata["videoExists"]}')
    print(f'PRIVACY={metadata["privacyStatus"]}')


if __name__ == '__main__':
    main()
