#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Tech News Generator with Gemini API key authentication.
- macOS/Linux friendly
- .env based configuration
- Generates index.html + archive/YYYY-MM-DD.html + post.md
"""

import os
import re
from glob import glob
from datetime import datetime, timedelta

import feedparser
from dotenv import load_dotenv
from google import genai

load_dotenv()

TODAY = datetime.now().strftime('%Y-%m-%d')
ARCHIVE_DIR = os.getenv('ARCHIVE_DIR', 'archive')
MODEL_ID = os.getenv('GEMINI_MODEL', 'gemini-3.1-pro-preview')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    raise RuntimeError('GEMINI_API_KEY 환경 변수가 설정되지 않았습니다. .env 파일 또는 셸 환경에 API 키를 넣어주세요.')

client = genai.Client(api_key=GEMINI_API_KEY)

RSS_FEEDS = [
    {"name": "AWS News", "url": "https://aws.amazon.com/blogs/aws/feed/", "enabled": True, "category": "Cloud"},
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "enabled": True, "category": "AI News"},
    {"name": "Microsoft Azure", "url": "https://azure.microsoft.com/en-us/blog/feed/", "enabled": True, "category": "Cloud"},
    {"name": "OpenAI", "url": "https://openai.com/news/rss.xml", "enabled": True, "category": "AI Model"},
    {"name": "MIT Technology Review AI", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/", "enabled": True, "category": "AI News"},
    {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/", "enabled": True, "category": "AI News"},
    {"name": "NVIDIA Blog", "url": "https://feeds.feedburner.com/nvidiablog", "enabled": True, "category": "Hardware"},
    {"name": "Hugging Face", "url": "https://huggingface.co/blog/feed.xml", "enabled": True, "category": "Open Source"},
    {"name": "Arxiv AI", "url": "http://export.arxiv.org/rss/cs.AI", "enabled": False, "category": "Research"},
    {"name": "Naver D2", "url": "https://d2.naver.com/d2.atom", "enabled": True, "category": "Tech"},
    {"name": "Kakao Tech", "url": "https://tech.kakao.com/feed/", "enabled": True, "category": "Tech"},
    {"name": "Line (LY Corp)", "url": "https://techblog.lycorp.co.jp/ko/feed/index.xml", "enabled": True, "category": "Tech"},
    {"name": "Woowa Bros", "url": "https://techblog.woowahan.com/feed/", "enabled": True, "category": "Tech"},
    {"name": "Toss Tech", "url": "https://toss.tech/rss.xml", "enabled": True, "category": "Fintech"},
]


def fetch_news_data():
    print('📡 RSS 피드에서 뉴스 수집 중...')
    articles = []
    cutoff_time = datetime.now() - timedelta(hours=24)

    for feed_info in RSS_FEEDS:
        if not feed_info['enabled']:
            continue
        try:
            print(f"  - {feed_info['name']} 수집 중...")
            feed = feedparser.parse(feed_info['url'])
            for entry in feed.entries:
                published = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    published = datetime(*entry.updated_parsed[:6])

                if published and published > cutoff_time:
                    articles.append({
                        'title': getattr(entry, 'title', 'No Title'),
                        'link': getattr(entry, 'link', ''),
                        'summary': getattr(entry, 'summary', ''),
                        'published': published.strftime('%Y-%m-%d %H:%M'),
                        'source': feed_info['name'],
                        'category': feed_info['category'],
                    })
        except Exception as e:
            print(f"  ⚠️ {feed_info['name']} 수집 실패: {e}")
            continue

    print(f'✅ 총 {len(articles)}개 기사 수집 완료')
    return articles


def ai_generate(prompt: str) -> str:
    response = client.models.generate_content(model=MODEL_ID, contents=prompt)
    return (response.text or '').strip()


def generate_html_content(news_data):
    print('🤖 AI가 뉴스 분석 중...')
    news_text = '\n\n'.join(
        [
            f"[{article['category']}] {article['title']}\n"
            f"출처: {article['source']}\n"
            f"발행: {article['published']}\n"
            f"요약: {article['summary'][:300]}...\n"
            f"링크: {article['link']}"
            for article in news_data
        ]
    )

    prompt = f"""
