#!/usr/bin/env python3
from audio_pipeline import load_today_briefing, generate_audio_script, save_audio_script, generate_tts_wav

print('=== AUDIO PIPELINE TEST ===')
briefing = load_today_briefing()
script = generate_audio_script(briefing)
script_out = save_audio_script(script)
print('SCRIPT_OUT =', script_out)
print('SCRIPT_LEN =', len(script))
audio_out = generate_tts_wav(script)
print('AUDIO_OUT =', audio_out)
print('OK')
