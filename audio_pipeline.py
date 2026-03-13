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


def generate_audio_script(briefing_text: str) -> str:
    prompt = f"""
[Role]
너는 IT 뉴스 브리핑 전문 라디오 작가다.

[Objective]
아래 일간 기술 브리핑 문서를 바탕으로 2~4분 길이의 한국어 오디오 브리핑 대본을 작성하라.
NotebookLM 스타일처럼 자연스럽고 매끄럽지만, 과장되거나 잡담이 많으면 안 된다.

[Rules]
- 핵심 사실을 훼손하지 마라.
- 뉴스 3~5개 정도만 핵심 순서대로 압축해 전달하라.
- 너무 긴 제목 나열 금지
- 자연스럽게 연결하되 정보 밀도를 유지하라.
- 진행 톤은 차분한 브리핑형
- 선정적 과장 금지
- 맨 끝에 "이상 오늘의 기술 브리핑이었습니다."로 끝내라.
- Markdown 문법 없이 순수 대본 텍스트만 출력하라.

[Input]
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
