# Daily Tech News

맥 기준으로 일간 기술 뉴스 HTML/Markdown 브리핑을 자동 생성하고 GitHub에 반영하는 프로젝트입니다.

## 현재 동작 방식
1. RSS 피드 수집
2. Gemini API로 HTML/Markdown 브리핑 생성
3. `index.html`, `archive/YYYY-MM-DD.html`, `post.md`, `archive/YYYY-MM-DD.md` 갱신
4. 변경 사항이 있으면 git commit / push

## 실행 환경
- macOS
- Python 3.10+
- Git
- Gemini API Key

## 초기 설정
```bash
cd /Users/namtop/data/Daily_Tech_News
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`.env` 파일에 API 키를 넣으세요.

```env
GEMINI_API_KEY=your_api_key
GEMINI_MODEL=gemini-3.1-pro-preview
ARCHIVE_DIR=archive
```

## 수동 실행
```bash
cd /Users/namtop/data/Daily_Tech_News
source .venv/bin/activate
python3 generator2.py
```

## 전체 자동 실행
```bash
cd /Users/namtop/data/Daily_Tech_News
chmod +x run_daily_news.sh
./run_daily_news.sh
```

## 참고
- 기존 `run_daily_news.ps1`는 Windows용 레거시 스크립트입니다.
- 현재 기본 운영 스크립트는 `run_daily_news.sh` 입니다.
- Git push를 하려면 이 맥에서 GitHub 인증이 되어 있어야 합니다.
- 브리핑 품질 규칙은 `QUALITY_RULES.md`를 따릅니다. 핵심 사실 보존이 카드 길이보다 우선입니다.
