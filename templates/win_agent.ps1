# Production PowerShell Remote Execution Client
# Features: Self-healing, Command-bound transcript logging, Production-ready
$serverUrl = $env:SERVER_URL
if (-not $serverUrl) {{
    $serverUrl = "{base_url}"
}}

# Production client configuration
$retryInterval = 30          # Retry interval in seconds for failed connections
$heartbeatInterval = 5       # Heartbeat interval for command polling
$maxRetries = 3              # Maximum retries for failed operations

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
Write-Host "=================================================================================" -ForegroundColor Green
Write-Host "                     PRODUCTION CLIENT STARTED                                  " -ForegroundColor Green
Write-Host "=================================================================================" -ForegroundColor Green
Write-Host "  Stable ID   : $stableId" -ForegroundColor Cyan
Write-Host "  Hostname    : $hostname" -ForegroundColor Cyan
Write-Host "  Username    : $username" -ForegroundColor Cyan
Write-Host "  Server URL  : $serverUrl" -ForegroundColor Cyan
Write-Host "  Mode        : Production (Self-healing)" -ForegroundColor Cyan
Write-Host "=================================================================================" -ForegroundColor Green
Write-Host ""

# Enhanced file upload with transcript support
function Upload-ResultFiles {{
    param(
        [string]$CommandId,
        [string]$ServerUrl,
        [string[]]$FilePaths
    )
    
    if (-not $FilePaths -or $FilePaths.Count -eq 0) {{
        return $null
    }}
    
    try {{
        Add-Type -AssemblyName System.Net.Http
        
        $httpClient = [System.Net.Http.HttpClient]::new()
        $form = [System.Net.Http.MultipartFormDataContent]::new()
        
        foreach ($filePath in $FilePaths) {{
            if (Test-Path $filePath) {{
                $fileName = [System.IO.Path]::GetFileName($filePath)
                $fileContent = [System.Net.Http.ByteArrayContent]::new([System.IO.File]::ReadAllBytes($filePath))
                $fileContent.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::Parse("application/octet-stream")
                $form.Add($fileContent, "files", $fileName)
            }}
        }}
        
        $response = $httpClient.PostAsync("$ServerUrl/upload_files/$CommandId", $form).Result
        
        if ($response.IsSuccessStatusCode) {{
            Write-Host "Files uploaded successfully for command $CommandId" -ForegroundColor Green
            return $response.Content.ReadAsStringAsync().Result | ConvertFrom-Json
        }} else {{
            Write-Host "Failed to upload files: $($response.StatusCode)" -ForegroundColor Yellow
            return $null
        }}
        
    }} catch {{
        Write-Host "Error uploading files: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }} finally {{
        if ($httpClient) {{ $httpClient.Dispose() }}
    }}
}}

# Upload transcript with metadata
function Upload-Transcript {{
    param(
        [string]$CommandId,
        [string]$ServerUrl, 
        [string]$TranscriptPath,
        [hashtable]$Metadata = @{{}}
    )
    
    if (-not (Test-Path $TranscriptPath)) {{
        Write-Host "Transcript file not found: $TranscriptPath" -ForegroundColor Yellow
        return $false
    }}
    
    try {{
        Add-Type -AssemblyName System.Net.Http
        
        $httpClient = [System.Net.Http.HttpClient]::new()
        $form = [System.Net.Http.MultipartFormDataContent]::new()
        
        # Add transcript file
        $transcriptContent = [System.Net.Http.ByteArrayContent]::new([System.IO.File]::ReadAllBytes($TranscriptPath))
        $transcriptContent.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::Parse("text/plain")
        $form.Add($transcriptContent, "transcript_file", "transcript.txt")
        
        # Add metadata
        if ($Metadata.Count -gt 0) {{
            $metadataJson = $Metadata | ConvertTo-Json -Compress
            $metadataContent = [System.Net.Http.StringContent]::new($metadataJson)
            $form.Add($metadataContent, "metadata")
        }}
        
        $response = $httpClient.PostAsync("$ServerUrl/upload_transcript/$CommandId", $form).Result
        
        if ($response.IsSuccessStatusCode) {{
            Write-Host "Transcript uploaded successfully for command $CommandId" -ForegroundColor Green
            return $true
        }} else {{
            Write-Host "Failed to upload transcript: $($response.StatusCode)" -ForegroundColor Yellow
            return $false
        }}
        
    }} catch {{
        Write-Host "Error uploading transcript: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }} finally {{
        if ($httpClient) {{ $httpClient.Dispose() }}
    }}
}}

