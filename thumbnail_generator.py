#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube thumbnail candidate generator for Daily Tech News.
- Creates 2~3 thumbnail PNG candidates for manual review
- Uses story pack first, then metadata fallback
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

TODAY = datetime.now().strftime('%Y-%m-%d')
ARCHIVE_DIR = Path(os.getenv('ARCHIVE_DIR', 'archive'))
WIDTH = 1280
HEIGHT = 720
FONT_BOLD = os.getenv('VIDEO_FONT_BOLD', '/System/Library/Fonts/Supplemental/Arial Bold.ttf')
FONT_REGULAR = os.getenv('VIDEO_FONT_REGULAR', '/System/Library/Fonts/Supplemental/Arial.ttf')


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8'))


def clean(text: str) -> str:
    return ' '.join((text or '').split()).strip()


def font(path: str, size: int):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt, max_width: int) -> list[str]:
    words = clean(text).split()
    if not words:
        return []
    lines = []
    current = words[0]
    for word in words[1:]:
        candidate = f'{current} {word}'
        bbox = draw.textbbox((0, 0), candidate, font=fnt)
        if (bbox[2] - bbox[0]) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def collect_copy_candidates() -> list[str]:
    story_pack = load_json(ARCHIVE_DIR / f'{TODAY}-story-pack.json')
    metadata = load_json(ARCHIVE_DIR / f'{TODAY}-youtube-metadata.json')
    candidates = []
    for item in story_pack.get('thumbnail_copy_candidates', []) or []:
        item = clean(str(item))
        if item:
            candidates.append(item)
    main_title = clean((story_pack.get('main_issue', {}) or {}).get('title', ''))
    if main_title:
        candidates.append(main_title)
    title = clean(metadata.get('title', ''))
    if title:
        candidates.append(title)
    deduped = []
    seen = set()
    for item in candidates:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped[:3] or ['TODAY AI STORY', 'TECH SHIFT TODAY', 'WHAT CHANGED']


def make_background(idx: int) -> Image.Image:
    palettes = [
        ((7, 16, 29), (15, 23, 42), (56, 189, 248)),
        ((18, 12, 34), (30, 22, 60), (168, 85, 247)),
        ((15, 23, 42), (20, 83, 45), (34, 197, 94)),
    ]
    c1, c2, accent = palettes[(idx - 1) % len(palettes)]
    img = Image.new('RGB', (WIDTH, HEIGHT), c1)
    draw = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        ratio = y / max(1, HEIGHT - 1)
        color = tuple(int(c1[i] * (1 - ratio) + c2[i] * ratio) for i in range(3))
        draw.line((0, y, WIDTH, y), fill=color)
    draw.rounded_rectangle((72, 68, WIDTH - 72, HEIGHT - 68), radius=42, outline=accent, width=6)
    draw.rectangle((92, 94, 112, HEIGHT - 94), fill=accent)
    return img


def render_thumbnail(text: str, idx: int) -> Path:
    img = make_background(idx)
    draw = ImageDraw.Draw(img)
    big = font(FONT_BOLD, 84)
    small = font(FONT_REGULAR, 28)
    lines = wrap(draw, text, big, WIDTH - 220)
    lines = lines[:3]
    y = 170
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=big)
        draw.text((130, y), line, font=big, fill=(255, 255, 255))
        y += (bbox[3] - bbox[1]) + 18
    draw.text((132, HEIGHT - 130), 'DAILY TECH NEWS', font=small, fill=(125, 211, 252))
    draw.text((132, HEIGHT - 92), TODAY, font=small, fill=(226, 232, 240))
    out = ARCHIVE_DIR / f'{TODAY}-thumbnail-{idx:02d}.png'
    img.save(out)
    return out


def main() -> None:
    candidates = collect_copy_candidates()
    paths = []
    for idx, text in enumerate(candidates, start=1):
        (ARCHIVE_DIR / f'{TODAY}-thumbcopy-{idx:02d}.txt').write_text(text + '\n', encoding='utf-8')
        paths.append(render_thumbnail(text, idx))
    print(f'THUMBNAIL_COUNT={len(paths)}')
    for path in paths:
        print(f'THUMBNAIL_SAVED={path}')


if __name__ == '__main__':
    main()
