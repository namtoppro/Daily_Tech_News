#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video pipeline for Daily Tech News.
- Uses today's generated images + today's audio
- Builds a simple slideshow mp4 using ffmpeg
"""

import os
import math
import subprocess
from datetime import datetime
from pathlib import Path

TODAY = datetime.now().strftime('%Y-%m-%d')
ARCHIVE_DIR = Path(os.getenv('ARCHIVE_DIR', 'archive'))
VIDEO_WIDTH = int(os.getenv('VIDEO_WIDTH', '1280'))
VIDEO_HEIGHT = int(os.getenv('VIDEO_HEIGHT', '720'))
VIDEO_FPS = int(os.getenv('VIDEO_FPS', '30'))


def get_audio_file() -> Path:
    candidates = [ARCHIVE_DIR / f'{TODAY}.wav', ARCHIVE_DIR / f'{TODAY}.mp3', ARCHIVE_DIR / f'{TODAY}.ogg']
    for c in candidates:
        if c.exists():
            return c
    raise RuntimeError('오늘자 오디오 파일이 없습니다.')


def get_images():
    images = sorted(ARCHIVE_DIR.glob(f'{TODAY}-img-*.*'))
    images = [p for p in images if p.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp'} and '-prompt' not in p.name]
    if not images:
        raise RuntimeError('오늘자 이미지가 없습니다.')
    return images


def get_audio_duration(audio_path: Path) -> float:
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(audio_path)]
    out = subprocess.check_output(cmd, text=True).strip()
    return float(out)


def make_concat_file(images, per_image_sec: float) -> Path:
    concat_path = ARCHIVE_DIR / f'{TODAY}-slideshow.txt'
    lines = []
    for img in images:
        lines.append(f"file '{img.name}'")
        lines.append(f'duration {per_image_sec:.3f}')
    lines.append(f"file '{images[-1].name}'")
    concat_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return concat_path


def build_video(audio_path: Path, images):
    duration = get_audio_duration(audio_path)
    per_image = max(5.0, duration / max(1, len(images)))
    concat_file = make_concat_file(images, per_image)
    output = ARCHIVE_DIR / f'{TODAY}.mp4'

    cmd = [
        'ffmpeg', '-y',
        '-f', 'concat', '-safe', '0', '-i', str(concat_file),
        '-i', str(audio_path),
        '-vf', f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
        '-r', str(VIDEO_FPS),
        '-c:v', 'libx264',
        '-preset', 'veryfast',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        str(output),
    ]
    subprocess.check_call(cmd)
    return output, per_image, duration, concat_file


def main():
    audio = get_audio_file()
    images = get_images()
    output, per_image, duration, concat_file = build_video(audio, images)
    print(f'AUDIO={audio}')
    print(f'IMAGE_COUNT={len(images)}')
    print(f'DURATION={duration:.2f}')
    print(f'PER_IMAGE_SEC={per_image:.2f}')
    print(f'CONCAT_FILE={concat_file}')
    print(f'VIDEO_OUT={output}')


if __name__ == '__main__':
    main()
