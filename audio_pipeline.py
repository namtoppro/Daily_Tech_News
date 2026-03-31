#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audio extension pipeline for Daily Tech News.
- Generates notebooklm-style audio script from today's briefing
- Generates WAV audio via Gemini TTS when configured
- Fully isolated from text publishing pipeline
"""

import os
import base64
import wave
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

TODAY = datetime.now().strftime('%Y-%m-%d')
ARCHIVE_DIR = os.getenv('ARCHIVE_DIR', 'archive')
AUDIO_SCRIPT_MODEL = os.getenv('AUDIO_SCRIPT_MODEL', os.getenv('GEMINI_MODEL', 'gemini-3.1-pro-preview'))
AUDIO_TTS_MODEL = os.getenv('GEMINI_TTS_MODEL', '')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    raise RuntimeError('GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.')

client = genai.Client(api_key=GEMINI_API_KEY)


def ai_generate(model: str, prompt: str) -> str:
    response = client.models.generate_content(model=model, contents=prompt)
    return (response.text or '').strip()


def load_today_briefing() -> str:
    path = Path('post.md')
    if not path.exists():
        raise RuntimeError('post.md가 없습니다. 먼저 텍스트 발행을 완료하세요.')
    return path.read_text(encoding='utf-8', errors='replace')


def load_story_pack_text() -> str:
    path = Path(ARCHIVE_DIR) / f'{TODAY}-story-pack.json'
    if not path.exists():
        return ''
    return path.read_text(encoding='utf-8', errors='replace').strip()


HOOK_TEMPLATES = [
    '오늘 진짜 봐야 할 변화는 {core_change}입니다.',
    '지금 돈이 이동하는 곳은 {core_change}입니다.',
    '오늘 핵심은 {core_change}입니다.',
    '지금 시장이 가장 민감하게 반응하는 변화는 {core_change}입니다.',
    '이번 흐름의 본질은 {core_change}입니다.',
    '오늘 이슈의 중심은 {core_change}입니다.',
    '겉으로는 여러 뉴스가 보이지만, 실제 핵심은 {core_change}입니다.',
    '지금 테크 업계에서 가장 먼저 봐야 할 변화는 {core_change}입니다.',
    '이번 브리핑에서 놓치면 안 되는 포인트는 {core_change}입니다.',
    '오늘 시장이 돈과 관심을 함께 보내는 지점은 {core_change}입니다.',
]


def generate_audio_script(briefing_text: str) -> str:
    story_pack_text = load_story_pack_text()
    hook_templates_text = '\n'.join([f'- {item}' for item in HOOK_TEMPLATES])
    prompt = f"""
[Role]
너는 IT 뉴스 브리핑 전문 라디오 작가이자 유튜브용 테크 뉴스 진행자다.

[Objective]
아래 입력을 바탕으로 2~4분 길이의 한국어 오디오 브리핑 대본을 작성하라.
단순 뉴스 나열형이 아니라, hook-first 구조의 유튜브형 설명 대본이어야 한다.

[Priority]
1. story pack이 있으면 그것을 최우선 반영한다.
2. briefing 문서는 사실 확인/보강 용도로 쓴다.
3. 웹 브리핑 문장을 그대로 길게 낭독하지 마라.

[Required Structure]
- Hook: 첫 2문장 안에 오늘 가장 중요한 변화와 시청 이유를 넣는다.
- Setup: 왜 이 이슈를 지금 봐야 하는지 설명한다.
- Main facts: 핵심 사실 3개를 자연스럽게 연결한다.
- Takeaway: 오늘 흐름을 한 문장으로 정리한다.
- Ending: 맨 끝은 반드시 "이상 오늘의 기술 브리핑이었습니다."로 끝낸다.

