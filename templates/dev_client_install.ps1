# Development Client Auto-Updater with Transcript Logging
$serverUrl = $env:SERVER_URL
if (-not $serverUrl) {{
    $serverUrl = "{base_url}"
}}

Write-Host "Development client auto-updater started"
Write-Host "Server URL: $serverUrl"
Write-Host "Press Ctrl+C to stop"

function Upload-Log {{
    param(
        [string]$ClientId,
        [string]$SessionId,
        [string]$Content
    )
    
    try {{
        $logData = @{{
            client_id = $ClientId
            session_id = $SessionId
            content = $Content
        }} | ConvertTo-Json -Compress
        
        Invoke-RestMethod -Uri "$serverUrl/dev_log" -Method POST -Body $logData -ContentType "application/json" -UseBasicParsing | Out-Null
        Write-Host "[LOG] Uploaded transcript to server" -ForegroundColor Green
    }} catch {{
        Write-Host "[LOG] Failed to upload transcript: $($_.Exception.Message)" -ForegroundColor Yellow
    }}
}}

while ($true) {{
    $clientId = [System.Guid]::NewGuid().ToString()
    $sessionId = [System.Guid]::NewGuid().ToString().Substring(0,8)
    
    # 建立 transcript 檔案路徑
    $transcriptPath = "$env:TEMP\client_transcript_$sessionId.txt"
    
    try {{
        Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Cyan
        Write-Host "[$sessionId] Starting new client session..." -ForegroundColor Cyan
        Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Cyan
        
        # 開始記錄 transcript
        Start-Transcript -Path $transcriptPath -Force | Out-Null
        
        try {{
            Write-Host "Downloading and executing client script..."
            $clientScript = Invoke-RestMethod -Uri "$serverUrl/client_install.ps1?single_run=true" -UseBasicParsing
            Invoke-Expression $clientScript
        }} finally {{
            # 停止記錄 transcript
            try {{ Stop-Transcript | Out-Null }} catch {{ }}
        }}
        
        # 讀取並上傳 transcript
        if (Test-Path $transcriptPath) {{
            $transcriptContent = Get-Content $transcriptPath -Raw -Encoding UTF8
            if ($transcriptContent) {{
                Upload-Log -ClientId $clientId -SessionId $sessionId -Content $transcriptContent
            }}
            # 清理 transcript 檔案
            Remove-Item $transcriptPath -Force -ErrorAction SilentlyContinue
        }}
        
        Write-Host "[$sessionId] Client session completed, will restart in 3 seconds..." -ForegroundColor Green
        Start-Sleep -Seconds 3
        
    }} catch {{
        Write-Host "[$sessionId] Failed to download or execute: $($_.Exception.Message)" -ForegroundColor Red
        
        # 即使失敗也上傳 transcript（如果存在）
        if (Test-Path $transcriptPath) {{
            try {{
                $transcriptContent = Get-Content $transcriptPath -Raw -Encoding UTF8
                if ($transcriptContent) {{
                    Upload-Log -ClientId $clientId -SessionId $sessionId -Content $transcriptContent
                }}
                Remove-Item $transcriptPath -Force -ErrorAction SilentlyContinue
            }} catch {{ }}
        }}
        
        Write-Host "[$sessionId] Retrying in 10 seconds..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
    }}
}}