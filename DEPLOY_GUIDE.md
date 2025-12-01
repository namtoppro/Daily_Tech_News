# GitHub 배포 가이드

## 📋 준비 완료된 항목
✅ Git 저장소 초기화 완료  
✅ 모든 파일 커밋 완료 (10개 파일)  
✅ 새로운 디자인 적용 완료

## 🚀 GitHub 배포 단계

### 1️⃣ GitHub 저장소 생성

현재 GitHub 로그인 페이지가 열려있습니다.

**작업 순서:**
1. GitHub 계정으로 로그인
2. 저장소 이름 입력: `git-news` (또는 원하는 이름)
3. Public 선택 (GitHub Pages 무료 사용)
4. **중요**: "Add a README file" 체크 **해제** (이미 로컬에 파일이 있음)
5. "Create repository" 클릭

### 2️⃣ 원격 저장소 연결 (직접 실행 필요)

저장소 생성 후, GitHub에서 보여주는 URL을 복사하여 아래 명령어 실행:

```bash
cd d:\anti\git-news

# 원격 저장소 추가 (HTTPS 방식)
git remote add origin https://github.com/사용자명/git-news.git

# 브랜치 이름을 main으로 변경
git branch -M main

# GitHub에 푸시
git push -u origin main
```

### 3️⃣ GitHub Pages 설정

1. GitHub 저장소 페이지에서 **Settings** 클릭
2. 왼쪽 메뉴에서 **Pages** 클릭
3. Source: **Deploy from a branch**
4. Branch: **main** 선택, 폴더: **/ (root)** 선택
5. **Save** 클릭

약 1-2분 후:
- `https://사용자명.github.io/git-news/` 에서 사이트 접속 가능
- `index.html`이 자동으로 메인 페이지가 됨

### 4️⃣ GitHub Actions 자동화

이미 `.github/workflows/daily_job.yml`이 포함되어 있어 자동화가 설정되어 있습니다!

**중요: API 키 등록**
자동화를 위해 GitHub Secrets에 Gemini API 키를 등록해야 합니다:

1. GitHub 저장소 → **Settings**
2. 왼쪽 메뉴 → **Secrets and variables** → **Actions**
3. **New repository secret** 클릭
4. Name: `GEMINI_API_KEY`
5. Secret: 발급받은 Gemini API 키 입력
6. **Add secret** 클릭

이제 매일 UTC 00:00 (한국시간 오전 9시)에 자동으로 뉴스가 업데이트됩니다!

## 🎯 최종 확인사항

- [ ] GitHub 저장소 생성 완료
- [ ] 원격 저장소 연결 및 푸시 완료
- [ ] GitHub Pages 설정 완료
- [ ] GEMINI_API_KEY Secret 등록 완료
- [ ] 배포된 사이트 접속 확인

## 📧 문제 발생 시

저에게 알려주시면 도와드리겠습니다!
