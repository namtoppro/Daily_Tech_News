# Daily Tech News 자동 수집 및 배포 스크립트
# Deep Research & Imagen 적용 버전

# 1. 환경 설정 (UTF-8 인코딩)
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

# 로그 설정
$LogFile = "d:\anti\git-news\logs\$(Get-Date -Format 'yyyy-MM-dd').log"
$LogDir = Split-Path -Parent $LogFile
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }

function Write-Log {
    param($Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMsg = "$Timestamp - $Message"
    Add-Content -Path $LogFile -Value $LogMsg -Encoding UTF8
    Write-Host $LogMsg
}

Write-Log "=========================================="
Write-Log "Daily Tech News (Premium) 작업 시작"
Write-Log "=========================================="

# 작업 디렉토리 이동
Set-Location "d:\anti\git-news"

# 2. Python 스크립트 실행 (generator2.py)
Write-Log "Step 1: Python 뉴스 생성기 실행 (Deep Research 진행 중...)"

try {
    # 실행 시간 3~5분 소요 가능 (Deep Research)
    $process = Start-Process -FilePath "python" -ArgumentList "generator2.py" -NoNewWindow -Wait -PassThru -RedirectStandardOutput "temp_output.txt" -RedirectStandardError "temp_error.txt"
    
    # 로그 기록
    if (Test-Path "temp_output.txt") {
        $out = Get-Content "temp_output.txt" -Encoding UTF8 -Raw
        if ($out) { $out -split "`n" | ForEach-Object { if($_ -match "\S") { Write-Log "[Py] $_" } } }
        Remove-Item "temp_output.txt" -Force
    }
    if (Test-Path "temp_error.txt") {
        $err = Get-Content "temp_error.txt" -Encoding UTF8 -Raw
        if ($err) { $err -split "`n" | ForEach-Object { if($_ -match "\S") { Write-Log "[Error] $_" } } }
        Remove-Item "temp_error.txt" -Force
    }

    if ($process.ExitCode -eq 0) {
        Write-Log "SUCCESS: 뉴스 및 이미지 생성 완료"
    } else {
        Write-Log "FAIL: Python 스크립트 오류 (Code: $($process.ExitCode))"
        exit 1
    }
} catch {
    Write-Log "ERROR: 실행 중 예외 발생 - $_"
    exit 1
}

# 3. Git 배포
Write-Log "Step 2: Git 배포 프로세스 시작"

$GitStatus = git status --porcelain
if ([string]::IsNullOrWhiteSpace($GitStatus)) {
    Write-Log "변경사항 없음. 종료합니다."
    exit 0
}

Write-Log "변경사항 감지됨. 배포 진행..."

# 이미지 파일(*.png) 포함하여 모든 파일 추가
git add . 2>&1 | Out-Null
git add *.png 2>$null # 혹시 누락될 경우를 대비해 명시적 추가

$CommitMsg = "Auto-update: $(Get-Date -Format 'yyyy-MM-dd HH:mm') (Deep Research)"
git commit -m $CommitMsg 2>&1 | Out-Null

git push 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Log "SUCCESS: GitHub 배포 완료"
} else {
    Write-Log "FAIL: Git Push 실패"
    exit 1
}

Write-Log "=========================================="
Write-Log "작업 종료"
Write-Log "=========================================="