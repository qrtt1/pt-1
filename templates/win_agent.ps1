# Production PowerShell Remote Execution Client
# Features: Self-healing, Auto-restart, Production-ready
$serverUrl = $env:SERVER_URL
if (-not $serverUrl) {{
    $serverUrl = "{base_url}"
}}

# API Token for authentication
$apiToken = "{api_token}"

# Get environment info for stable identification
$hostname = $env:COMPUTERNAME
$username = $env:USERNAME

# Use provided client_id or generate one
$providedClientId = "{client_id}".Trim()
if ($providedClientId) {{
    $stableId = $providedClientId
    Write-Host "Using provided Client ID: $stableId" -ForegroundColor Cyan
}} else {{
    # Generate stable client ID based on hostname:username
    $md5 = [System.Security.Cryptography.MD5]::Create()
    $inputString = "$($hostname.ToLower()):$($username.ToLower())"
    $hash = $md5.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($inputString))
    $hashString = ($hash | ForEach {{ "{{0:x2}}" -f $_ }}) -join ''
    $stableId = $hashString.Substring(0, 12)
    Write-Host "Using auto-generated Client ID: $stableId" -ForegroundColor Yellow
    Write-Host "Tip: Use ?client_id=<name> in URL for custom ID" -ForegroundColor Gray
}}

# Set environment variable for child scripts
$env:PT1_CLIENT_ID = $stableId

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

        # Upload transcript to server silently
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

        Invoke-RestMethod -Uri $uploadUri -Method Post -ContentType "multipart/form-data; boundary=$boundary" -Headers @{{"X-API-Token"=$script:apiToken}} -Body $bodyLines -UseBasicParsing | Out-Null
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
        # Download and save client script to file
        $clientScript = Invoke-RestMethod -Uri "$serverUrl/client_install.ps1" -Headers @{{"X-API-Token"=$apiToken}} -UseBasicParsing
        $clientScriptPath = Join-Path $workDir "$sessionId-client.ps1"
        $clientScript | Out-File -FilePath $clientScriptPath -Encoding UTF8

        # Execute client script
        & powershell -NoProfile -ExecutionPolicy Bypass -File $clientScriptPath

        # Cleanup client script file
        Remove-Item $clientScriptPath -Force -ErrorAction SilentlyContinue

        # Check for graceful exit flag (created by client_install.ps1)
        $gracefulExitFlag = Join-Path $workDir "GRACEFUL_EXIT.flag"
        if (Test-Path $gracefulExitFlag) {{
            Write-Host "[$sessionId] Detected flag: $gracefulExitFlag" -ForegroundColor Gray
            Write-Host "[$sessionId] Received graceful exit signal from server" -ForegroundColor Cyan
            Write-Host "Agent stopping gracefully..." -ForegroundColor Green

            # Clean up flag
            Remove-Item $gracefulExitFlag -Force -ErrorAction SilentlyContinue

            # Exit main loop and stop agent
            break
        }}

        # Normal completion: quiet restart
        Start-Sleep -Seconds 3

    }} catch {{
        $errorMsg = $_.Exception.Message
        $statusCode = $null
        if ($_.Exception.Response) {{
            try {{
                $statusCode = $_.Exception.Response.StatusCode.value__
            }} catch {{}}
        }}

        # Treat 401 as auth failure: stop agent to avoid infinite retries
        if ($statusCode -eq 401 -or $errorMsg -like "*401*Unauthorized*") {{
            Write-Host "[$sessionId] Received 401 Unauthorized, stopping agent (check API token/rotation)" -ForegroundColor Red
            break
        }}

        Write-Host "[$sessionId] Session failed: $errorMsg" -ForegroundColor Red
        Write-Host "[$sessionId] Auto-healing: Retrying in 10 seconds..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
    }} finally {{
        # Stop transcript
        Stop-Transcript | Out-Null

        # Check if skip transcript flag exists
        $skipTranscriptFlag = Join-Path $workDir "SKIP_TRANSCRIPT.flag"
        $shouldUploadTranscript = -not (Test-Path $skipTranscriptFlag)

        if ($shouldUploadTranscript) {{
            # Upload transcript using dedicated function (silent, no output)
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
