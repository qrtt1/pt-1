# Diagnostic Client
$serverUrl = $env:SERVER_URL
if (-not $serverUrl) {{
    $serverUrl = "{base_url}"
}}
$singleRun = {single_run}

# Get environment info for stable identification
$hostname = $env:COMPUTERNAME
$username = $env:USERNAME

# Generate stable client ID
$md5 = [System.Security.Cryptography.MD5]::Create()
$inputString = "$($hostname.ToLower()):$($username.ToLower())"
$hash = $md5.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($inputString))
$hashString = ($hash | ForEach {{ "{{0:x2}}" -f $_ }}) -join ''
$stableId = $hashString.Substring(0, 12)

# Display startup information
Write-Host "==================================================================================" -ForegroundColor Cyan
Write-Host "                            DIAGNOSTIC CLIENT STARTED                            " -ForegroundColor Cyan
Write-Host "==================================================================================" -ForegroundColor Cyan
Write-Host "  Stable ID   : $stableId                                                   " -ForegroundColor Green
Write-Host "  Hostname    : $hostname                                                       " -ForegroundColor Green
Write-Host "  Username    : $username                                                       " -ForegroundColor Green
Write-Host "  Server URL  : $serverUrl             " -ForegroundColor Green
Write-Host "  Single Run  : $singleRun                                                     " -ForegroundColor Green
Write-Host "==================================================================================" -ForegroundColor Cyan
Write-Host ""

# Register client to server and get stable ID
Write-Host "Registering client to server..." -ForegroundColor Yellow
try {{
    $registerData = @{{
        client_id = $stableId
        hostname = $hostname
        username = $username
    }} | ConvertTo-Json -Compress
    
    $registerResult = Invoke-RestMethod -Uri "$serverUrl/register_client" -Method POST -Body $registerData -ContentType "application/json" -UseBasicParsing
    $registeredStableId = $registerResult.stable_id
    $clientStatus = $registerResult.client_info
    
    Write-Host "==================================================================================" -ForegroundColor Green
    Write-Host "                         CLIENT REGISTRATION SUCCESSFUL                          " -ForegroundColor Green
    Write-Host "==================================================================================" -ForegroundColor Green
    Write-Host "  Stable ID   : $registeredStableId                                           " -ForegroundColor Green
    Write-Host "  Status      : $($clientStatus.status)                                                        " -ForegroundColor Green
    Write-Host "  First Seen  : $(Get-Date $([DateTimeOffset]::FromUnixTimeSeconds($clientStatus.first_seen)).DateTime -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Green
    Write-Host "==================================================================================" -ForegroundColor Green
    Write-Host ""
}} catch {{
    Write-Host "==================================================================================" -ForegroundColor Red
    Write-Host "                         CLIENT REGISTRATION FAILED                              " -ForegroundColor Red
    Write-Host "==================================================================================" -ForegroundColor Red
    Write-Host "  Error       : $($_.Exception.Message)                                      " -ForegroundColor Red
    Write-Host "  Using local Stable ID: $stableId                                          " -ForegroundColor Yellow
    Write-Host "==================================================================================" -ForegroundColor Red
    Write-Host ""
}}