[Rules]
- 핵심 사실을 훼손하지 마라.
- 메인 이슈 1개를 중심으로 말하고, 나머지는 보조 근거처럼 연결하라.
- 너무 긴 제목 나열 금지.
- 문장 길이는 짧고 낭독 가능하게 유지하라.
- 진행 톤은 차분하지만 첫 도입은 분명해야 한다.
- 첫 2문장은 단순 인사말보다, 시청자가 왜 지금 이 영상을 봐야 하는지 바로 느끼게 만들어라.
- 첫 문장 또는 둘째 문장에는 시장 변화, 사용자 영향, 비용 변화, 신뢰 문제 중 최소 1개를 직접 언급하라.
- 첫 문장은 아래 템플릿 중 하나의 구조를 반드시 따른다. 단, 표현은 입력 사실에 맞게 자연스럽게 채워라.
{hook_templates_text}
- 첫 문장은 반드시 마침표로 끝나는 완결된 한 문장으로 작성한다.
- 둘째 문장은 첫 문장의 의미를 풀어주되, 입력 출처가 수집된 기사/공식 발표라는 점을 자연스럽게 연결할 수 있다.
- 선정적 과장 금지.
- 입력은 수집된 원문 기사/공식 발표/브리핑 요약이다. 입력에 없는 사실, 숫자, 인과관계, 전망을 새로 만들지 마라.
- "AI가 분석한 결과"처럼 들리는 표현을 피하고, 사실 기반 정리 톤을 유지하라.
- 필요하면 "수집된 원문 기사와 공식 발표를 바탕으로"라는 취지의 문장을 자연스럽게 녹여도 된다.
- Markdown 문법 없이 순수 대본 텍스트만 출력하라.
- 오디오로 읽었을 때 어색한 괄호/불릿/기호 나열을 피하라.

[Optional Story Pack]
{story_pack_text if story_pack_text else '(없음)'}

[Briefing Input]
{briefing_text}
"""
    return ai_generate(AUDIO_SCRIPT_MODEL, prompt)


def save_audio_script(script: str) -> Path:
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    out = Path(ARCHIVE_DIR) / f'{TODAY}-audio-script.md'
    out.write_text(script, encoding='utf-8')
    return out


def generate_tts_wav(script: str) -> Path | None:
    if not AUDIO_TTS_MODEL:
        print('TTS_SKIP: GEMINI_TTS_MODEL not configured')
        return None

    response = client.models.generate_content(
        model=AUDIO_TTS_MODEL,
        contents=script,
        config=types.GenerateContentConfig(response_modalities=['AUDIO'])
    )

    candidates = getattr(response, 'candidates', None) or []
    if not candidates:
        raise RuntimeError('TTS 응답 candidates가 없습니다.')

    parts = []
    for cand in candidates:
        content = getattr(cand, 'content', None)
        if not content:
            continue
        for part in getattr(content, 'parts', []) or []:
            parts.append(part)

    if not parts:
        raise RuntimeError('TTS 응답 parts가 없습니다.')

    for part in parts:
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
            out = Path(ARCHIVE_DIR) / f'{TODAY}{ext}'
            out.write_bytes(raw)
            print(f'TTS_AUDIO_SAVED={out} mime={mime} bytes={len(raw)}')
            return out
        elif 'ogg' in mime:
            ext = '.ogg'
            out = Path(ARCHIVE_DIR) / f'{TODAY}{ext}'
            out.write_bytes(raw)
            print(f'TTS_AUDIO_SAVED={out} mime={mime} bytes={len(raw)}')
            return out
        elif 'wav' in mime or 'L16' in mime or 'pcm' in mime:
            out = Path(ARCHIVE_DIR) / f'{TODAY}.wav'
            with wave.open(str(out), 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                wf.writeframes(raw)
            print(f'TTS_AUDIO_SAVED={out} mime={mime} bytes={len(raw)} wrapped_as=wav')
            return out

    raise RuntimeError('TTS 오디오 inline_data를 찾지 못했습니다.')


def main():
    briefing = load_today_briefing()
    script = generate_audio_script(briefing)
    script_out = save_audio_script(script)
    print(f'AUDIO_SCRIPT_SAVED={script_out}')
    try:
        audio_out = generate_tts_wav(script)
        if audio_out:
            print(f'AUDIO_FILE_SAVED={audio_out}')
    except Exception as e:
        # Keep audio isolated from text/news publishing
        print(f'TTS_FAILED={e}')


if __name__ == '__main__':
    main()
