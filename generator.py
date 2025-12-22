#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Tech News Generator with AI (Vertex AI / Google Gen AI SDK)
서비스 계정 JSON 키 파일로 인증하는 버전 + _generator.py 디자인 적용
"""

import os
import re
from glob import glob
from pathlib import Path
from datetime import datetime, timedelta

import feedparser
from dotenv import load_dotenv

from google import genai
from google.genai.types import HttpOptions

# ------------------------------------------------------------------
# 1. 환경 변수 로드 및 기본 설정
# ------------------------------------------------------------------
load_dotenv()

TODAY = datetime.now().strftime('%Y-%m-%d')
ARCHIVE_DIR = os.getenv("ARCHIVE_DIR", "archive")

# Vertex AI / Gen AI 설정 (서비스 계정 JSON 경로는 GOOGLE_APPLICATION_CREDENTIALS로 지정)
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

if not PROJECT_ID:
    raise RuntimeError("GOOGLE_CLOUD_PROJECT 환경 변수가 설정되지 않았습니다.")
if not LOCATION:
    raise RuntimeError("GOOGLE_CLOUD_LOCATION 환경 변수가 설정되지 않았습니다.")
if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS 환경 변수가 설정되지 않았습니다. (서비스 계정 JSON 경로)")

# Gen AI 클라이언트 생성 (Vertex AI 모드 + v1 API)
client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION,
    http_options=HttpOptions(api_version="v1"),
)

MODEL_ID = "gemini-3-flash-preview"

# RSS 피드 목록
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

# ------------------------------------------------------------------
# 2. RSS 뉴스 수집
# ------------------------------------------------------------------
def fetch_news_data():
    """RSS 피드에서 24시간 이내 뉴스 수집"""
    print("📡 RSS 피드에서 뉴스 수집 중...")

    articles = []
    cutoff_time = datetime.now() - timedelta(hours=24)

    for feed_info in RSS_FEEDS:
        if not feed_info["enabled"]:
            continue

        try:
            print(f"  - {feed_info['name']} 수집 중...")
            feed = feedparser.parse(feed_info["url"])

            for entry in feed.entries:
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    published = datetime(*entry.updated_parsed[:6])

                if published and published > cutoff_time:
                    article = {
                        "title": getattr(entry, "title", "No Title"),
                        "link": getattr(entry, "link", ""),
                        "summary": getattr(entry, "summary", ""),
                        "published": published.strftime("%Y-%m-%d %H:%M"),
                        "source": feed_info["name"],
                        "category": feed_info["category"],
                    }
                    articles.append(article)

        except Exception as e:
            print(f"  ⚠️ {feed_info['name']} 수집 실패: {e}")
            continue

    print(f"✅ 총 {len(articles)}개 기사 수집 완료")
    return articles

# ------------------------------------------------------------------
# 3. Vertex AI로 HTML 리포트 생성 (디자인 변경됨)
# ------------------------------------------------------------------
def generate_html_content(news_data):
    """AI에게 뉴스 분석 및 HTML 생성 요청 (Vertex AI Gemini)"""
    print("🤖 AI가 뉴스 분석 중...")

    # 뉴스 데이터를 텍스트로 변환
    news_text = "\n\n".join(
        [
            f"[{article['category']}] {article['title']}\n"
            f"출처: {article['source']}\n"
            f"발행: {article['published']}\n"
            f"요약: {article['summary'][:300]}...\n"
            f"링크: {article['link']}"
            for article in news_data
        ]
    )

    # 프롬프트 (_generator.py의 디자인 적용, 아카이브 드롭다운은 후처리에서 삽입)
    prompt = f"""
# Role Definition

당신은 '수석 IT 저널리스트'이자 '웹 퍼블리싱 전문가'입니다.

[Input Data]를 분석하여 심도 있는 내용이 담긴 **단일 HTML 리포트**를 작성하세요.

# Content Processing Rules (핵심: 무손실 요약 + 한글 번역)

