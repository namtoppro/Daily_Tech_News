#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Tech News Generator with AI (Hybrid Architecture)
- Headline: Deep Research Agent + Imagen 4.0
- Briefing: Gemini 2.5 Flash + Google Search Grounding
"""

import os
import time
import glob
from datetime import datetime, timedelta
import feedparser
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ------------------------------------------------------------------
# 1. 환경 설정
# ------------------------------------------------------------------
load_dotenv()

# Google AI Studio API Key
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    print("⚠️ 경고: GOOGLE_API_KEY가 .env 파일에 설정되지 않았습니다.")

# 클라이언트 초기화
client = genai.Client(api_key=API_KEY)

TODAY = datetime.now().strftime('%Y-%m-%d')
ARCHIVE_DIR = "archive"
IMAGE_FILENAME = "headline_thumb.png"

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
# [스타일 정의] CSS 코드를 문자열 변수로 분리 (SyntaxError 방지)
# ------------------------------------------------------------------
CSS_STYLE = """
/* Modern Dashboard CSS */
:root {
  --primary-color: #2c3e50;
  --accent-color: #e74c3c;
  --highlight-color: #2980b9;
  --bg-color: #f4f6f8;
  --card-bg: #ffffff;
  --text-color: #333333;
  --meta-color: #7f8c8d;
}
body {
  font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
  max-width: 1000px; margin: 0 auto; padding: 20px;
  background: var(--bg-color); color: var(--text-color); line-height: 1.6;
}
.header { text-align: center; margin-bottom: 40px; border-bottom: 3px solid var(--primary-color); padding-bottom: 20px; }
.header h1 { font-size: 2.5rem; margin: 0; color: var(--primary-color); letter-spacing: -1px; }
.header p { font-size: 1.1rem; color: var(--meta-color); margin: 10px 0 0; }

.archive-selector { text-align: right; margin-bottom: 10px; }
.archive-selector select { padding: 8px; border-radius: 5px; }

.section-title { font-size: 1.6em; font-weight: 800; margin: 40px 0 20px; color: var(--primary-color); border-left: 6px solid var(--accent-color); padding-left: 15px; }

