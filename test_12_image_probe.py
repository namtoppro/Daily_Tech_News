#!/usr/bin/env python3
from dotenv import dotenv_values
cfg = dotenv_values('.env')
print('=== IMAGE PROBE ===')
print('GEMINI_IMAGE_MODEL =', cfg.get('GEMINI_IMAGE_MODEL'))
print('IMAGE_MAX_COUNT =', cfg.get('IMAGE_MAX_COUNT', '6'))
print('IMAGE_SLEEP_SEC =', cfg.get('IMAGE_SLEEP_SEC', '5'))
print('IMAGE_RETRY_COUNT =', cfg.get('IMAGE_RETRY_COUNT', '2'))
print('IMAGE_RETRY_BACKOFF_SEC =', cfg.get('IMAGE_RETRY_BACKOFF_SEC', '8'))
print('STATUS = probe only; serial generation with rate-limit awareness enabled in image_pipeline.py')
