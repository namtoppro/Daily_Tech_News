# Daily Tech News 자동 수집 및 배포 스크립트
# 작업 스케줄러에서 매일 자동 실행

# UTF-8 인코딩 설정 (한글 및 이모지 지원)
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

# 로그 파일 설정
$LogFile = "d:\anti\git-news\logs\$(Get-Date -Format 'yyyy-MM-dd').log"
$LogDir = Split-Path -Parent $LogFile
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

function Write-Log {
    param($Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "$Timestamp - $Message"
    # UTF-8로 로그 저장
    Add-Content -Path $LogFile -Value $LogMessage -Encoding UTF8
    Write-Host $LogMessage
}

Write-Log "=========================================="
Write-Log "Daily Tech News 자동 수집 시작"
Write-Log "=========================================="

# 작업 디렉토리로 이동
Set-Location "d:\anti\git-news"
Write-Log "작업 디렉토리: $(Get-Location)"

# 1. 뉴스 수집 및 HTML 생성
Write-Log "Step 1: 뉴스 수집 중..."
try {
    # Python을 UTF-8 모드로 실행
    $process = Start-Process -FilePath "python" -ArgumentList "generator.py" -NoNewWindow -Wait -PassThru -RedirectStandardOutput "temp_output.txt" -RedirectStandardError "temp_error.txt"
    
    # 출력 읽기 (UTF-8)
    if (Test-Path "temp_output.txt") {
        $output = Get-Content "temp_output.txt" -Encoding UTF8 -Raw
        if ($output) {
            $output -split "`n" | ForEach-Object { Write-Log $_ }
        }
        Remove-Item "temp_output.txt" -Force
    }
    
    if (Test-Path "temp_error.txt") {
        $errors = Get-Content "temp_error.txt" -Encoding UTF8 -Raw
        if ($errors) {
            $errors -split "`n" | ForEach-Object { Write-Log "ERROR: $_" }
        }
        Remove-Item "temp_error.txt" -Force
    }
    
    if ($process.ExitCode -eq 0) {
        Write-Log "SUCCESS: 뉴스 수집 성공"
    }
    else {
        Write-Log "FAIL: 뉴스 수집 실패 (Exit Code: $($process.ExitCode))"
        exit 1
    }
}
catch {
    Write-Log "ERROR: 오류 발생: $_"
    exit 1
}

# 2. Git 변경사항 확인
Write-Log "Step 2: Git 변경사항 확인..."
$GitStatus = git status --porcelain
if ([string]::IsNullOrWhiteSpace($GitStatus)) {
    Write-Log "변경사항 없음. 작업 종료."
    Write-Log "=========================================="
    exit 0
}

Write-Log "변경된 파일:"
$GitStatus | ForEach-Object { Write-Log "  $_" }

# 3. Git Add
Write-Log "Step 3: Git add 실행..."
git add . 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Log "SUCCESS: Git add 성공"
}
else {
    Write-Log "FAIL: Git add 실패"
    exit 1
}

# 4. Git Commit
Write-Log "Step 4: Git commit 실행..."
$CommitMessage = "Auto-update news - $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
git commit -m $CommitMessage 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Log "SUCCESS: Git commit 성공: $CommitMessage"
}
else {
    Write-Log "FAIL: Git commit 실패"
    exit 1
}

# 5. Git Push
Write-Log "Step 5: Git push 실행..."
git push 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Log "SUCCESS: Git push 성공"
}
else {
    Write-Log "FAIL: Git push 실패"
    exit 1
}

Write-Log "=========================================="
Write-Log "SUCCESS: 모든 작업 완료!"
Write-Log "=========================================="
exit 0