# Role Definition
당신은 '수석 IT 저널리스트'이자 '웹 퍼블리싱 전문가'입니다.
[Input Data]를 분석하여 심도 있는 내용이 담긴 단일 HTML 리포트를 작성하세요.

# Content Processing Rules
0. 모든 기사 제목과 내용을 반드시 한글로 번역하세요.
1. 각 카드 내용은 **확인된 사실 + 짧은 의미 해석** 구조로 작성하세요.
2. HTML 본문에서는 인사이트 문장을 반드시 줄바꿈 후 `<strong>[인사이트]</strong>` 라벨로 시작하게 작성하세요.
3. 카드 본문 구조를 아래처럼 강제합니다:
   - 첫 문장/첫 단락: 확인된 사실 요약
   - 줄바꿈 (`<br>` 또는 새 단락)
   - `<strong>[인사이트]</strong>` 로 시작하는 해석 문장 1개
4. `<strong>[인사이트]</strong>` 라벨은 실제 HTML 출력에 반드시 포함되어야 하며, 생략하거나 일반 문장 속에 녹이지 마세요.
5. 요약은 배경, 원인, 결과, 의미를 중심으로 작성하고, 전망 문장은 최소화하세요. 가능하면 미래 예측보다 현재 확인된 사실과 해석에 집중하세요.
6. 미래 표현이 꼭 필요할 때도 `시사한다`, `보여준다`, `해석된다`, `가능성이 있다` 정도로 제한하고, `~할 것이다`, `~이끌 것이다`, `~도래할 것이다`, `핵심으로 자리 잡을 전망이다` 같은 강한 단정은 사용하지 마세요.
7. 계층 구조화:
   - 🚨 HEADLINE (1~2개): 가장 상세하게 작성. 한국 독자 관점에서 파급력, 클릭성, 산업 영향도를 우선 반영하세요.
   - 🔥 MAJOR NEWS (4~6개): 핵심 논조 유지
   - 📄 BRIEF: 간결 요약
8. 각 기사 하단에 [Source: 언론사명] 표기
9. 템플릿 문장 반복을 줄이고 기사별 어조를 약간씩 다르게 하세요.
10. 카드 길이 제한:
   - HEADLINE summary: 220~280자 수준
   - MAJOR summary: 120~170자 수준
   - BRIEF summary: 70~110자 수준
11. 과장광고, 과도한 확신, 선정적 표현 금지
12. 브리핑은 기사처럼 보여야 하며, 과하게 홍보성/예언형으로 쓰지 마세요.

# HTML Structure Output
완전한 HTML5 코드를 작성하세요.
아카이브 드롭다운은 작성하지 마세요.

