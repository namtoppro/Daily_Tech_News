# 🚀 Daily Tech News Generator

AI 기반 기술 뉴스 자동 수집 및 분석 시스템

## 📋 주요 기능

- **자동 뉴스 수집**: 14개 주요 IT 뉴스 소스에서 RSS 피드 자동 수집
- **AI 분석**: Google Gemini를 활용한 심층 뉴스 분석 및 요약
- **계층적 분류**: Headline / Major News / Brief 자동 분류
- **아카이브 관리**: 날짜별 과거 기사 자동 저장 및 조회
- **GitHub Actions**: 매일 자동 실행 (스케줄링)

## 🛠️ 설치 방법

### 1. 저장소 클론
```bash
git clone https://github.com/yourusername/git-news.git
cd git-news
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정
```bash
cp .env.example .env
```

`.env` 파일을 열고 Gemini API 키를 입력하세요:
```
GEMINI_API_KEY=your_actual_api_key_here
```

**API 키 발급**: https://aistudio.google.com/app/apikey

## 🚀 사용 방법

### 로컬 실행
```bash
python generator.py
```

실행 결과:
- `index.html`: 최신 뉴스 대시보드
- `archive/YYYY-MM-DD.html`: 날짜별 아카이브

### GitHub Pages로 배포

1. GitHub 저장소 Settings → Pages
2. Source를 `main` 브랜치로 설정
3. `https://yourusername.github.io/git-news/`로 접속

### 자동화 (GitHub Actions)

`.github/workflows/daily_job.yml`이 매일 자동으로 실행됩니다.

**스케줄 수정**: `.github/workflows/daily_job.yml`의 cron 값 변경
```yaml
schedule:
  - cron: '0 0 * * *'  # 매일 UTC 00:00 (KST 09:00)
```

**수동 실행**: GitHub Actions 탭에서 "Run workflow" 클릭

## 📰 뉴스 소스

현재 수집 중인 RSS 피드:
- AWS News, Microsoft Azure (Cloud)
- TechCrunch AI, OpenAI, MIT Tech Review (AI News)
- NVIDIA, Hugging Face (AI/ML)
- Naver D2, Kakao, Line, Woowa Bros, Toss (한국 Tech)

`generator.py`의 `RSS_FEEDS` 리스트에서 추가/제거 가능합니다.

## 📂 프로젝트 구조

```
git-news/
├── .github/workflows/
│   └── daily_job.yml       # GitHub Actions 스케줄러
├── archive/                 # 과거 기사 저장소
├── templates/
│   └── layout.html         # (옵션) 커스텀 템플릿
├── generator.py            # 메인 스크립트
├── requirements.txt        # 의존성 목록
├── .env.example            # 환경 변수 예시
└── README.md
```

## 🔧 커스터마이징

### 뉴스 소스 추가
`generator.py`의 `RSS_FEEDS` 리스트에 추가:
```python
{"name": "새 소스", "url": "https://example.com/feed", "enabled": True, "category": "Tech"}
```

### AI 프롬프트 수정
`generate_html_content()` 함수의 `prompt` 변수를 수정하세요.

### 디자인 변경
AI가 생성하는 HTML 템플릿의 CSS를 프롬프트에서 수정하거나,
`templates/layout.html`을 직접 편집하세요.

## 🌐 라이선스

MIT License

## 📧 문의

이슈나 질문은 GitHub Issues로 남겨주세요.
