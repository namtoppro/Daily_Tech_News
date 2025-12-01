#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Tech News Generator with AI
AI 기반 뉴스 수집 및 HTML 리포트 생성 봇
"""

import os
import datetime
from glob import glob
from pathlib import Path
import feedparser
from datetime import datetime, timedelta
import google.generativeai as genai
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 설정값
TODAY = datetime.now().strftime('%Y-%m-%d')
ARCHIVE_DIR = "archive"
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

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


def fetch_news_data():
    """RSS 피드에서 24시간 이내 뉴스 수집"""
    print("📡 RSS 피드에서 뉴스 수집 중...")
    
    articles = []
    cutoff_time = datetime.now() - timedelta(hours=24)
    
    for feed_info in RSS_FEEDS:
        if not feed_info['enabled']:
            continue
            
        try:
            print(f"  - {feed_info['name']} 수집 중...")
            feed = feedparser.parse(feed_info['url'])
            
            for entry in feed.entries:
                # 발행 시간 파싱
                published = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    published = datetime(*entry.updated_parsed[:6])
                
                # 24시간 이내 기사만 수집
                if published and published > cutoff_time:
                    article = {
                        'title': entry.title if hasattr(entry, 'title') else 'No Title',
                        'link': entry.link if hasattr(entry, 'link') else '',
                        'summary': entry.summary if hasattr(entry, 'summary') else '',
                        'published': published.strftime('%Y-%m-%d %H:%M'),
                        'source': feed_info['name'],
                        'category': feed_info['category']
                    }
                    articles.append(article)
                    
        except Exception as e:
            print(f"  ⚠️ {feed_info['name']} 수집 실패: {e}")
            continue
    
    print(f"✅ 총 {len(articles)}개 기사 수집 완료")
    return articles


def generate_html_content(news_data):
    """AI에게 뉴스 분석 및 HTML 생성 요청"""
    print("🤖 AI가 뉴스 분석 중...")
    
    # Gemini API 설정
    if not GEMINI_API_KEY:
        print("⚠️ GEMINI_API_KEY가 설정되지 않았습니다. 환경변수를 확인하세요.")
        return generate_fallback_html(news_data)
    
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    # 뉴스 데이터를 텍스트로 변환
    news_text = "\n\n".join([
        f"[{article['category']}] {article['title']}\n"
        f"출처: {article['source']}\n"
        f"발행: {article['published']}\n"
        f"요약: {article['summary'][:300]}...\n"
        f"링크: {article['link']}"
        for article in news_data
    ])
    
    # AI 프롬프트
    prompt = f"""
# Role Definition

당신은 '수석 IT 저널리스트'이자 '웹 퍼블리싱 전문가'입니다.

[Input Data]를 분석하여 심도 있는 내용이 담긴 **단일 HTML 리포트**를 작성하세요.

# Content Processing Rules (핵심: 무손실 요약)

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

(아래 구조를 따르는 완벽한 HTML5 코드를 작성하세요. CSS는 `<style>` 태그 안에 모두 포함하세요.)