0. **한글 번역 필수:** 모든 기사 제목과 내용을 **반드시 한글로 번역**하세요. 영문 기사는 자연스러운 한국어로 완전히 번역하되, 전문 용어는 원어를 괄호 안에 병기할 수 있습니다 (예: 생성형 AI(Generative AI)).

1. **깊이 있는 요약:** 기사를 한 줄로 너무 짧게 줄이지 마세요. 기사의 **'배경, 원인, 결과, 향후 전망'**이 포함되도록 3~5문장으로 서술형 요약을 하세요.

2. **계층 구조화:**
   - **🚨 HEADLINE (1~2개):** 가장 상세하게 작성 (기사당 300자 내외). 핵심 팩트와 수치를 불릿 포인트로 추가.
   - **🔥 MAJOR NEWS (4~6개):** 기사의 핵심 논조가 유지되도록 요약 (기사당 150자 내외).
   - **📄 BRIEF (나머지):** 간결하게 핵심만 전달.

3. **출처 명시:** 모든 기사 하단에 `[Source: 언론사명]`을 작게 표기하세요.

# Design & Layout Rules (CSS)

- **전체 레이아웃:** A4 용지 1~2장 분량에 정보가 꽉 차 보이는 '대시보드' 스타일.
- **반응형 그리드:**
  - PC 화면: Headline은 상단 전체, Major News는 **2열(2 columns)** 그리드 배치로 공간 효율 극대화.
  - 모바일: 1열로 보기 편하게 정렬.
- **스타일링:**
  - 폰트: 가독성 좋은 Sans-serif (Pretendard, Roboto, system-ui).
  - 색상: 신뢰감을 주는 딥 블루(Deep Blue) & 그레이 톤. 중요 키워드는 **볼드체** 또는 하이라이트 처리.
  - 가독성: 텍스트 덩어리가 너무 빽빽하지 않도록 적절한 `line-height`와 `padding` 사용.

# HTML Structure Output

아래 구조와 CSS 스타일을 **정확히** 따르는 완벽한 HTML5 코드를 작성하세요.
**중요: 아카이브 드롭다운 메뉴(archive-selector)는 절대 작성하지 마세요. 후처리에서 자동으로 추가됩니다.**

