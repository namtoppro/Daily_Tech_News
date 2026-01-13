# Daily Tech News ?ë™ ?˜ì§‘ ë°?ë°°í¬ ?¤í¬ë¦½íŠ¸
# ?‘ì—… ?¤ì?ì¤„ëŸ¬?ì„œ ë§¤ì¼ ?ë™ ?¤í–‰

# UTF-8 ?¸ì½”???¤ì • (?œê? ë°??´ëª¨ì§€ ì§€??
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

# ë¡œê·¸ ?Œì¼ ?¤ì •
$LogFile = "d:\anti\git-news\logs\$(Get-Date -Format 'yyyy-MM-dd').log"
$LogDir = Split-Path -Parent $LogFile
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

function Write-Log {
    param($Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "$Timestamp - $Message"
    # UTF-8ë¡?ë¡œê·¸ ?€??
    Add-Content -Path $LogFile -Value $LogMessage -Encoding UTF8
    Write-Host $LogMessage
}

Write-Log "=========================================="
Write-Log "Daily Tech News ?ë™ ?˜ì§‘ ?œìž‘"
Write-Log "=========================================="

# ?‘ì—… ?”ë ‰? ë¦¬ë¡??´ë™
Set-Location "d:\anti\git-news"
Write-Log "?‘ì—… ?”ë ‰? ë¦¬: $(Get-Location)"

# 1. ?´ìŠ¤ ?˜ì§‘ ë°?HTML ?ì„±
Write-Log "Step 1: ?´ìŠ¤ ?˜ì§‘ ì¤?.."
try {
    # Python??UTF-8 ëª¨ë“œë¡??¤í–‰
    $process = Start-Process -FilePath "python" -ArgumentList "generator2.py" -NoNewWindow -Wait -PassThru -RedirectStandardOutput "temp_output.txt" -RedirectStandardError "temp_error.txt"
    
    # ì¶œë ¥ ?½ê¸° (UTF-8)
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
        Write-Log "SUCCESS: ?´ìŠ¤ ?˜ì§‘ ?±ê³µ"
    }
    else {
        Write-Log "FAIL: ?´ìŠ¤ ?˜ì§‘ ?¤íŒ¨ (Exit Code: $($process.ExitCode))"
        exit 1
    }
}
catch {
    Write-Log "ERROR: ?¤ë¥˜ ë°œìƒ: $_"
    exit 1
}

# 2. Git ë³€ê²½ì‚¬???•ì¸
Write-Log "Step 2: Git ë³€ê²½ì‚¬???•ì¸..."
$GitStatus = git status --porcelain
if ([string]::IsNullOrWhiteSpace($GitStatus)) {
    Write-Log "ë³€ê²½ì‚¬???†ìŒ. ?‘ì—… ì¢…ë£Œ."
    Write-Log "=========================================="
    exit 0
}

Write-Log "ë³€ê²½ëœ ?Œì¼:"
$GitStatus | ForEach-Object { Write-Log "  $_" }

# 3. Git Add
Write-Log "Step 3: Git add ?¤í–‰..."
git add . 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Log "SUCCESS: Git add ?±ê³µ"
}
else {
    Write-Log "FAIL: Git add ?¤íŒ¨"
    exit 1
}

# 4. Git Commit
Write-Log "Step 4: Git commit ?¤í–‰..."
$CommitMessage = "Auto-update news - $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
git commit -m $CommitMessage 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Log "SUCCESS: Git commit ?±ê³µ: $CommitMessage"
}
else {
    Write-Log "FAIL: Git commit ?¤íŒ¨"
    exit 1
}

# 5. Git Push
Write-Log "Step 5: Git push ?¤í–‰..."
git push 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Log "SUCCESS: Git push ?±ê³µ"
}
else {
    Write-Log "FAIL: Git push ?¤íŒ¨"
    exit 1
}

Write-Log "=========================================="
Write-Log "SUCCESS: ëª¨ë“  ?‘ì—… ?„ë£Œ!"
Write-Log "=========================================="
exit 0
