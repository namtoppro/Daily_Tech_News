#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video pipeline for Daily Tech News.
- Uses today's generated images + today's audio
- Builds a more YouTube-friendly mp4 using ffmpeg
- Adds intro template, subtitle layer, keyword highlight cards, and closing CTA card
- Renders text overlays as PNG assets via Pillow, then composites with ffmpeg overlay filter
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

TODAY = datetime.now().strftime('%Y-%m-%d')
ARCHIVE_DIR = Path(os.getenv('ARCHIVE_DIR', 'archive'))
RENDER_DIR = ARCHIVE_DIR / '.render' / TODAY
VIDEO_WIDTH = int(os.getenv('VIDEO_WIDTH', '1280'))
VIDEO_HEIGHT = int(os.getenv('VIDEO_HEIGHT', '720'))
VIDEO_FPS = int(os.getenv('VIDEO_FPS', '30'))
VIDEO_MIN_PER_IMAGE_SEC = float(os.getenv('VIDEO_MIN_PER_IMAGE_SEC', '3.2'))
VIDEO_MAX_PER_IMAGE_SEC = float(os.getenv('VIDEO_MAX_PER_IMAGE_SEC', '6.0'))
VIDEO_INTRO_SEC = float(os.getenv('VIDEO_INTRO_SEC', '5.0'))
VIDEO_OUTRO_SEC = float(os.getenv('VIDEO_OUTRO_SEC', '4.0'))
VIDEO_CARD_SEC = float(os.getenv('VIDEO_CARD_SEC', '3.2'))
FFPROBE_BIN = os.getenv('FFPROBE_BIN') or shutil.which('ffprobe') or '/opt/homebrew/bin/ffprobe'
FFMPEG_BIN = os.getenv('FFMPEG_BIN') or shutil.which('ffmpeg') or '/opt/homebrew/bin/ffmpeg'
FONT_REGULAR = os.getenv('VIDEO_FONT_REGULAR', '/System/Library/Fonts/Supplemental/Arial.ttf')
FONT_BOLD = os.getenv('VIDEO_FONT_BOLD', '/System/Library/Fonts/Supplemental/Arial Bold.ttf')


def get_audio_file() -> Path:
    candidates = [ARCHIVE_DIR / f'{TODAY}.wav', ARCHIVE_DIR / f'{TODAY}.mp3', ARCHIVE_DIR / f'{TODAY}.ogg']
    for c in candidates:
        if c.exists():
            return c
    raise RuntimeError('오늘자 오디오 파일이 없습니다.')


