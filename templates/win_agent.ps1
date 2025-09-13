# Production PowerShell Remote Execution Client
# Features: Self-healing, Auto-restart, Production-ready
$serverUrl = $env:SERVER_URL
if (-not $serverUrl) {{
    $serverUrl = "{base_url}"
}}

# Create random working directory in temp
$workDirName = "pt1_agent_" + [System.Guid]::NewGuid().ToString("N").Substring(0, 8)
$workDir = Join-Path $env:TEMP $workDirName
New-Item -ItemType Directory -Path $workDir -Force | Out-Null
Set-Location $workDir

Write-Host "===============================================================================" -ForegroundColor Green
Write-Host "                      POWERSHELL AGENT STARTED                               " -ForegroundColor Green
Write-Host "===============================================================================" -ForegroundColor Green
Write-Host "  Server URL  : $serverUrl" -ForegroundColor Cyan
Write-Host "  Work Dir    : $workDir" -ForegroundColor Cyan
Write-Host "===============================================================================" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Main execution loop with self-healing and auto-restart
$sessionCount = 0

while ($true) {{
    $sessionCount++
    $sessionId = "session-{{0:000}}" -f $sessionCount

    try {{
        # 靜默執行客戶端腳本，不顯示 session 資訊
        $clientScript = Invoke-RestMethod -Uri "$serverUrl/client_install.ps1" -UseBasicParsing
        Invoke-Expression $clientScript

        # 正常完成時也靜默，直接重啟
        Start-Sleep -Seconds 3

    }} catch {{
        $errorMsg = $_.Exception.Message
        Write-Host "[$sessionId] Session failed: $errorMsg" -ForegroundColor Red
        Write-Host "[$sessionId] Auto-healing: Retrying in 10 seconds..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
    }}
}}