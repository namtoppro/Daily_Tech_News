#!/usr/bin/env python3
from image_pipeline import load_briefing, extract_story_blocks, generate_image_prompt, generate_image_bytes, save_image

print('=== IMAGE GENERATION TEST ===')
briefing = load_briefing()
stories = extract_story_blocks(briefing)
if not stories:
    raise SystemExit('스토리를 추출하지 못했습니다.')
story = stories[0]
print('TITLE =', story['title'])
prompt = generate_image_prompt(story['title'], story['body'])
print('PROMPT_PREVIEW =', prompt[:600])
raw, mime = generate_image_bytes(prompt)
out = save_image(raw, mime, 1)
print('IMAGE_OUT =', out)
print('MIME =', mime)
print('BYTES =', len(raw))
print('OK')