<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{TODAY} Tech Briefing</title>
<style>
  /* 여기에 CSS 작성: 모던하고 깔끔한 뉴스 대시보드 스타일 */
  body {{ font-family: system-ui, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; background: #f4f6f8; color: #333; }}
  .header {{ text-align: center; margin-bottom: 30px; border-bottom: 3px solid #2c3e50; padding-bottom: 10px; }}
  .section-title {{ font-size: 1.5em; font-weight: bold; margin: 20px 0 10px; color: #2c3e50; border-left: 5px solid #e74c3c; padding-left: 10px; }}
 
  /* Headline 스타일: 강조, 박스 형태 */
  .headline-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; border-top: 5px solid #e74c3c; }}
  .headline-title {{ font-size: 1.8em; margin: 0 0 10px; color: #c0392b; }}
 
  /* Major News 스타일: 2열 그리드 */
  .grid-container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
  .news-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); display: flex; flex-direction: column; justify-content: space-between; }}
  .news-title {{ font-size: 1.2em; font-weight: bold; margin-bottom: 10px; color: #2980b9; }}
 
  /* Brief 스타일: 리스트 형태 */
  .brief-list {{ background: white; padding: 20px; border-radius: 8px; }}
  .brief-item {{ border-bottom: 1px solid #eee; padding: 10px 0; }}
  .brief-item:last-child {{ border-bottom: none; }}
 
  .source {{ font-size: 0.85em; color: #7f8c8d; margin-top: 10px; text-align: right; }}
  .summary {{ line-height: 1.6; text-align: justify; }}

  /* 아카이브 드롭다운 스타일 */
  .archive-selector {{ position: absolute; top: 20px; right: 20px; }}
  .archive-selector select {{ padding: 10px; border-radius: 5px; border: 2px solid #2c3e50; background: white; cursor: pointer; }}

  @media (max-width: 768px) {{ .grid-container {{ grid-template-columns: 1fr; }} .archive-selector {{ position: static; text-align: center; margin-bottom: 20px; }} }}
</style>
</head>
<body>
  <div class="archive-selector">
    {{ARCHIVE_DROPDOWN}}
  </div>
  
  <div class="header">
    <h1>🚀 Daily Tech Insight</h1>
    <p>오늘의 주요 IT 트렌드 심층 분석 - {TODAY}</p>
  </div>

  <div class="section-title">🚨 HEADLINE NEWS</div>
  <!-- 여기에 Headline 기사들 -->

  <div class="section-title">🔥 MAJOR ISSUES</div>
  <div class="grid-container">
    <!-- 여기에 Major News 기사들 (2열 그리드) -->
  </div>

  <div class="section-title">📄 BRIEF & OTHERS</div>
  <div class="brief-list">
    <!-- 여기에 Brief 기사들 -->
  </div>
</body>
</html>

# Input Data

{news_text}
"""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"⚠️ AI 생성 실패: {e}")
        return generate_fallback_html(news_data)


def generate_fallback_html(news_data):
    """AI 실패 시 기본 HTML 생성"""
    print("📝 기본 HTML 생성 중...")
    
    # 날짜 포맷팅
    from datetime import datetime
    today_obj = datetime.now()
    date_display = today_obj.strftime('%Y년 %m월 %d일(%a)').replace('Mon', '월').replace('Tue', '화').replace('Wed', '수').replace('Thu', '목').replace('Fri', '금').replace('Sat', '토').replace('Sun', '일')
    
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

<div class="archive-selector">
  {{{{ARCHIVE_DROPDOWN}}}}
</div>

<div class="header">
  <h1>🚀 Daily Tech Insight</h1>
  <p>{date_display} • 오늘의 주요 IT 트렌드 심층 분석</p>
</div>

<div class="section-title">🔥 주요 뉴스</div>
<div class="grid-container">
"""
    
    # 주요 뉴스 (처음 10개를 2열 그리드로)
    for article in news_data[:10]:
        html += f"""
  <div class="news-card">
    <div class="news-title">{article['title']}</div>
    <div class="news-meta">[{article['category']}] {article['source']} • {article['published']}</div>
    <div class="news-summary">{article['summary'][:250]}...</div>
    <a href="{article['link']}" target="_blank" class="news-link">원문 보기 →</a>
  </div>
"""
    
    html += """
</div>

<div class="section-title">📄 기타 소식</div>
<div class="brief-list">
"""
    
    # 나머지 뉴스 (Brief 형태로)
    for article in news_data[10:20]:
        html += f"""
  <div class="brief-item">
    <div class="brief-title">{article['title']}</div>
    <div class="brief-content">{article['summary'][:150]}... <a href="{article['link']}" target="_blank" class="news-link">더보기</a></div>
    <div class="brief-meta">[{article['category']}] {article['source']} • {article['published']}</div>
  </div>
"""
    
    html += """
</div>

</body>
</html>
"""
    return html


def build_archive_dropdown():
    """아카이브 드롭다운 메뉴 생성"""
    files = sorted(glob(os.path.join(ARCHIVE_DIR, "*.html")), reverse=True)
    options = ""
    
    for f in files:
        date_str = os.path.basename(f).replace(".html", "")
        options += f'<option value="{date_str}.html">{date_str}</option>\n'
    
    dropdown_html = f"""
    <select onchange="if(this.value) location.href='archive/' + this.value">
        <option value="">📅 과거 기사 보기</option>
        {options}
    </select>
    """
    return dropdown_html


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("� Daily Tech News Generator with AI")
    print("=" * 60)
    
    # 폴더 생성
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    
    # 1. 뉴스 수집
    raw_data = fetch_news_data()
    
    if not raw_data:
        print("❌ 수집된 기사가 없습니다.")
        return
    
    # 2. AI 요약 생성
    html_content = generate_html_content(raw_data)
    
    # 3. 아카이브 드롭다운 생성
    archive_menu = build_archive_dropdown()
    
    # 4. HTML에 드롭다운 삽입
    if '{{ARCHIVE_DROPDOWN}}' in html_content:
        full_html = html_content.replace('{{ARCHIVE_DROPDOWN}}', archive_menu)
    else:
        full_html = html_content
    
    # 5. 파일 저장
    # (1) 아카이브 저장
    archive_path = os.path.join(ARCHIVE_DIR, f"{TODAY}.html")
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"✅ Archive 저장: {archive_path}")
    
    # (2) 메인 인덱스 업데이트
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"✅ Index 업데이트: index.html")
    
    print("=" * 60)
    print("✨ 작업 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