<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{TODAY} Tech Briefing</title>
<style>
  body {{ font-family: 'Pretendard', 'Roboto', system-ui, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; background: #f4f6f8; color: #333; line-height: 1.6; }}
  .header {{ text-align: center; margin-bottom: 30px; border-bottom: 3px solid #2c3e50; padding-bottom: 10px; }}
  .header h1 {{ font-size: 2.2em; color: #2c3e50; margin-bottom: 5px; }}
  .header p {{ color: #555; font-size: 1.1em; }}
  .section-title {{ font-size: 1.5em; font-weight: bold; margin: 30px 0 15px; color: #2c3e50; border-left: 5px solid #e74c3c; padding-left: 10px; }}
  .headline-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; border-top: 5px solid #e74c3c; }}
  .headline-title {{ font-size: 1.8em; margin: 0 0 10px; color: #c0392b; line-height: 1.3; }}
  .headline-card ul {{ list-style-type: disc; margin-left: 20px; padding-left: 0; color: #555; }}
  .headline-card ul li {{ margin-bottom: 5px; }}
  .grid-container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
  .news-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); display: flex; flex-direction: column; justify-content: space-between; }}
  .news-title {{ font-size: 1.2em; font-weight: bold; margin-bottom: 10px; color: #2980b9; line-height: 1.4; }}
  .brief-list {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
  .brief-item {{ border-bottom: 1px solid #eee; padding: 15px 0; }}
  .brief-item:last-child {{ border-bottom: none; }}
  .brief-title {{ font-weight: bold; color: #34495e; margin-bottom: 5px; display: block; }}
  .source {{ font-size: 0.85em; color: #7f8c8d; margin-top: 10px; text-align: right; font-style: italic; }}
  .summary {{ line-height: 1.6; text-align: justify; margin-bottom: 15px; }}
  .summary strong {{ color: #e74c3c; }}
  .brief-summary {{ line-height: 1.5; margin-top: 5px; color: #555; }}
  .archive-selector {{ position: absolute; top: 20px; right: 20px; z-index: 100; }}
  .archive-selector select {{ padding: 10px; border-radius: 5px; border: 2px solid #2c3e50; background: white; cursor: pointer; font-size: 0.9em; color: #2c3e50; }}
  @media (max-width: 768px) {{
    body {{ padding: 15px; }}
    .header h1 {{ font-size: 1.8em; }}
    .section-title {{ font-size: 1.3em; margin: 25px 0 10px; }}
    .headline-title {{ font-size: 1.5em; }}
    .grid-container {{ grid-template-columns: 1fr; }}
    .news-title {{ font-size: 1.1em; }}
    .archive-selector {{ position: static; text-align: center; margin-bottom: 20px; }}
    .archive-selector select {{ width: 100%; max-width: 300px; }}
  }}
</style>
</head>
<body>
  <div class="header">
    <h1>🚀 Daily Tech Insight</h1>
    <p>오늘의 주요 IT 트렌드 심층 분석 - {TODAY}</p>
  </div>
  <div class="section-title">🚨 HEADLINE NEWS</div>
  <div class="section-title">🔥 MAJOR ISSUES</div>
  <div class="grid-container"></div>
  <div class="section-title">📄 BRIEF & OTHERS</div>
  <div class="brief-list"></div>
</body>
</html>

# Input Data
{news_text}
"""
    try:
        html_content = ai_generate(prompt)
        html_content = html_content.replace('```html', '').replace('```', '')
        html_content = re.sub(r'<div class="archive-selector">.*?</div>\s*', '', html_content, flags=re.DOTALL)
        return html_content.strip()
    except Exception as e:
        print(f'⚠️ AI 생성 실패: {e}')
        return generate_fallback_html(news_data)


def generate_post_markdown(news_data):
    print('📝 AI가 post.md(브리핑) 작성 중...')
    news_text = '\n\n'.join(
        [
            f"[{article['category']}] {article['title']}\n"
            f"출처: {article['source']}\n"
            f"발행: {article['published']}\n"
            f"요약: {article['summary'][:450]}...\n"
            f"링크: {article['link']}"
            for article in news_data
        ]
    )
    prompt = f"""
[Role]
너는 데이터 저널리즘 팀의 에디터다. 과장 없이 사실만으로 설득한다.

[Objective]
업로드된 스토리 전체를 객관적인 **일간 기술 브리핑** 기사 1편으로 작성하라.
한국어 본문 + 영어 요약을 함께 제공하되, **사실 정보와 AI 인사이트를 분리해서** 제공하라.

[Guidelines]
- 문서 성격은 `주간 브리핑`이 아니라 `오늘의 브리핑`이다. `주간`, `이번 주` 같은 표현은 사용하지 마라.
- 각 핵심 이슈는 반드시 아래 3개 구역으로 나눠라:
  1. **문제 인식**
  2. **발표 및 업데이트 내용** → 여기에는 기사에 나온 사실, 수치, 날짜, 발언만 쓴다.
  3. **인사이트** → 여기에는 왜 중요한지, 어떤 흐름인지, 누가 영향을 받는지 해석한다.
- `발표 및 업데이트 내용`에는 해석이나 의견을 넣지 마라.
- 인사이트는 반드시 본문 기사 안에서 **줄바꿈 후 `[인사이트]`** 라벨을 붙여 시작하라.
- 즉 형식은 아래처럼 강제한다:
  - 발표 및 업데이트 내용
  - 빈 줄
  - [인사이트] ...
- `인사이트`에는 기사 원문에 없는 추가 맥락 해석은 가능하지만, 사실처럼 단정하지 말고 시사점/가능성 수준으로 제한하라.
- 수치/버전/날짜 명시
- 각 구역 끝에는 관련 소스 1개 이상 연결(Source: …)
- 미래 전망 문장은 최소화하라. 가능하면 현재 확인된 사실과 의미 해석 중심으로 작성하라.
- 미래 표현이 필요해도 `가능성이 있다`, `시사한다`, `보여준다`, `해석된다` 수준으로 제한하라.
- `~할 것이다`, `~이끌 것이다`, `~도래할 것이다`, `핵심으로 자리 잡을 전망이다` 같은 강한 미래 단정은 금지한다.
- 과장광고, 과도한 미래 확신, 선정적 표현 금지
- 마지막에 직군별 인사이트:
  - 개발자라면
  - 경영자라면
  - CFO라면
- 마지막 줄에 전체 출처 목록 정리

[Output]
- Markdown으로만 출력
- 맨 위 제목: # Tech Briefing - {TODAY}
- 그 아래 섹션 제목은 `일간 기술 브리핑`, `오늘의 핵심 이슈`, `오늘의 인사이트`처럼 오늘 기준 표현만 사용
- 정보/인사이트가 섞여 보이지 않게 제목을 명확히 분리
- 각 핵심 이슈 본문 안에서는 인사이트 문단을 별도 소제목으로 빼지 말고, 반드시 줄바꿈 후 `[인사이트]` 라벨로 표시하라

[Input Data]
{news_text}
"""
    try:
        md = ai_generate(prompt)
        md = md.replace('```markdown', '').replace('```md', '').replace('```', '').strip()
        return md
    except Exception as e:
        print(f'⚠️ post.md 생성 실패: {e}')
        return generate_fallback_markdown(news_data)


def generate_fallback_markdown(news_data):
    lines = [f'# Tech Briefing - {TODAY}', '']
    lines.append('## 수집 기사 목록(요약)')
    lines.append('')
    for a in news_data:
        lines.append(f"- **{a.get('title', '')}** ({a.get('source', '')}, {a.get('published', '')})")
        if a.get('link'):
            lines.append(f"  - Source: {a['link']}")
    lines.append('')
    lines.append('전체 출처 목록')
    for a in news_data:
        if a.get('link'):
            lines.append(f"- {a.get('source', '')}: {a['link']}")
    return '\n'.join(lines)


def translate_to_korean(text, text_type='title'):
    try:
        if text_type == 'title':
            prompt = '다음 기사 제목을 자연스러운 한국어로 번역하세요. 번역문만 출력하세요:\n\n' + text
        else:
            prompt = '다음 기사 요약을 자연스러운 한국어로 번역하세요. 전문 용어는 원어를 괄호에 병기하세요. 번역문만 출력하세요:\n\n' + text
        return ai_generate(prompt).strip()
    except Exception as e:
        print(f"  ⚠️ 번역 실패 ({text[:30]}...): {e}")
        return text


def generate_fallback_html(news_data):
    print('📝 기본 HTML 생성 중...')
    today_obj = datetime.now()
    date_display = (
        today_obj.strftime('%Y년 %m월 %d일(%a)')
        .replace('Mon', '월').replace('Tue', '화').replace('Wed', '수')
        .replace('Thu', '목').replace('Fri', '금').replace('Sat', '토').replace('Sun', '일')
    )
    html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Daily Tech Insight - {TODAY}</title>
<style>
:root {{ --primary-color:#2c3e50; --accent-color:#e74c3c; --highlight-color:#2980b9; --bg-color:#f4f6f8; --card-bg:#ffffff; --text-color:#333333; --meta-color:#7f8c8d; }}
body {{ font-family:'Pretendard',-apple-system,BlinkMacSystemFont,system-ui,Roboto,'Helvetica Neue','Segoe UI','Apple SD Gothic Neo','Malgun Gothic',sans-serif; max-width:1000px; margin:0 auto; padding:20px; background:var(--bg-color); color:var(--text-color); line-height:1.6; word-break:keep-all; }}
.header {{ text-align:center; margin-bottom:40px; border-bottom:3px solid var(--primary-color); padding-bottom:20px; }}
.header h1 {{ font-size:2.5rem; margin:0; color:var(--primary-color); letter-spacing:-1px; }}
.header p {{ font-size:1.1rem; color:var(--meta-color); margin:10px 0 0; }}
.archive-selector {{ text-align:center; margin-bottom:20px; }}
.archive-selector select {{ padding:10px 15px; border-radius:8px; border:2px solid var(--primary-color); background:white; cursor:pointer; font-size:0.95em; transition:all 0.2s; }}
.archive-selector select:hover {{ background:var(--primary-color); color:white; }}
.section-title {{ font-size:1.6em; font-weight:800; margin:40px 0 20px; color:var(--primary-color); border-left:6px solid var(--accent-color); padding-left:15px; display:flex; align-items:center; }}
.grid-container {{ display:grid; grid-template-columns:repeat(2, 1fr); gap:25px; margin-bottom:30px; }}
.news-card {{ background:var(--card-bg); padding:25px; border-radius:12px; box-shadow:0 4px 6px rgba(0,0,0,0.04); border:1px solid #eee; transition:all 0.3s ease; }}
.news-card:hover {{ transform:translateY(-3px); box-shadow:0 8px 15px rgba(0,0,0,0.1); }}
.news-title {{ font-size:1.35em; font-weight:700; margin-bottom:15px; color:var(--highlight-color); line-height:1.4; }}
.news-meta {{ font-size:0.85em; color:var(--meta-color); margin-bottom:12px; font-weight:600; }}
.news-summary {{ font-size:0.95em; color:#555; margin-bottom:15px; line-height:1.7; text-align:justify; }}
.news-link {{ display:inline-block; color:var(--highlight-color); text-decoration:none; font-weight:600; font-size:0.9em; transition:color 0.2s; }}
.news-link:hover {{ color:var(--accent-color); }}
.brief-list {{ background:var(--card-bg); padding:10px 25px; border-radius:12px; box-shadow:0 2px 4px rgba(0,0,0,0.05); }}
.brief-item {{ border-bottom:1px solid #f0f0f0; padding:18px 0; }}
.brief-item:last-child {{ border-bottom:none; }}
.brief-title {{ font-weight:700; font-size:1.1em; color:#2c3e50; margin-bottom:8px; }}
.brief-content {{ font-size:0.9em; color:#666; line-height:1.6; }}
.brief-meta {{ font-size:0.8em; color:var(--meta-color); margin-top:5px; font-style:italic; }}
@media (max-width:768px) {{ .grid-container {{ grid-template-columns:1fr; }} .header h1 {{ font-size:2rem; }} }}
</style>
</head>
<body>
<div class="header"><h1>🚀 Daily Tech Insight</h1><p>{date_display} • 오늘의 주요 IT 트렌드 심층 분석</p></div>
<div class="section-title">🔥 주요 뉴스</div><div class="grid-container">'''

    print('🌐 기사 번역 중...')
    for idx, article in enumerate(news_data[:10], 1):
        print(f"  [{idx}/10] {article['title'][:50]}...")
        translated_title = translate_to_korean(article['title'], 'title')
        translated_summary = translate_to_korean(article['summary'][:250], 'summary')
        html += f'''<div class="news-card"><div class="news-title">{translated_title}</div><div class="news-meta">[{article['category']}] {article['source']} • {article['published']}</div><div class="news-summary">{translated_summary}...</div><a href="{article['link']}" target="_blank" class="news-link">원문 보기 →</a></div>'''

    html += '</div><div class="section-title">📄 기타 소식</div><div class="brief-list">'
    for idx, article in enumerate(news_data[10:20], 11):
        print(f"  [{idx}/20] {article['title'][:50]}...")
        translated_title = translate_to_korean(article['title'], 'title')
        translated_summary = translate_to_korean(article['summary'][:150], 'summary')
        html += f'''<div class="brief-item"><div class="brief-title">{translated_title}</div><div class="brief-content">{translated_summary}... <a href="{article['link']}" target="_blank" class="news-link">더보기</a></div><div class="brief-meta">[{article['category']}] {article['source']} • {article['published']}</div></div>'''
    html += '</div></body></html>'
    return html


def build_archive_dropdown(is_archive_page=False):
    files = sorted(glob(os.path.join(ARCHIVE_DIR, '*.html')), reverse=True)
    options = ''
    for f in files:
        date_str = os.path.basename(f).replace('.html', '')
        options += f'        <option value="{date_str}.html">{date_str}</option>\n'
    if is_archive_page:
        return f'''<div class="archive-selector">
    <select onchange="if(this.value) location.href = this.value">
        <option value="">📅 과거 기사 보기</option>
        <option value="../index.html">🏠 오늘 뉴스로 이동</option>
{options}    </select>
</div>'''
    return f'''<div class="archive-selector">
    <select onchange="if(this.value) location.href='archive/' + this.value">
        <option value="">📅 과거 기사 보기</option>
{options}    </select>
</div>'''


def insert_archive_dropdown(html_content, is_archive_page=False):
    dropdown = build_archive_dropdown(is_archive_page)
    if '<body>' in html_content:
        return html_content.replace('<body>', f'<body>\n{dropdown}\n')
    if '<body ' in html_content:
        return re.sub(r'(<body[^>]*>)', rf'\1\n{dropdown}\n', html_content)
    return html_content


def main():
    print('=' * 60)
    print(f'  Daily Tech News Generator with Gemini API ({MODEL_ID})')
    print('=' * 60)
    os.makedirs(ARCHIVE_DIR, exist_ok=True)

    raw_data = fetch_news_data()
    if not raw_data:
        raise RuntimeError('수집된 기사가 없습니다.')

    html_content = generate_html_content(raw_data)
    post_md = generate_post_markdown(raw_data)
    index_html = insert_archive_dropdown(html_content, is_archive_page=False)
    archive_html = insert_archive_dropdown(html_content, is_archive_page=True)

    archive_path = os.path.join(ARCHIVE_DIR, f'{TODAY}.html')
    with open(archive_path, 'w', encoding='utf-8') as f:
        f.write(archive_html)
    print(f'✅ Archive 저장: {archive_path}')

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(index_html)
    print('✅ Index 업데이트: index.html')

    with open('post.md', 'w', encoding='utf-8') as f:
        f.write(post_md)
    print('✅ post.md 저장: post.md')

    archive_md_path = os.path.join(ARCHIVE_DIR, f'{TODAY}.md')
    with open(archive_md_path, 'w', encoding='utf-8') as f:
        f.write(post_md)
    print(f'✅ Archive post.md 저장: {archive_md_path}')

    print('=' * 60)
    print('✨ 작업 완료!')
    print('=' * 60)


if __name__ == '__main__':
    main()