if ($singleRun) {{
    # Single run mode: wait for one command or timeout after 10 seconds
    $timeout = 10
    $elapsed = 0
    $commandExecuted = $false
    
    while ($elapsed -lt $timeout -and -not $commandExecuted) {{
        try {{
            $response = Invoke-RestMethod -Uri "$serverUrl/next_command?client_id=$stableId&hostname=$hostname&username=$username" -Method GET -TimeoutSec 5
            
            if ($response.command) {{
                $commandId = $response.command_id
                Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Yellow
                Write-Host " [$stableId] Executing: $($response.command)" -ForegroundColor Yellow
                if ($commandId) {{ Write-Host " Command ID: $commandId" -ForegroundColor Yellow }}
                Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Yellow
                
                try {{
                    $result = Invoke-Expression $response.command 2>&1 | Out-String
                    $status = "completed"
                }} catch {{
                    $result = $_.Exception.Message
                    $status = "failed"
                }}
                
                Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Magenta
                Write-Host " [$stableId] Result:" -ForegroundColor Magenta
                $result.Split("`n") | ForEach {{ if ($_ -ne "") {{ Write-Host " $_" -ForegroundColor White }} }}
                Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Magenta
                Write-Host ""
                
                # Submit result to server if command_id is available
                if ($commandId) {{
                    try {{
                        $resultData = @{{
                            command_id = $commandId
                            result = $result
                            status = $status
                        }} | ConvertTo-Json -Compress
                        
                        Invoke-RestMethod -Uri "$serverUrl/submit_result" -Method POST -Body $resultData -ContentType "application/json" -UseBasicParsing | Out-Null
                        Write-Host "[$stableId] Result submitted successfully" -ForegroundColor Green
                    }} catch {{
                        Write-Host "[$stableId] Failed to submit result: $($_.Exception.Message)" -ForegroundColor Red
                    }}
                }}
                
                $commandExecuted = $true
                Write-Host "[$stableId] Command executed, exiting single run mode..." -ForegroundColor Green
            }} else {{
                Start-Sleep -Seconds 1
                $elapsed++
            }}
        }} catch {{
            Write-Host "[$stableId] Error checking for commands: $($_.Exception.Message)" -ForegroundColor Red
            Start-Sleep -Seconds 1
            $elapsed++
        }}
    }}
    
    if (-not $commandExecuted) {{
        Write-Host "[$stableId] No command received within $timeout seconds, exiting..." -ForegroundColor Yellow
    }}
}} else {{
    # Continuous mode: keep running until error
    while ($true) {{
        try {{
            # Include session ID in each request
            $response = Invoke-RestMethod -Uri "$serverUrl/next_command?client_id=$stableId&hostname=$hostname&username=$username" -Method GET -TimeoutSec 30
            
            if ($response.command) {{
                $commandId = $response.command_id
                Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Yellow
                Write-Host " [$stableId] Executing: $($response.command)" -ForegroundColor Yellow
                if ($commandId) {{ Write-Host " Command ID: $commandId" -ForegroundColor Yellow }}
                Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Yellow
                
                try {{
                    $result = Invoke-Expression $response.command 2>&1 | Out-String
                    $status = "completed"
                }} catch {{
                    $result = $_.Exception.Message
                    $status = "failed"
                }}
                
                Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Magenta
                Write-Host " [$stableId] Result:" -ForegroundColor Magenta
                $result.Split("`n") | ForEach {{ if ($_ -ne "") {{ Write-Host " $_" -ForegroundColor White }} }}
                Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Magenta
                Write-Host ""
                
                # Submit result to server if command_id is available
                if ($commandId) {{
                    try {{
                        $resultData = @{{
                            command_id = $commandId
                            result = $result
                            status = $status
                        }} | ConvertTo-Json -Compress
                        
                        Invoke-RestMethod -Uri "$serverUrl/submit_result" -Method POST -Body $resultData -ContentType "application/json" -UseBasicParsing | Out-Null
                        Write-Host "[$stableId] Result submitted successfully" -ForegroundColor Green
                    }} catch {{
                        Write-Host "[$stableId] Failed to submit result: $($_.Exception.Message)" -ForegroundColor Red
                    }}
                }}
            }} else {{
                # Silent wait
            }}
            
            Start-Sleep -Seconds 5
        }} catch {{
            Write-Host "==================================================================================" -ForegroundColor Red
            Write-Host "                                CONNECTION ERROR                                 " -ForegroundColor Red
            Write-Host "==================================================================================" -ForegroundColor Red
            Write-Host "  Stable ID   : $stableId                                               " -ForegroundColor Red
            Write-Host "  Error       : $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "  Action      : Exiting client loop...                                              " -ForegroundColor Red
            Write-Host "==================================================================================" -ForegroundColor Red
            break
        }}
    }}
}}

Write-Host "==================================================================================" -ForegroundColor DarkYellow
Write-Host "                             CLIENT DISCONNECTED                                 " -ForegroundColor DarkYellow
Write-Host "  Stable ID   : $stableId                                               " -ForegroundColor DarkYellow
Write-Host "==================================================================================" -ForegroundColor DarkYellow