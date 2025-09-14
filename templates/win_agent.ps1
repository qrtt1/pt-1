# Production PowerShell Remote Execution Client
# Features: Self-healing, Auto-restart, Production-ready
$serverUrl = $env:SERVER_URL
if (-not $serverUrl) {{
    $serverUrl = "{base_url}"
}}

# Get environment info for stable identification
$hostname = $env:COMPUTERNAME
$username = $env:USERNAME

# Generate stable client ID
$md5 = [System.Security.Cryptography.MD5]::Create()
$inputString = "$($hostname.ToLower()):$($username.ToLower())"
$hash = $md5.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($inputString))
$hashString = ($hash | ForEach {{ "{{0:x2}}" -f $_ }}) -join ''
$stableId = $hashString.Substring(0, 12)

# Create random working directory in temp
$workDirName = "pt1_agent_" + [System.Guid]::NewGuid().ToString("N").Substring(0, 8)
$workDir = Join-Path $env:TEMP $workDirName
New-Item -ItemType Directory -Path $workDir -Force | Out-Null
Set-Location $workDir

Write-Host "===============================================================================" -ForegroundColor Green
Write-Host "                      POWERSHELL AGENT STARTED                               " -ForegroundColor Green
Write-Host "===============================================================================" -ForegroundColor Green
Write-Host "  Client ID   : $stableId" -ForegroundColor Cyan
Write-Host "  Server URL  : $serverUrl" -ForegroundColor Cyan
Write-Host "  Work Dir    : $workDir" -ForegroundColor Cyan
Write-Host "===============================================================================" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Upload transcript function
function Upload-SessionTranscript {{
    param(
        [string]$TranscriptPath,
        [string]$SessionId,
        [string]$ClientId,
        [string]$ServerUrl
    )

    try {{
        if (-not (Test-Path $TranscriptPath)) {{
            return $false
        }}

        # Upload transcript to server (靜默執行)
        $uploadUri = "$ServerUrl/agent_transcript/$ClientId"
        $fileBytes = [System.IO.File]::ReadAllBytes($TranscriptPath)
        $fileEnc = [System.Text.Encoding]::GetEncoding('UTF-8').GetString($fileBytes)

        $boundary = [System.Guid]::NewGuid().ToString()
        $LF = "`r`n"
        $bodyLines = (
            "--$boundary",
            "Content-Disposition: form-data; name=`"transcript_file`"; filename=`"$SessionId-transcript.txt`"",
            "Content-Type: text/plain",
            "",
            $fileEnc,
            "--$boundary",
            "Content-Disposition: form-data; name=`"session_id`"",
            "",
            $SessionId,
            "--$boundary--",
            ""
        ) -join $LF

        Invoke-RestMethod -Uri $uploadUri -Method Post -ContentType "multipart/form-data; boundary=$boundary" -Body $bodyLines | Out-Null
        return $true
    }} catch {{
        return $false
    }}
}}

# Main execution loop with self-healing and auto-restart
$sessionCount = 0

while ($true) {{
    $sessionCount++
    $sessionId = "session-{{0:000}}" -f $sessionCount

    # Start transcript for this session
    $transcriptPath = Join-Path $workDir "$sessionId-transcript.txt"
    Start-Transcript -Path $transcriptPath -Force | Out-Null

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
    }} finally {{
        # Stop transcript
        Stop-Transcript | Out-Null

        # Check if skip transcript flag exists
        $skipTranscriptFlag = Join-Path $env:TEMP "SKIP_TRANSCRIPT_$stableId.flag"
        $shouldUploadTranscript = -not (Test-Path $skipTranscriptFlag)

        if ($shouldUploadTranscript) {{
            # Upload transcript using dedicated function (靜默上傳，不顯示訊息)
            $uploadSuccess = Upload-SessionTranscript -TranscriptPath $transcriptPath -SessionId $sessionId -ClientId $stableId -ServerUrl $serverUrl
        }} else {{
            Write-Host "[$sessionId] No command executed - transcript upload skipped" -ForegroundColor Gray
            # Clean up the skip flag
            Remove-Item $skipTranscriptFlag -Force -ErrorAction SilentlyContinue
        }}

        # Clean up transcript file
        if (Test-Path $transcriptPath) {{
            Remove-Item $transcriptPath -Force -ErrorAction SilentlyContinue
        }}
    }}
}}