# Execute command with transcript logging
function Execute-CommandWithTranscript {{
    param(
        [string]$Command,
        [string]$CommandId
    )
    
    $transcriptPath = "$env:TEMP\transcript_$CommandId.txt"
    $resultFiles = @()
    $executionStart = Get-Date
    $exitCode = 0
    $errorMessage = $null
    
    try {{
        # Start transcript
        Start-Transcript -Path $transcriptPath -Force | Out-Null
        Write-Host "==================== COMMAND EXECUTION START ====================" -ForegroundColor Cyan
        Write-Host "Command ID: $CommandId" -ForegroundColor Cyan
        Write-Host "Command: $Command" -ForegroundColor Cyan
        Write-Host "Start Time: $executionStart" -ForegroundColor Cyan
        Write-Host "==================================================================" -ForegroundColor Cyan
        
        # Execute the command
        $result = Invoke-Expression $Command 2>&1
        $resultString = $result | Out-String
        
        Write-Host "==================== COMMAND EXECUTION END ======================" -ForegroundColor Cyan
        Write-Host "End Time: $(Get-Date)" -ForegroundColor Cyan
        Write-Host "Duration: $((Get-Date) - $executionStart)" -ForegroundColor Cyan
        Write-Host "==================================================================" -ForegroundColor Cyan
        
        # Check for created files in current directory
        $currentFiles = Get-ChildItem -File | Where-Object {{ $_.LastWriteTime -gt $executionStart }}
        if ($currentFiles) {{
            Write-Host "Files created during execution:" -ForegroundColor Green
            $currentFiles | ForEach-Object {{ 
                Write-Host "  - $($_.Name)" -ForegroundColor Green
                $resultFiles += $_.FullName
            }}
        }}
        
    }} catch {{
        $exitCode = 1
        $errorMessage = $_.Exception.Message
        $resultString = "ERROR: $errorMessage"
        Write-Host "Command execution failed: $errorMessage" -ForegroundColor Red
        
    }} finally {{
        try {{ Stop-Transcript | Out-Null }} catch {{ }}
    }}
    
    $executionEnd = Get-Date
    $duration = $executionEnd - $executionStart
    
    # Prepare metadata
    $metadata = @{{
        execution_start = $executionStart.ToString("yyyy-MM-dd HH:mm:ss")
        execution_end = $executionEnd.ToString("yyyy-MM-dd HH:mm:ss")
        duration_seconds = [math]::Round($duration.TotalSeconds, 2)
        exit_code = $exitCode
        hostname = $hostname
        username = $username
        powershell_version = $PSVersionTable.PSVersion.ToString()
    }}
    
    if ($errorMessage) {{
        $metadata.error_message = $errorMessage
    }}
    
    if ($resultFiles.Count -gt 0) {{
        $metadata.files_created = $resultFiles.Count
    }}
    
    # Upload transcript first
    Upload-Transcript -CommandId $CommandId -ServerUrl $serverUrl -TranscriptPath $transcriptPath -Metadata $metadata
    
    # Upload any result files
    if ($resultFiles.Count -gt 0) {{
        Upload-ResultFiles -CommandId $CommandId -ServerUrl $serverUrl -FilePaths $resultFiles
    }}
    
    # Clean up transcript
    if (Test-Path $transcriptPath) {{
        Remove-Item $transcriptPath -Force -ErrorAction SilentlyContinue
    }}
    
    return @{{
        result = $resultString
        status = if ($exitCode -eq 0) {{ "completed" }} else {{ "failed" }}
        result_type = if ($resultFiles.Count -gt 0) {{ 
            if ($resultString -and $resultString.Trim()) {{ "mixed" }} else {{ if ($resultFiles.Count -gt 1) {{ "files" }} else {{ "file" }} }}
        }} else {{ "text" }}
        metadata = $metadata
    }}
}}

# Enhanced retry mechanism with exponential backoff
function Invoke-WithRetry {{
    param(
        [scriptblock]$ScriptBlock,
        [int]$MaxRetries = $maxRetries,
        [int]$BaseDelay = 5
    )
    
    for ($attempt = 1; $attempt -le $MaxRetries; $attempt++) {{
        try {{
            return & $ScriptBlock
        }} catch {{
            if ($attempt -eq $MaxRetries) {{
                throw $_
            }}
            
            $delay = $BaseDelay * [math]::Pow(2, $attempt - 1)
            Write-Host "Attempt $attempt failed, retrying in $delay seconds..." -ForegroundColor Yellow
            Start-Sleep -Seconds $delay
        }}
    }}
}}

# Main execution loop with self-healing
$consecutiveFailures = 0
$maxConsecutiveFailures = 10

Write-Host "Starting production client loop..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

while ($true) {{
    try {{
        # Get next command with retry
        $response = Invoke-WithRetry {{
            $uri = "$serverUrl/next_command?client_id=$stableId&hostname=$hostname&username=$username"
            Invoke-RestMethod -Uri $uri -Method GET -UseBasicParsing -TimeoutSec 30
        }}
        
        if ($response -and $response.command) {{
            $command = $response.command
            $commandId = $response.command_id
            
            Write-Host "[$((Get-Date).ToString('HH:mm:ss'))] Executing command: $commandId" -ForegroundColor Green
            Write-Host "Command: $command" -ForegroundColor White
            
            # Execute command with full transcript logging
            $executionResult = Execute-CommandWithTranscript -Command $command -CommandId $commandId
            
            # Submit result with retry
            $resultPayload = @{{
                command_id = $commandId
                result = $executionResult.result
                status = $executionResult.status
                result_type = $executionResult.result_type
            }} | ConvertTo-Json -Depth 3
            
            Invoke-WithRetry {{
                Invoke-RestMethod -Uri "$serverUrl/submit_result" -Method POST -Body $resultPayload -ContentType "application/json" -UseBasicParsing
            }}
            
            Write-Host "[$((Get-Date).ToString('HH:mm:ss'))] Command completed: $($executionResult.status)" -ForegroundColor Green
            $consecutiveFailures = 0
            
        }} else {{
            # No command available, normal polling
            Start-Sleep -Seconds $heartbeatInterval
        }}
        
    }} catch {{
        $consecutiveFailures++
        $errorMsg = $_.Exception.Message
        
        Write-Host "[$((Get-Date).ToString('HH:mm:ss'))] Error (failure $consecutiveFailures/$maxConsecutiveFailures): $errorMsg" -ForegroundColor Red
        
        if ($consecutiveFailures -ge $maxConsecutiveFailures) {{
            Write-Host "Too many consecutive failures. Entering extended recovery mode..." -ForegroundColor Red
            Start-Sleep -Seconds ($retryInterval * 2)
            $consecutiveFailures = [math]::Floor($maxConsecutiveFailures / 2)  # Reset but keep some history
        }} else {{
            Start-Sleep -Seconds $retryInterval
        }}
    }}
}}