def get_images() -> list[Path]:
    images = sorted(ARCHIVE_DIR.glob(f'{TODAY}-img-*.*'))
    images = [p for p in images if p.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp'} and '-prompt' not in p.name]
    if not images:
        raise RuntimeError('오늘자 이미지가 없습니다.')
    return images


def ensure_video_bins() -> None:
    missing = []
    if not Path(FFPROBE_BIN).exists():
        missing.append(f'ffprobe={FFPROBE_BIN}')
    if not Path(FFMPEG_BIN).exists():
        missing.append(f'ffmpeg={FFMPEG_BIN}')
    if missing:
        raise RuntimeError('필수 비디오 도구 없음: ' + ', '.join(missing))


def get_audio_duration(audio_path: Path) -> float:
    cmd = [FFPROBE_BIN, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(audio_path)]
    out = subprocess.check_output(cmd, text=True).strip()
    return float(out)


def load_audio_script() -> str:
    path = ARCHIVE_DIR / f'{TODAY}-audio-script.md'
    if not path.exists():
        return ''
    return path.read_text(encoding='utf-8', errors='replace').strip()


def load_story_pack() -> dict:
    path = ARCHIVE_DIR / f'{TODAY}-story-pack.json'
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8'))


def clean_text(text: str) -> str:
    text = re.sub(r'\*+', ' ', text or '')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def split_sentences(text: str) -> list[str]:
    text = clean_text(text)
    if not text:
        return []
    text = re.sub(r'([\.\!\?])\s+', r'\1\n', text)
    text = re.sub(r'(다\.)\s+', r'\1\n', text)
    return [p.strip(' .') for p in text.splitlines() if p.strip(' .')]


def prepare_render_dir() -> None:
    if RENDER_DIR.exists():
        shutil.rmtree(RENDER_DIR)
    RENDER_DIR.mkdir(parents=True, exist_ok=True)


def make_concat_file(images: list[Path], per_image_sec: float) -> Path:
    concat_path = RENDER_DIR / f'{TODAY}-slideshow.txt'
    lines = []
    for img in images:
        lines.append(f"file '{img.resolve()}'")
        lines.append(f'duration {per_image_sec:.3f}')
    lines.append(f"file '{images[-1].resolve()}'")
    concat_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return concat_path


def load_font(path: str, size: int):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    words = clean_text(text).split()
    if not words:
        return []
    lines = []
    current = words[0]
    for word in words[1:]:
        candidate = f'{current} {word}'
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def make_overlay_canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new('RGBA', (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 0))
    return image, ImageDraw.Draw(image)


def save_overlay(name: str, image: Image.Image) -> Path:
    out = RENDER_DIR / f'{TODAY}-{name}.png'
    image.save(out)
    return out


def create_intro_overlay(title: str, subtitle: str) -> Path:
    image, draw = make_overlay_canvas()
    draw.rectangle((0, 0, VIDEO_WIDTH, VIDEO_HEIGHT), fill=(0, 0, 0, 175))
    font_title = load_font(FONT_BOLD, 54)
    font_sub = load_font(FONT_REGULAR, 28)
    title_lines = wrap_text(draw, title, font_title, VIDEO_WIDTH - 200)
    sub_lines = wrap_text(draw, subtitle, font_sub, VIDEO_WIDTH - 260)
    y = 180
    for line in title_lines[:3]:
        bbox = draw.textbbox((0, 0), line, font=font_title)
        w = bbox[2] - bbox[0]
        draw.text(((VIDEO_WIDTH - w) / 2, y), line, font=font_title, fill=(255, 255, 255, 255))
        y += 70
    y += 20
    for line in sub_lines[:3]:
        bbox = draw.textbbox((0, 0), line, font=font_sub)
        w = bbox[2] - bbox[0]
        draw.rounded_rectangle((110, y - 14, VIDEO_WIDTH - 110, y + 34), radius=18, fill=(0, 0, 0, 92))
        draw.text(((VIDEO_WIDTH - w) / 2, y), line, font=font_sub, fill=(235, 241, 255, 255))
        y += 42
    return save_overlay('intro-overlay', image)


def create_keyword_overlay(text: str, idx: int) -> Path:
    image, draw = make_overlay_canvas()
    font = load_font(FONT_BOLD, 28)
    lines = wrap_text(draw, text, font, 640)
    box_h = 110 + max(0, len(lines) - 1) * 36
    draw.rounded_rectangle((36, 36, 760, 36 + box_h), radius=24, fill=(10, 15, 28, 180), outline=(56, 189, 248, 240), width=3)
    draw.rectangle((36, 36, 52, 36 + box_h), fill=(56, 189, 248, 255))
    y = 72
    for line in lines[:3]:
        draw.text((76, y), line, font=font, fill=(255, 255, 255, 255))
        y += 38
    return save_overlay(f'keyword-overlay-{idx:02d}', image)


def create_subtitle_overlay(text: str, idx: int) -> Path:
    image, draw = make_overlay_canvas()
    font = load_font(FONT_BOLD, 24)
    lines = wrap_text(draw, text, font, VIDEO_WIDTH - 240)
    box_h = 56 + max(0, len(lines) - 1) * 34
    top = VIDEO_HEIGHT - 54 - box_h
    draw.rounded_rectangle((90, top, VIDEO_WIDTH - 90, VIDEO_HEIGHT - 34), radius=20, fill=(0, 0, 0, 165))
    y = top + 18
    for line in lines[:3]:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        draw.text(((VIDEO_WIDTH - w) / 2, y), line, font=font, fill=(255, 255, 255, 255))
        y += 32
    return save_overlay(f'subtitle-overlay-{idx:03d}', image)


def create_outro_overlay(title: str, subtitle: str) -> Path:
    image, draw = make_overlay_canvas()
    draw.rectangle((0, 0, VIDEO_WIDTH, VIDEO_HEIGHT), fill=(0, 0, 0, 190))
    font_title = load_font(FONT_BOLD, 46)
    font_sub = load_font(FONT_REGULAR, 24)
    title_lines = wrap_text(draw, title, font_title, VIDEO_WIDTH - 220)
    sub_lines = wrap_text(draw, subtitle, font_sub, VIDEO_WIDTH - 260)
    y = 220
    for line in title_lines[:2]:
        bbox = draw.textbbox((0, 0), line, font=font_title)
        w = bbox[2] - bbox[0]
        draw.text(((VIDEO_WIDTH - w) / 2, y), line, font=font_title, fill=(255, 255, 255, 255))
        y += 60
    y += 18
    for line in sub_lines[:3]:
        bbox = draw.textbbox((0, 0), line, font=font_sub)
        w = bbox[2] - bbox[0]
        draw.text(((VIDEO_WIDTH - w) / 2, y), line, font=font_sub, fill=(230, 236, 245, 255))
        y += 34
    footer = 'lowprice.koreall.site'
    bbox = draw.textbbox((0, 0), footer, font=font_sub)
    w = bbox[2] - bbox[0]
    draw.text(((VIDEO_WIDTH - w) / 2, y + 24), footer, font=font_sub, fill=(125, 211, 252, 255))
    return save_overlay('outro-overlay', image)


def build_overlay_plan(duration: float, story_pack: dict, script: str) -> tuple[list[dict], str]:
    main_issue = story_pack.get('main_issue', {}) or {}
    narrative = story_pack.get('narrative', {}) or {}
    title_candidates = story_pack.get('title_candidates', []) or []

    intro_title = title_candidates[0] if title_candidates else main_issue.get('title', 'Daily Tech News')
    intro_sub = narrative.get('hook') or main_issue.get('why_it_matters') or '오늘 가장 중요한 기술 이슈를 빠르게 정리합니다.'
    mode = 'story-pack' if story_pack else 'generic'
    overlays = [
        {'path': create_intro_overlay(intro_title, intro_sub), 'start': 0.0, 'end': min(duration, VIDEO_INTRO_SEC), 'kind': 'intro'}
    ]

    card_texts = []
    for item in main_issue.get('key_facts', []) or []:
        cleaned = clean_text(str(item))
        if cleaned:
            card_texts.append(cleaned)
    if not card_texts:
        for key in ['setup', 'fact_1', 'fact_2', 'fact_3']:
            cleaned = clean_text(str(narrative.get(key, '')))
            if cleaned:
                card_texts.append(cleaned)
    if not story_pack:
        card_texts = []
    card_texts = card_texts[:3]

    usable_start = VIDEO_INTRO_SEC + 3.0
    usable_end = max(usable_start + VIDEO_CARD_SEC, duration - VIDEO_OUTRO_SEC - VIDEO_CARD_SEC)
    if card_texts:
        if len(card_texts) == 1:
            card_times = [max(usable_start, min(duration - VIDEO_OUTRO_SEC - VIDEO_CARD_SEC, duration * 0.38))]
        else:
            span = max(0.0, usable_end - usable_start)
            step = span / max(1, len(card_texts) - 1)
            card_times = [usable_start + step * idx for idx in range(len(card_texts))]
        for idx, text in enumerate(card_texts, start=1):
            start = card_times[idx - 1]
            overlays.append({'path': create_keyword_overlay(text, idx), 'start': start, 'end': min(duration - VIDEO_OUTRO_SEC - 0.2, start + VIDEO_CARD_SEC), 'kind': 'card'})

    sentences = split_sentences(script)
    if sentences:
        weights = [max(1, len(s.replace(' ', ''))) for s in sentences]
        total_weight = sum(weights)
        cursor = 0.0
        for idx, (sentence, weight) in enumerate(zip(sentences, weights), start=1):
            seg = duration * (weight / total_weight)
            if idx == len(sentences):
                end = duration
            else:
                end = min(duration, cursor + max(1.4, seg))
            overlays.append({'path': create_subtitle_overlay(sentence, idx), 'start': cursor, 'end': end, 'kind': 'subtitle'})
            cursor = end

    outro_start = max(0.0, duration - VIDEO_OUTRO_SEC)
    outro_sub = narrative.get('takeaway') or '더 자세한 내용은 설명란과 아카이브를 확인하세요.'
    overlays.append({'path': create_outro_overlay('Daily Tech News', outro_sub), 'start': outro_start, 'end': duration, 'kind': 'outro'})
    return overlays, mode


def build_filter_complex(overlays: list[dict]) -> str:
    chain = [f'[0:v]scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,format=rgba[v0]']
    current = 'v0'
    for idx, overlay in enumerate(overlays, start=2):
        next_label = f'v{idx-1}'
        start = overlay['start']
        end = overlay['end']
        chain.append(f'[{current}][{idx}:v]overlay=0:0:enable=between(t\\,{start:.2f}\\,{end:.2f})[{next_label}]')
        current = next_label
    chain.append(f'[{current}]format=yuv420p[vout]')
    return ';'.join(chain)


def build_video(audio_path: Path, images: list[Path]):
    prepare_render_dir()
    duration = get_audio_duration(audio_path)
    visual_window = max(1.0, duration)
    slideshow_window = max(1.0, visual_window - VIDEO_INTRO_SEC - VIDEO_OUTRO_SEC)
    per_image = min(VIDEO_MAX_PER_IMAGE_SEC, max(VIDEO_MIN_PER_IMAGE_SEC, slideshow_window / max(1, len(images))))
    concat_file = make_concat_file(images, per_image)
    script = load_audio_script()
    story_pack = load_story_pack()
    overlays, mode = build_overlay_plan(duration, story_pack, script)
    output = ARCHIVE_DIR / f'{TODAY}.mp4'

    cmd = [FFMPEG_BIN, '-y', '-f', 'concat', '-safe', '0', '-i', str(concat_file), '-i', str(audio_path)]
    for overlay in overlays:
        cmd.extend(['-loop', '1', '-i', str(overlay['path'])])
    cmd.extend([
        '-filter_complex', build_filter_complex(overlays),
        '-map', '[vout]',
        '-map', '1:a',
        '-r', str(VIDEO_FPS),
        '-c:v', 'libx264',
        '-preset', 'veryfast',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        str(output),
    ])
    subprocess.check_call(cmd)
    return output, per_image, duration, concat_file, overlays, mode


def main():
    ensure_video_bins()
    audio = get_audio_file()
    images = get_images()
    output, per_image, duration, concat_file, overlays, mode = build_video(audio, images)
    print(f'FFPROBE_BIN={FFPROBE_BIN}')
    print(f'FFMPEG_BIN={FFMPEG_BIN}')
    print(f'AUDIO={audio}')
    print(f'IMAGE_COUNT={len(images)}')
    print(f'DURATION={duration:.2f}')
    print(f'PER_IMAGE_SEC={per_image:.2f}')
    print(f'CONCAT_FILE={concat_file}')
    print(f'OVERLAY_COUNT={len(overlays)}')
    print(f'STORY_PACK_MODE={mode}')
    print(f'VIDEO_OUT={output}')


if __name__ == '__main__':
    main()
