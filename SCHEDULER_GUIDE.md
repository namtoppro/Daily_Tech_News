# Windows 작업 스케줄러 설정 가이드

## 📋 개요

매일 오전 9시 10분에 자동으로 다음 작업을 수행합니다:
1. 뉴스 수집 (`python generator.py`)
2. Git 커밋
3. GitHub 푸시

## 🚀 설정 방법

### 1️⃣ 자동 설정 (추천)

**PowerShell을 관리자 권한으로 실행**한 후:

```powershell
cd d:\anti\git-news
.\setup_task_scheduler.ps1
```

이렇게 하면 자동으로 작업 스케줄러가 등록됩니다!

### 2️⃣ 수동 설정

1. **작업 스케줄러 열기**
   - `Win + R` → `taskschd.msc` 입력

2. **작업 만들기**
   - 우측 패널에서 "작업 만들기" 클릭

3. **일반 탭**
   - 이름: `DailyTechNews_AutoUpdate`
   - 설명: `Daily Tech News 자동 수집 및 GitHub 배포`
   - 사용자가 로그온할 때만 실행: 체크
   - 가장 높은 수준의 권한으로 실행: 체크

4. **트리거 탭**
   - 새로 만들기
   - 작업 시작: 일정에 따라
   - 설정: 매일
   - 시작: 오전 9:10
   - 확인

5. **동작 탭**
   - 새로 만들기
   - 동작: 프로그램 시작
   - 프로그램/스크립트: `PowerShell.exe`
   - 인수 추가:
     ```
     -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "d:\anti\git-news\run_daily_news.ps1"
     ```
   - 시작 위치: `d:\anti\git-news`
   - 확인

6. **조건 탭**
   - ✅ 네트워크 사용 가능한 경우에만 시작
   - ✅ AC 전원일 때만 시작: 체크 해제
   - ✅ 배터리 전원 사용 시 중지: 체크 해제

7. **설정 탭**
   - ✅ 예약된 시작을 놓친 경우 가능한 빨리 작업 실행
   - 확인

## 🧪 테스트 실행

**PowerShell에서**:
```powershell
# 작업 스케줄러에 등록된 작업 수동 실행
Start-ScheduledTask -TaskName "DailyTechNews_AutoUpdate"

# 로그 확인
Get-Content "d:\anti\git-news\logs\$(Get-Date -Format 'yyyy-MM-dd').log"
```

**또는 직접 스크립트 실행**:
```powershell
cd d:\anti\git-news
.\run_daily_news.ps1
```

## 📝 로그 확인

로그는 `d:\anti\git-news\logs\` 폴더에 날짜별로 저장됩니다.

**오늘 로그 확인**:
```powershell
notepad "d:\anti\git-news\logs\$(Get-Date -Format 'yyyy-MM-dd').log"
```

## 🔧 문제 해결

### 실행 정책 오류
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 작업 상태 확인
```powershell
Get-ScheduledTask -TaskName "DailyTechNews_AutoUpdate" | Get-ScheduledTaskInfo
```

### 작업 삭제
```powershell
Unregister-ScheduledTask -TaskName "DailyTechNews_AutoUpdate" -Confirm:$false
```

## 📋 작업 수정

실행 시간을 변경하거나 설정을 수정하려면:

1. 작업 스케줄러 열기 (`taskschd.msc`)
2. `DailyTechNews_AutoUpdate` 찾기
3. 우클릭 → 속성
4. 트리거 탭에서 수정

또는 스크립트를 삭제하고 재등록:
```powershell
Unregister-ScheduledTask -TaskName "DailyTechNews_AutoUpdate" -Confirm:$false
.\setup_task_scheduler.ps1
```

## ⚠️ 주의사항

1. **Git 자격증명**: Personal Access Token이 Git에 이미 설정되어 있어야 합니다
2. **Python 환경**: Python이 PATH에 등록되어 있어야 합니다
3. **네트워크**: 인터넷 연결 필요
4. **Gemini API**: `.env` 파일에 API 키가 설정되어 있어야 합니다

## 🎯 확인 완료!

설정이 완료되면 매일 오전 9시 10분에 자동으로:
- 📰 뉴스 수집
- 🤖 AI 분석
- 🌐 GitHub 배포

가 진행됩니다!
