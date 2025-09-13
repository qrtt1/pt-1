# Production PowerShell Remote Execution Client
# Features: Self-healing, Auto-restart, Production-ready
$serverUrl = $env:SERVER_URL
if (-not $serverUrl) {{
    $serverUrl = "{base_url}"
}}

Write-Host "===============================================================================" -ForegroundColor Green
Write-Host "                   PRODUCTION CLIENT STARTED                                   " -ForegroundColor Green
Write-Host "===============================================================================" -ForegroundColor Green
Write-Host "  Server URL  : $serverUrl" -ForegroundColor Cyan
Write-Host "  Mode        : Production (Self-healing + Auto-restart)" -ForegroundColor Cyan
Write-Host "===============================================================================" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Main execution loop with self-healing and auto-restart
$sessionCount = 0

while ($true) {{
    $sessionCount++
    $sessionId = "session-{{0:000}}" -f $sessionCount

    try {{
        Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Cyan
        Write-Host "[$sessionId] Starting client session..." -ForegroundColor Cyan
        Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Cyan

        Write-Host "[$sessionId] Downloading and executing client script..." -ForegroundColor White
        $clientScript = Invoke-RestMethod -Uri "$serverUrl/client_install.ps1" -UseBasicParsing
        Invoke-Expression $clientScript

        Write-Host "[$sessionId] Client session completed successfully" -ForegroundColor Green
        Write-Host "[$sessionId] Will restart in 3 seconds..." -ForegroundColor Green
        Start-Sleep -Seconds 3

    }} catch {{
        $errorMsg = $_.Exception.Message
        Write-Host "[$sessionId] Session failed: $errorMsg" -ForegroundColor Red

        Write-Host "[$sessionId] Auto-healing: Retrying in 10 seconds..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
    }}
}}