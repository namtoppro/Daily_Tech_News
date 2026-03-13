#!/usr/bin/env python3
import os
from datetime import datetime
from generator2 import fetch_news_data, generate_html_content, generate_post_markdown, insert_archive_dropdown

print('=== WRITE OUTPUTS TEST ===')
news = fetch_news_data()
if not news:
    raise SystemExit('RSS 수집 결과가 없어 파일 저장 테스트 불가')
html = generate_html_content(news[:8])
md = generate_post_markdown(news[:8])
index_html = insert_archive_dropdown(html, is_archive_page=False)
archive_html = insert_archive_dropdown(html, is_archive_page=True)

today = datetime.now().strftime('%Y-%m-%d')
os.makedirs('archive', exist_ok=True)
with open('test_index.html', 'w', encoding='utf-8') as f:
    f.write(index_html)
with open(f'archive/test-{today}.html', 'w', encoding='utf-8') as f:
    f.write(archive_html)
with open('test_post.md', 'w', encoding='utf-8') as f:
    f.write(md)
print('WROTE = test_index.html, test_post.md, archive/test-YYYY-MM-DD.html')
print('OK')
