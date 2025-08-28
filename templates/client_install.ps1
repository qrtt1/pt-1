# Diagnostic Client - Client ID: {client_id}
$clientId = "{client_id}"
$sessionId = [System.Guid]::NewGuid().ToString().Substring(0,8)
$serverUrl = $env:SERVER_URL
if (-not $serverUrl) {{
    $serverUrl = "{base_url}"
}}
$singleRun = {single_run}

# Display startup information
Write-Host "==================================================================================" -ForegroundColor Cyan
Write-Host "                            DIAGNOSTIC CLIENT STARTED                            " -ForegroundColor Cyan
Write-Host "==================================================================================" -ForegroundColor Cyan
Write-Host "  Client ID   : $clientId  " -ForegroundColor Green
Write-Host "  Session ID  : $sessionId                                              " -ForegroundColor Green
Write-Host "  Server URL  : $serverUrl             " -ForegroundColor Green
Write-Host "  Single Run  : $singleRun                                                     " -ForegroundColor Green
Write-Host "==================================================================================" -ForegroundColor Cyan
Write-Host ""

if ($singleRun) {{
    # Single run mode: wait for one command or timeout after 10 seconds
    $timeout = 10
    $elapsed = 0
    $commandExecuted = $false
    
    while ($elapsed -lt $timeout -and -not $commandExecuted) {{
        try {{
            $response = Invoke-RestMethod -Uri "$serverUrl/next_command?client_id=$clientId&session_id=$sessionId" -Method GET -TimeoutSec 5
            
            if ($response.command) {{
                Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Yellow
                Write-Host " [$sessionId] Executing: $($response.command)" -ForegroundColor Yellow
                Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Yellow
                
                $result = Invoke-Expression $response.command 2>&1 | Out-String
                
                Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Magenta
                Write-Host " [$sessionId] Result:" -ForegroundColor Magenta
                $result.Split("`n") | ForEach {{ if ($_ -ne "") {{ Write-Host " $_" -ForegroundColor White }} }}
                Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Magenta
                Write-Host ""
                
                $commandExecuted = $true
                Write-Host "[$sessionId] Command executed, exiting single run mode..." -ForegroundColor Green
            }} else {{
                Write-Host "[$sessionId] Waiting for commands... ($elapsed/$timeout seconds)" -ForegroundColor Gray
                Start-Sleep -Seconds 1
                $elapsed++
            }}
        }} catch {{
            Write-Host "[$sessionId] Error checking for commands: $($_.Exception.Message)" -ForegroundColor Red
            Start-Sleep -Seconds 1
            $elapsed++
        }}
    }}
    
    if (-not $commandExecuted) {{
        Write-Host "[$sessionId] No command received within $timeout seconds, exiting..." -ForegroundColor Yellow
    }}
}} else {{
    # Continuous mode: keep running until error
    while ($true) {{
        try {{
            # Include session ID in each request
            $response = Invoke-RestMethod -Uri "$serverUrl/next_command?client_id=$clientId&session_id=$sessionId" -Method GET -TimeoutSec 30
            
            if ($response.command) {{
                Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Yellow
                Write-Host " [$sessionId] Executing: $($response.command)" -ForegroundColor Yellow
                Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Yellow
                
                $result = Invoke-Expression $response.command 2>&1 | Out-String
                
                Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Magenta
                Write-Host " [$sessionId] Result:" -ForegroundColor Magenta
                $result.Split("`n") | ForEach {{ if ($_ -ne "") {{ Write-Host " $_" -ForegroundColor White }} }}
                Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Magenta
                Write-Host ""
            }} else {{
                Write-Host "[$sessionId] Waiting for commands..." -ForegroundColor Gray
            }}
            
            Start-Sleep -Seconds 5
        }} catch {{
            Write-Host "==================================================================================" -ForegroundColor Red
            Write-Host "                                CONNECTION ERROR                                 " -ForegroundColor Red
            Write-Host "==================================================================================" -ForegroundColor Red
            Write-Host "  Session ID  : $sessionId                                              " -ForegroundColor Red
            Write-Host "  Error       : $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "  Action      : Exiting client loop...                                              " -ForegroundColor Red
            Write-Host "==================================================================================" -ForegroundColor Red
            break
        }}
    }}
}}

Write-Host "==================================================================================" -ForegroundColor DarkYellow
Write-Host "                             CLIENT DISCONNECTED                                 " -ForegroundColor DarkYellow
Write-Host "  Session ID  : $sessionId                                              " -ForegroundColor DarkYellow
Write-Host "==================================================================================" -ForegroundColor DarkYellow