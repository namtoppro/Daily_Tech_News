#!/usr/bin/env python3
import shutil
print('=== VIDEO PROBE ===')
print('ffmpeg =', shutil.which('ffmpeg'))
print('ffprobe =', shutil.which('ffprobe'))
if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
    raise SystemExit('ffmpeg/ffprobe가 필요합니다.')
print('OK')
