#!/usr/bin/env python3
from video_pipeline import get_audio_file, get_images, build_video

print('=== VIDEO GENERATION TEST ===')
audio = get_audio_file()
images = get_images()
out, per_image, duration, concat_file = build_video(audio, images)
print('AUDIO =', audio)
print('IMAGE_COUNT =', len(images))
print('DURATION =', duration)
print('PER_IMAGE =', per_image)
print('CONCAT =', concat_file)
print('VIDEO_OUT =', out)
print('OK')