<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{TODAY} Tech Briefing</title>
<style>
  /* 여기에 CSS 작성: 모던하고 깔끔한 뉴스 대시보드 스타일 */
  body {{ font-family: 'Pretendard', 'Roboto', system-ui, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; background: #f4f6f8; color: #333; line-height: 1.6; }}
  .header {{ text-align: center; margin-bottom: 30px; border-bottom: 3px solid #2c3e50; padding-bottom: 10px; }}
  .header h1 {{ font-size: 2.2em; color: #2c3e50; margin-bottom: 5px; }}
  .header p {{ color: #555; font-size: 1.1em; }}
  .section-title {{ font-size: 1.5em; font-weight: bold; margin: 30px 0 15px; color: #2c3e50; border-left: 5px solid #e74c3c; padding-left: 10px; }}
 
  /* Headline 스타일: 강조, 박스 형태 */
  .headline-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; border-top: 5px solid #e74c3c; }}
  .headline-title {{ font-size: 1.8em; margin: 0 0 10px; color: #c0392b; line-height: 1.3; }}
  .headline-card ul {{ list-style-type: disc; margin-left: 20px; padding-left: 0; color: #555; }}
  .headline-card ul li {{ margin-bottom: 5px; }}
 
  /* Major News 스타일: 2열 그리드 */
  .grid-container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
  .news-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); display: flex; flex-direction: column; justify-content: space-between; }}
  .news-title {{ font-size: 1.2em; font-weight: bold; margin-bottom: 10px; color: #2980b9; line-height: 1.4; }}
 
  /* Brief 스타일: 리스트 형태 */
  .brief-list {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
  .brief-item {{ border-bottom: 1px solid #eee; padding: 15px 0; }}
  .brief-item:last-child {{ border-bottom: none; }}
  .brief-title {{ font-weight: bold; color: #34495e; margin-bottom: 5px; display: block; }}
 
  .source {{ font-size: 0.85em; color: #7f8c8d; margin-top: 10px; text-align: right; font-style: italic; }}
  .summary {{ line-height: 1.6; text-align: justify; margin-bottom: 15px; }}
  .summary strong {{ color: #e74c3c; }}
  .brief-summary {{ line-height: 1.5; margin-top: 5px; color: #555; }}

  /* 아카이브 드롭다운 스타일 */
  .archive-selector {{ position: absolute; top: 20px; right: 20px; z-index: 100; }}
  .archive-selector select {{ padding: 10px; border-radius: 5px; border: 2px solid #2c3e50; background: white; cursor: pointer; font-size: 0.9em; color: #2c3e50; }}

  /* 반응형 디자인 */
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
  <!-- 아카이브 드롭다운은 후처리에서 자동 삽입됨, 여기에 넣지 마세요 -->
  
  <div class="header">
    <h1>🚀 Daily Tech Insight</h1>
    <p>오늘의 주요 IT 트렌드 심층 분석 - {TODAY}</p>
  </div>

  <div class="section-title">🚨 HEADLINE NEWS</div>
  <!-- HEADLINE 뉴스 카드들을 여기에 추가 -->

  <div class="section-title">🔥 MAJOR ISSUES</div>
  <div class="grid-container">
    <!-- MAJOR NEWS 카드들을 여기에 추가 -->
  </div>

  <div class="section-title">📄 BRIEF & OTHERS</div>
  <div class="brief-list">
    <!-- BRIEF 아이템들을 여기에 추가 -->
  </div>
</body>
</html>

# Input Data

{news_text}
"""

    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
        )
        html_content = response.text or ""

        # 마크다운 코드 블록 제거
        html_content = html_content.replace("```html", "").replace("```", "")
        
        # 기존에 AI가 삽입한 archive-selector 제거 (있을 경우)
        html_content = re.sub(
            r'<div class="archive-selector">.*?</div>\s*',
            '',
            html_content,
            flags=re.DOTALL
        )

        return html_content.strip()
    except Exception as e:
        print(f"⚠️ AI 생성 실패: {e}")
        return generate_fallback_html(news_data)

# ------------------------------------------------------------------
# 4. 번역용 헬퍼 (Vertex AI 사용)
# ------------------------------------------------------------------
def translate_to_korean(text, text_type="title"):
    """영문 텍스트를 한글로 번역 (Vertex AI Gemini 사용)"""
    try:
        if text_type == "title":
            prompt = (
                "다음 기사 제목을 자연스러운 한국어로 번역하세요. "
                "번역문만 출력하세요:\n\n" + text
            )
        else:
            prompt = (
                "다음 기사 요약을 자연스러운 한국어로 번역하세요. "
                "전문 용어는 원어를 괄호에 병기하세요. 번역문만 출력하세요:\n\n"
                + text
            )

        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
        )
        return (response.text or "").strip()
    except Exception as e:
        print(f"  ⚠️ 번역 실패 ({text[:30]}...): {e}")
        return text

# ------------------------------------------------------------------
# 5. AI 실패 시 기본 HTML 생성 (_generator.py 디자인 적용)
# ------------------------------------------------------------------
def generate_fallback_html(news_data):
    """AI 실패 시 기본 HTML 생성 + 번역기 사용 (디자인 업그레이드)"""
    print("📝 기본 HTML 생성 중...")

    today_obj = datetime.now()
    date_display = (
        today_obj.strftime("%Y년 %m월 %d일(%a)")
        .replace("Mon", "월")
        .replace("Tue", "화")
        .replace("Wed", "수")
        .replace("Thu", "목")
        .replace("Fri", "금")
        .replace("Sat", "토")
        .replace("Sun", "일")
    )

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Daily Tech Insight - {TODAY}</title>
<style>
:root {{
  --primary-color: #2c3e50;
  --accent-color: #e74c3c;
  --highlight-color: #2980b9;
  --bg-color: #f4f6f8;
  --card-bg: #ffffff;
  --text-color: #333333;
  --meta-color: #7f8c8d;
}}

body {{
  font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Malgun Gothic', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', sans-serif;
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
  background: var(--bg-color);
  color: var(--text-color);
  line-height: 1.6;
  word-break: keep-all;
}}

/* Header */
.header {{
  text-align: center;
  margin-bottom: 40px;
  border-bottom: 3px solid var(--primary-color);
  padding-bottom: 20px;
}}
.header h1 {{
  font-size: 2.5rem;
  margin: 0;
  color: var(--primary-color);
  letter-spacing: -1px;
}}
.header p {{
  font-size: 1.1rem;
  color: var(--meta-color);
  margin: 10px 0 0;
}}

/* Archive Selector */
.archive-selector {{
  text-align: center;
  margin-bottom: 20px;
}}
.archive-selector select {{
  padding: 10px 15px;
  border-radius: 8px;
  border: 2px solid var(--primary-color);
  background: white;
  cursor: pointer;
  font-size: 0.95em;
  transition: all 0.2s;
}}
.archive-selector select:hover {{
  background: var(--primary-color);
  color: white;
}}

/* Section Title */
.section-title {{
  font-size: 1.6em;
  font-weight: 800;
  margin: 40px 0 20px;
  color: var(--primary-color);
  border-left: 6px solid var(--accent-color);
  padding-left: 15px;
  display: flex;
  align-items: center;
}}

/* News Grid */
.grid-container {{
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 25px;
  margin-bottom: 30px;
}}

.news-card {{
  background: var(--card-bg);
  padding: 25px;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.04);
  border: 1px solid #eee;
  transition: all 0.3s ease;
}}

.news-card:hover {{
  transform: translateY(-3px);
  box-shadow: 0 8px 15px rgba(0,0,0,0.1);
}}

.news-title {{
  font-size: 1.35em;
  font-weight: 700;
  margin-bottom: 15px;
  color: var(--highlight-color);
  line-height: 1.4;
}}

.news-meta {{
  font-size: 0.85em;
  color: var(--meta-color);
  margin-bottom: 12px;
  font-weight: 600;
}}

.news-summary {{
  font-size: 0.95em;
  color: #555;
  margin-bottom: 15px;
  line-height: 1.7;
  text-align: justify;
}}

.news-link {{
  display: inline-block;
  color: var(--highlight-color);
  text-decoration: none;
  font-weight: 600;
  font-size: 0.9em;
  transition: color 0.2s;
}}

.news-link:hover {{
  color: var(--accent-color);
}}

/* Brief List */
.brief-list {{
  background: var(--card-bg);
  padding: 10px 25px;
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}}

.brief-item {{
  border-bottom: 1px solid #f0f0f0;
  padding: 18px 0;
}}

.brief-item:last-child {{
  border-bottom: none;
}}

.brief-title {{
  font-weight: 700;
  font-size: 1.1em;
  color: #2c3e50;
  margin-bottom: 8px;
}}

.brief-content {{
  font-size: 0.9em;
  color: #666;
  line-height: 1.6;
}}

.brief-meta {{
  font-size: 0.8em;
  color: var(--meta-color);
  margin-top: 5px;
  font-style: italic;
}}

/* Responsive */
@media (max-width: 768px) {{
  .grid-container {{
    grid-template-columns: 1fr;
  }}
  .header h1 {{
    font-size: 2rem;
  }}
}}
</style>
</head>
<body>

<div class="header">
  <h1>🚀 Daily Tech Insight</h1>
  <p>{date_display} • 오늘의 주요 IT 트렌드 심층 분석</p>
</div>

<div class="section-title">🔥 주요 뉴스</div>
<div class="grid-container">
"""

    print("🌐 기사 번역 중...")
    for idx, article in enumerate(news_data[:10], 1):
        print(f"  [{idx}/10] {article['title'][:50]}...")
        translated_title = translate_to_korean(article["title"], "title")
        translated_summary = translate_to_korean(article["summary"][:250], "summary")

        html += f"""
  <div class="news-card">
    <div class="news-title">{translated_title}</div>
    <div class="news-meta">[{article['category']}] {article['source']} • {article['published']}</div>
    <div class="news-summary">{translated_summary}...</div>
    <a href="{article['link']}" target="_blank" class="news-link">원문 보기 →</a>
  </div>
"""

    html += """
</div>

<div class="section-title">📄 기타 소식</div>
<div class="brief-list">
"""

    for idx, article in enumerate(news_data[10:20], 11):
        print(f"  [{idx}/20] {article['title'][:50]}...")
        translated_title = translate_to_korean(article["title"], "title")
        translated_summary = translate_to_korean(article["summary"][:150], "summary")

        html += f"""
  <div class="brief-item">
    <div class="brief-title">{translated_title}</div>
    <div class="brief-content">{translated_summary}... <a href="{article['link']}" target="_blank" class="news-link">더보기</a></div>
    <div class="brief-meta">[{article['category']}] {article['source']} • {article['published']}</div>
  </div>
"""

    html += """
</div>

</body>
</html>
"""
    return html

# ------------------------------------------------------------------
# 6. 아카이브 드롭다운 생성
# ------------------------------------------------------------------
def build_archive_dropdown(is_archive_page=False):
    """아카이브 드롭다운 메뉴 생성
    
    Args:
        is_archive_page: True면 archive/*.html용, False면 index.html용
    """
    files = sorted(glob(os.path.join(ARCHIVE_DIR, "*.html")), reverse=True)
    options = ""

    for f in files:
        date_str = os.path.basename(f).replace(".html", "")
        options += f'        <option value="{date_str}.html">{date_str}</option>\n'

    if is_archive_page:
        # archive/*.html용: 상대 경로 사용 + 메인 이동 옵션 추가
        dropdown_html = f"""<div class="archive-selector">
    <select onchange="if(this.value) location.href = this.value">
        <option value="">📅 과거 기사 보기</option>
        <option value="../index.html">🏠 오늘 뉴스로 이동</option>
{options}    </select>
</div>"""
    else:
        # index.html용: archive/ 경로 추가
        dropdown_html = f"""<div class="archive-selector">
    <select onchange="if(this.value) location.href='archive/' + this.value">
        <option value="">📅 과거 기사 보기</option>
{options}    </select>
</div>"""
    return dropdown_html

# ------------------------------------------------------------------
# 7. HTML에 드롭다운 삽입
# ------------------------------------------------------------------
def insert_archive_dropdown(html_content, is_archive_page=False):
    """HTML에 아카이브 드롭다운 삽입"""
    dropdown = build_archive_dropdown(is_archive_page)
    
    # <body> 태그 바로 다음에 드롭다운 삽입
    if "<body>" in html_content:
        html_content = html_content.replace("<body>", f"<body>\n{dropdown}\n")
    elif "<body " in html_content:
        # <body class="..."> 같은 형태도 처리
        html_content = re.sub(
            r'(<body[^>]*>)',
            rf'\1\n{dropdown}\n',
            html_content
        )
    
    return html_content

# ------------------------------------------------------------------
# 8. 메인 실행 함수
# ------------------------------------------------------------------
def main():
    print("=" * 60)
    print("  Daily Tech News Generator with AI (Vertex AI)")
    print("=" * 60)

    os.makedirs(ARCHIVE_DIR, exist_ok=True)

    # 1. 뉴스 수집
    raw_data = fetch_news_data()

    if not raw_data:
        print("❌ 수집된 기사가 없습니다.")
        return

    # 2. AI 요약 생성 (드롭다운 없는 원본 HTML)
    html_content = generate_html_content(raw_data)

    # 3. index.html용 HTML 생성 (드롭다운 삽입)
    index_html = insert_archive_dropdown(html_content, is_archive_page=False)

    # 4. archive용 HTML 생성 (드롭다운 삽입)
    archive_html = insert_archive_dropdown(html_content, is_archive_page=True)

    # 5. 파일 저장
    archive_path = os.path.join(ARCHIVE_DIR, f"{TODAY}.html")
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(archive_html)
    print(f"✅ Archive 저장: {archive_path}")

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    print("✅ Index 업데이트: index.html")

    print("=" * 60)
    print("✨ 작업 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()