#!/usr/bin/env python3
from generator2 import fetch_news_data, generate_html_content

print('=== HTML GENERATION TEST ===')
news = fetch_news_data()
if not news:
    raise SystemExit('RSS 수집 결과가 없어 HTML 생성 테스트 불가')
html = generate_html_content(news[:8])
print('HTML_LENGTH =', len(html))
print(html[:500])
if '<html' not in html.lower() or '</html>' not in html.lower():
    raise SystemExit('생성된 HTML 형식이 올바르지 않습니다.')
print('OK')
