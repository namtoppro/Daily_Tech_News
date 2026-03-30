#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Tech News YouTube story pack generator.
- Builds a YouTube-oriented narrative layer from today's briefing
- Keeps web/news briefing and YouTube packaging separated
- Outputs title/hook/thumbnail candidates + narrative skeleton
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google import genai

load_dotenv()

TODAY = datetime.now().strftime('%Y-%m-%d')
ARCHIVE_DIR = Path(os.getenv('ARCHIVE_DIR', 'archive'))
STORY_PACK_MODEL = os.getenv('STORY_PACK_MODEL', os.getenv('GEMINI_MODEL', 'gemini-3.1-pro-preview'))
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    raise RuntimeError('GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.')

client = genai.Client(api_key=GEMINI_API_KEY)


def ai_generate(prompt: str) -> str:
    response = client.models.generate_content(model=STORY_PACK_MODEL, contents=prompt)
    return (response.text or '').strip()


def read_required_text(path: Path, error_message: str) -> str:
    if not path.exists():
        raise RuntimeError(error_message)
    return path.read_text(encoding='utf-8', errors='replace').strip()


def extract_json_block(text: str) -> dict:
    cleaned = text.strip().replace('```json', '').replace('```', '').strip()
    start = cleaned.find('{')
    end = cleaned.rfind('}')
    if start == -1 or end == -1 or end <= start:
        raise RuntimeError('AI 응답에서 JSON 객체를 찾지 못했습니다.')
    return json.loads(cleaned[start:end + 1])


def load_inputs() -> dict:
    post_path = Path('post.md')
    archive_md_path = ARCHIVE_DIR / f'{TODAY}.md'
    youtube_rules_path = Path('YOUTUBE_RULES.md')

    return {
        'post_path': str(post_path),
        'archive_md_path': str(archive_md_path),
        'rules_path': str(youtube_rules_path),
        'post_text': read_required_text(post_path, 'post.md가 없습니다. 먼저 텍스트 브리핑을 생성하세요.'),
        'archive_text': read_required_text(archive_md_path, f'{archive_md_path} 파일이 없습니다.'),
        'rules_text': read_required_text(youtube_rules_path, 'YOUTUBE_RULES.md가 없습니다.'),
    }


def build_prompt(context: dict) -> str:
    return f"""
[Role]
너는 Daily Tech News의 유튜브 편집 데스크이자 테크 뉴스 내러티브 프로듀서다.
웹 브리핑용 요약을 다시 유튜브용 이야기 상품으로 재패키징해야 한다.

[Mission]
아래 Daily Tech News 브리핑을 바탕으로, 오늘 영상에서 전면에 내세울 메인 이슈 1개와 보조 이슈를 뽑아
YouTube용 story pack JSON을 만들어라.

[Must Follow]
{context['rules_text']}

[Important]
- 브리핑 기사 전체를 균등 나열하지 마라.
- 오늘 영상의 중심이 될 메인 이슈 1개를 강하게 고른다.
- 나머지는 supporting issue로 제한한다.
- 클릭베이트 금지. 하지만 브리핑형/날짜형 제목 반복도 금지.
- 핵심은 '무슨 일이 있었는지'보다 '왜 지금 봐야 하는지'를 만드는 것이다.
- 유튜브용 재료를 만드는 단계이지, 최종 대본 전체를 장문으로 쓰는 단계가 아니다.

[Output JSON Schema]
{{
  "date": "{TODAY}",
  "main_issue": {{
    "title": "string",
    "angle": "string",
    "why_it_matters": "string",
    "key_facts": ["string", "string", "string"],
    "key_numbers": ["string", "string"],
    "source_articles": ["string", "string"]
  }},
  "supporting_issues": [
    {{
      "title": "string",
      "role": "supporting",
      "key_fact": "string",
      "source_articles": ["string"]
    }}
  ],
  "hook_candidates": ["string", "string", "string"],
  "title_candidates": ["string", "string", "string", "string", "string"],
  "thumbnail_copy_candidates": ["string", "string", "string"],
  "narrative": {{
    "hook": "string",
    "setup": "string",
    "fact_1": "string",
    "fact_2": "string",
    "fact_3": "string",
    "takeaway": "string"
  }},
  "packaging_notes": "string"
}}

[Hard Constraints]
- 반드시 JSON 객체 하나만 출력한다.
- title_candidates는 한국어 기준으로 출력한다.
- thumbnail_copy_candidates는 2~5단어 수준의 짧은 문구를 우선한다.
- supporting_issues는 최대 3개까지만 넣는다.
- key_facts는 중복 없이 구체적으로 쓴다.
- why_it_matters는 시청자가 지금 봐야 하는 이유가 드러나야 한다.

[Primary Input: post.md]
{context['post_text']}

[Secondary Input: archive markdown]
{context['archive_text']}
"""


def normalize_story_pack(data: dict, context: dict) -> dict:
    title_candidates = [str(x).strip() for x in data.get('title_candidates', []) if str(x).strip()]
    hook_candidates = [str(x).strip() for x in data.get('hook_candidates', []) if str(x).strip()]
    thumbnail_copy_candidates = [str(x).strip() for x in data.get('thumbnail_copy_candidates', []) if str(x).strip()]
    supporting_issues = data.get('supporting_issues', []) or []
    supporting_issues = supporting_issues[:3]

    return {
        'date': TODAY,
        'main_issue': data.get('main_issue', {}) or {},
        'supporting_issues': supporting_issues,
        'hook_candidates': hook_candidates[:3],
        'title_candidates': title_candidates[:5],
        'thumbnail_copy_candidates': thumbnail_copy_candidates[:3],
        'narrative': data.get('narrative', {}) or {},
        'packaging_notes': str(data.get('packaging_notes', '')).strip(),
        'sourceFiles': [context['post_path'], context['archive_md_path'], context['rules_path']],
        'generatorModel': STORY_PACK_MODEL,
    }


def save_story_pack(payload: dict) -> Path:
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    out = ARCHIVE_DIR / f'{TODAY}-story-pack.json'
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return out


def main() -> None:
    context = load_inputs()
    raw = ai_generate(build_prompt(context))
    payload = normalize_story_pack(extract_json_block(raw), context)
    out = save_story_pack(payload)
    print(f'STORY_PACK_SAVED={out}')
    print(f'MAIN_ISSUE={payload.get("main_issue", {}).get("title", "")}')
    print(f'TITLE_CANDIDATE_1={(payload.get("title_candidates") or [""])[0]}')


if __name__ == '__main__':
    main()