/* Headline */
.headline-card { background: var(--card-bg); padding: 30px; border-radius: 12px; box-shadow: 0 8px 20px rgba(0,0,0,0.1); border-top: 6px solid var(--accent-color); margin-bottom: 40px; }
.headline-tag { display: inline-block; background: var(--accent-color); color: white; padding: 5px 12px; border-radius: 20px; font-size: 0.85em; font-weight: bold; margin-bottom: 15px; }
.headline-title { font-size: 2em; font-weight: 800; margin-bottom: 20px; color: #c0392b; line-height: 1.3; }
.headline-image img { width: 100%; max-height: 400px; object-fit: cover; border-radius: 8px; margin-bottom: 20px; }
.headline-content { font-size: 1.05em; color: #444; line-height: 1.8; }

/* Grid */
.grid-container { display: grid; grid-template-columns: repeat(2, 1fr); gap: 25px; }
.news-card { background: var(--card-bg); padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.04); border: 1px solid #eee; transition: transform 0.2s; }
.news-card:hover { transform: translateY(-3px); }
.news-title { font-size: 1.35em; font-weight: 700; margin-bottom: 15px; color: var(--highlight-color); }
.news-meta { font-size: 0.85em; color: var(--meta-color); margin-bottom: 12px; }
.news-summary { font-size: 0.95em; color: #555; text-align: justify; }

/* Brief */
.brief-list { background: var(--card-bg); padding: 10px 25px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
.brief-item { border-bottom: 1px solid #f0f0f0; padding: 18px 0; }
.brief-item:last-child { border-bottom: none; }
.brief-title { font-weight: 700; font-size: 1.1em; color: #2c3e50; margin-bottom: 5px; }
.brief-content { font-size: 0.9em; color: #666; }

@media (max-width: 768px) {
  .grid-container { grid-template-columns: 1fr; }
  .header h1 { font-size: 2rem; }
}
"""

# ------------------------------------------------------------------
# 2. RSS 뉴스 수집
# ------------------------------------------------------------------
def fetch_rss_news():
    print("📡 RSS 피드 데이터 수집 중...")
    articles = []
    cutoff_time = datetime.now() - timedelta(hours=24)

    for feed_info in RSS_FEEDS:
        if not feed_info["enabled"]: continue
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries:
                published = datetime.now()
                # 날짜 파싱 시도
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    published = datetime(*entry.updated_parsed[:6])
                
                if published > cutoff_time:
                    articles.append({
                        "title": entry.title,
                        "link": entry.link,
                        "summary": getattr(entry, "summary", ""),
                        "source": feed_info["name"],
                        "category": feed_info.get("category", "Tech")
                    })
        except Exception as e:
            print(f"  ⚠️ {feed_info['name']} 수집 에러: {e}")
            
    print(f"✅ 총 {len(articles)}개 최신 기사 수집 완료")
    return articles

# ------------------------------------------------------------------
# 3. [AI] 오늘의 헤드라인 주제 선정
# ------------------------------------------------------------------
def select_headline_topic(articles):
    if not articles: return "최신 IT 트렌드"
    
    print("🧠 오늘의 핵심 주제 선정 중...")
    titles = "\n".join([f"- [{a['source']}] {a['title']}" for a in articles[:40]])
    
    prompt = f"""
    다음은 지난 24시간 동안 수집된 테크 뉴스 제목들입니다.
    이 중에서 가장 기술적으로 중요하고 파급력이 큰 '단 하나의 주제'를 선정해주세요.
    
    [뉴스 목록]
    {titles}
    
    답변은 군더더기 없이 주제만 한글로 출력하세요. (예: Gemini 1.5 Pro 출시와 멀티모달 혁신)
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        topic = response.text.strip()
    except:
        topic = articles[0]['title']
        
    print(f"🎯 선정된 주제: {topic}")
    return topic

# ------------------------------------------------------------------
# 4. [솔루션 1] Deep Research & Imagen (헤드라인)
# ------------------------------------------------------------------
def create_premium_headline(topic):
    print(f"🕵️ '{topic}' 심층 조사 시작 (Deep Research)... (약 3~5분 소요)")
    
    headline_content = ""
    
    try:
        # Deep Research Agent 호출
        task = client.interactions.create(
            agent="deep-research-pro-preview-12-2025", 
            input=f"{topic}에 대한 최신 동향, 기술적 특징, 시장 반응, 주요 플레이어를 심층 분석해서 뉴스 리포트 형식으로 작성해줘. 반드시 한국어로 작성해.",
            background=True
        )
        
        while True:
            chk = client.interactions.get(task.id)
            if chk.status == "completed":
                headline_content = chk.outputs[-1].text
                print("\n✅ 심층 리포트 작성 완료")
                break
            elif chk.status == "failed":
                raise Exception(f"Deep Research 실패: {chk.error}")
            
            print(".", end="", flush=True)
            time.sleep(5)
            
    except Exception as e:
        print(f"\n⚠️ Deep Research 에러 (Flash 모델로 대체): {e}")
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{topic}에 대해 자세히 설명해줘.",
            config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())])
        )
        headline_content = resp.text

    # Imagen 썸네일 생성
    print("🎨 AI 썸네일 이미지 생성 중 (Imagen)...")
    try:
        img_prompt = f"Futuristic technology illustration regarding {topic}, high quality, cinematic lighting, professional, 4k, 16:9 aspect ratio, no text"
        img_resp = client.models.generate_images(
            model='imagen-4.0-generate-001',
            prompt=img_prompt,
            config=types.GenerateImagesConfig(number_of_images=1, aspect_ratio="16:9")
        )
        img_resp.generated_images[0].image.save(IMAGE_FILENAME)
        print(f"✅ 이미지 저장 완료: {IMAGE_FILENAME}")
    except Exception as e:
        print(f"⚠️ 이미지 생성 실패: {e}")

    return headline_content

# ------------------------------------------------------------------
# 5. 나머지 뉴스 처리 (Major & Brief)
# ------------------------------------------------------------------
def create_other_news_html(articles, headline_topic):
    print("📰 나머지 뉴스 요약 및 HTML 생성 중...")
    
    news_text = "\n".join([f"[{a['source']}] {a['title']} - {a['link']}" for a in articles])
    
    prompt = f"""
    당신은 IT 뉴스 에디터입니다. 오늘의 메인 주제인 '{headline_topic}'은 이미 다루었으니 제외하세요.
    나머지 뉴스([Source Data])를 바탕으로 아래 두 섹션의 **HTML 코드(div 태그 내용만)**를 작성해주세요.
    
    1. **🔥 MAJOR ISSUES**: 중요한 뉴스 4~6개를 선정. (grid-container, news-card 클래스 사용)
    2. **📄 BRIEF & OTHERS**: 그 외 단신들. (brief-list, brief-item 클래스 사용)
    
    **작성 규칙:**
    - 한국어로 번역 및 요약할 것.
    - Google Search를 사용하여 최신 내용을 보강할 것.
    - 아래 CSS 클래스 구조를 정확히 지킬 것:
      <div class="grid-container"> ... <div class="news-card"> ... </div> ... </div>
      <div class="brief-list"> ... <div class="brief-item"> ... </div> ... </div>
    
    [Source Data]
    {news_text}
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())])
    )
    
    return response.text

# ------------------------------------------------------------------
# 6. 아카이브 드롭다운 (오류 수정됨)
# ------------------------------------------------------------------
def build_archive_dropdown(is_archive=False):
    # 파일 검색
    files = sorted(glob.glob(os.path.join(ARCHIVE_DIR, "*.html")), reverse=True)
    options = ""
    for f in files:
        # 오류가 발생했던 부분을 안전하게 수정: os.path.basename 사용 후 replace
        filename = os.path.basename(f)
        date_str = filename.replace(".html", "")
        options += f'<option value="{date_str}.html">{date_str}</option>\n'
    
    # 드롭다운 동작 스크립트 설정
    js_action = "if(this.value) location.href = this.value" if is_archive else "if(this.value) location.href='archive/' + this.value"
    
    return f"""<div class="archive-selector">
    <select onchange="{js_action}">
        <option value="">📅 과거 뉴스 보기</option>
        {options}
    </select>
</div>"""

# ------------------------------------------------------------------
# 7. 최종 HTML 조립
# ------------------------------------------------------------------
def build_final_html(topic, headline_body, other_news_html):
    date_display = datetime.now().strftime("%Y년 %m월 %d일")
    
    img_tag = ""
    if os.path.exists(IMAGE_FILENAME):
        img_tag = f'<div class="headline-image"><img src="{IMAGE_FILENAME}" alt="AI Generated Image"></div>'
    
    formatted_headline = headline_body.replace("\n-", "<br>• ").replace("\n", "<br>")
    dropdown = build_archive_dropdown(False)

    # .format() 메소드로 HTML 템플릿 완성 (f-string 오류 원천 차단)
    html_template = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Daily Tech Insight - {today}</title>
<style>
{css}
</style>
</head>
<body>

{dropdown}

<div class="header">
  <h1>🚀 Daily Tech Insight</h1>
  <p>{date_display} • AI Deep Research & Analysis</p>
</div>

<div class="headline-card">
  <span class="headline-tag">AI 심층 리포트</span>
  {img_tag}
  <div class="headline-title">{topic}</div>
  <div class="headline-content">
    {formatted_headline}
  </div>
</div>

<div class="section-title">🔥 MAJOR ISSUES</div>
{other_news_html}

<footer style="text-align:center; margin-top:50px; color:#aaa; font-size:0.85em; padding: 20px;">
  Powered by Google Gemini 2.5 Deep Research & Imagen 4.0
</footer>

</body>
</html>
"""
    return html_template.format(
        today=TODAY,
        css=CSS_STYLE,
        dropdown=dropdown,
        date_display=date_display,
        img_tag=img_tag,
        topic=topic,
        formatted_headline=formatted_headline,
        other_news_html=other_news_html
    )

# ------------------------------------------------------------------
# Main Execution
# ------------------------------------------------------------------
def main():
    print("="*50)
    print(" Daily Tech News Generator (Hybrid Edition)")
    print("="*50)
    
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    
    # 1. 뉴스 수집
    articles = fetch_rss_news()
    if not articles:
        print("❌ 수집된 기사가 없습니다.")
        return

    # 2. 주제 선정
    headline_topic = select_headline_topic(articles)
    
    # 3. 헤드라인 심층 생성
    headline_body = create_premium_headline(headline_topic)
    
    # 4. 나머지 뉴스 생성
    other_news_html = create_other_news_html(articles, headline_topic)
    
    # 5. HTML 조립
    final_html = build_final_html(headline_topic, headline_body, other_news_html)
    
    # 6. 파일 저장
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)
    print("✅ index.html 업데이트 완료")
    
    archive_path = os.path.join(ARCHIVE_DIR, f"{TODAY}.html")
    with open(archive_path, "w", encoding="utf-8") as f:
        # 아카이브용은 동일 내용 저장 (필요 시 경로 수정 가능)
        # 아카이브 폴더 내에서는 이미지/CSS 경로가 달라질 수 있으므로 href만 수정
        content_for_archive = final_html.replace('href="archive/', 'href="')
        f.write(content_for_archive)
    print(f"✅ 아카이브 저장 완료: {archive_path}")

if __name__ == "__main__":
    main()