#!/usr/bin/env python3
from generator2 import fetch_news_data

print('=== RSS FETCH TEST ===')
news = fetch_news_data()
print(f'COUNT = {len(news)}')
for article in news[:5]:
    print('-', article.get('source'), '|', article.get('title', '')[:100])
if not news:
    raise SystemExit('RSS 수집 결과가 0건입니다.')
print('OK')
