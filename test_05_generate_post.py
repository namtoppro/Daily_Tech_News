#!/usr/bin/env python3
from generator2 import fetch_news_data, generate_post_markdown

print('=== POST MARKDOWN TEST ===')
news = fetch_news_data()
if not news:
    raise SystemExit('RSS 수집 결과가 없어 post 생성 테스트 불가')
md = generate_post_markdown(news[:8])
print('MD_LENGTH =', len(md))
print(md[:500])
if '# Tech Briefing - ' not in md:
    raise SystemExit('Markdown 헤더가 예상 형식과 다릅니다.')
print('OK')
