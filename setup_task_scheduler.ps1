# Windows 작업 스케줄러 등록 스크립트
# 관리자 권한으로 실행 필요

# 관리자 권한 확인
$IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $IsAdmin) {
    Write-Host "❌ 이 스크립트는 관리자 권한이 필요합니다." -ForegroundColor Red
    Write-Host "PowerShell을 관리자 권한으로 실행한 후 다시 시도하세요." -ForegroundColor Yellow
    pause
    exit
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Daily Tech News 작업 스케줄러 등록" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 작업 설정
$TaskName = "DailyTechNews_AutoUpdate"
$ScriptPath = "d:\anti\git-news\run_daily_news.ps1"
$WorkingDirectory = "d:\anti\git-news"

# 기존 작업 삭제 (있을 경우)
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Write-Host "기존 작업 삭제 중..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "✅ 기존 작업 삭제 완료" -ForegroundColor Green
}

# 작업 실행 동작 정의
$Action = New-ScheduledTaskAction `
    -Execute "PowerShell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ScriptPath`"" `
    -WorkingDirectory $WorkingDirectory

# 트리거 정의: 매일 오전 9시 10분
$Trigger = New-ScheduledTaskTrigger -Daily -At "09:10AM"

# 설정 정의
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2)

# 사용자 계정으로 실행 (현재 로그인한 사용자)
$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType S4U `
    -RunLevel Highest

# 작업 등록
try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Principal $Principal `
        -Description "Daily Tech News 자동 수집 및 GitHub 배포 (매일 오전 9시 10분)"
    
    Write-Host ""
    Write-Host "✅ 작업 스케줄러 등록 완료!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 작업 정보:" -ForegroundColor Cyan
    Write-Host "  - 작업 이름: $TaskName" -ForegroundColor White
    Write-Host "  - 실행 시간: 매일 오전 9시 10분" -ForegroundColor White
    Write-Host "  - 스크립트: $ScriptPath" -ForegroundColor White
    Write-Host "  - 로그 위치: d:\anti\git-news\logs\" -ForegroundColor White
    Write-Host ""
    Write-Host "🔍 작업 확인 방법:" -ForegroundColor Yellow
    Write-Host "  1. 작업 스케줄러 열기 (taskschd.msc)" -ForegroundColor White
    Write-Host "  2. 작업 스케줄러 라이브러리에서 '$TaskName' 검색" -ForegroundColor White
    Write-Host ""
    Write-Host "🧪 수동 테스트 실행:" -ForegroundColor Yellow
    Write-Host "  Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
    Write-Host ""
    
}
catch {
    Write-Host "❌ 작업 등록 실패: $_" -ForegroundColor Red
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
pause
