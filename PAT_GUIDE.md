# GitHub Personal Access Token (PAT) 생성 가이드

## ⚠️ 문제 발생
GitHub에 푸시할 때 다음 오류가 발생했습니다:
```
refusing to allow a Personal Access Token to update workflow `.github/workflows/daily_job.yml` without `workflow` scope
```

GitHub Actions 워크플로우 파일(`.github/workflows/daily_job.yml`)을 푸시하려면 **워크플로우 권한이 있는 Personal Access Token**이 필요합니다.

## 🔑 Personal Access Token 생성 방법

### 1단계: GitHub Token 페이지 접속
https://github.com/settings/tokens/new

### 2단계: Token 설정
- **Note**: `Daily Tech News Deployment` (토큰 이름)
- **Expiration**: `90 days` 또는 원하는 기간
- **Select scopes**: 다음 권한 선택
  - ✅ `repo` (모든 하위 항목 포함)
  - ✅ `workflow` (중요! 이것이 없으면 Actions 파일 푸시 불가)

### 3단계: Token 생성 및 복사
1. 페이지 하단 **Generate token** 클릭
2. 생성된 토큰 복사 (한 번만 표시되므로 반드시 복사!)
3. 안전한 곳에 저장

### 4단계: Git 자격증명 업데이트

**방법 1: HTTPS URL에 토큰 포함 (간단)**
```bash
git remote set-url origin https://토큰@github.com/namtoppro/Daily_Tech_News.git
git push -u origin main
```

**방법 2: Git Credential Manager 사용 (권장)**
```bash
git push -u origin main
```
푸시 시 Username과 Password를 요청하면:
- Username: `namtoppro`
- Password: `생성한_토큰_붙여넣기`

## 🚨 보안 주의사항
- Token은 비밀번호와 같으니 절대 공유하지 마세요
- `.env` 파일처럼 `.gitignore`에 이미 포함되어 있어 안전합니다
- Token이 노출되면 즉시 GitHub에서 삭제하고 새로 생성하세요

## 다음 단계
Token을 생성하셨으면 알려주세요. 푸시를 도와드리겠습니다!
