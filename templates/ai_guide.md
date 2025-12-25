# PowerShell Remote Execution Service - AI Assistant Guide

## Service Overview

This is a remote PowerShell execution service designed for AI assistants to execute Windows-specific commands and scripts on remote machines.

**Server URL**: {base_url}

## Core Capabilities

- ✅ Execute PowerShell commands remotely
- ✅ Support multiple concurrent clients
- ✅ File upload/download for command results
- ✅ Command queuing and status tracking
- ✅ Complete command lifecycle monitoring

## Authentication

### Token Architecture

PT-1 使用雙層 token 機制：

1. **Refresh Token (PT1_API_TOKEN)** - 長效期，用於換取 session token
2. **Session Token** - 短效期（1 小時），用於 API 呼叫

### Public Endpoints (No Authentication Required)
- `GET /` - 服務概述
- `GET /ai_guide` - 本指南

### Token Exchange Endpoint (Requires Refresh Token)
- `POST /auth/token/exchange` - 換取 session token

### API Endpoints (Require Session Token)
所有其他 API 端點都需要有效的 session token。

### Authentication Flow

**Step 1: Exchange for Session Token**
```http
POST {base_url}/auth/token/exchange
X-API-Token: your-refresh-token-here

Response:
{{
  "session_token": "uuid-here",
  "expires_at": "2025-12-25T12:00:00Z",
  "token_type": "Bearer",
  "expires_in": 3600
}}
```

**Step 2: Use Session Token for API Calls**

支援兩種驗證方式：

**方式 1：X-API-Token header（推薦）**
```http
X-API-Token: your-session-token-here
```

**方式 2：Authorization Bearer header**
```http
Authorization: Bearer your-session-token-here
```

**Important**: Session tokens expire after 1 hour. When you receive a 401 error, exchange for a new session token.

## API Endpoints

### 1. Send Command
```http
POST {base_url}/send_command
Content-Type: application/json
X-API-Token: your-session-token-here

{{
  "client_id": "target_machine_name",
  "command": "Get-Process | Select-Object -First 5"
}}
```

**Response**:
```json
{{
  "status": "Command queued for target_machine_name",
  "command_id": "uuid-here",
  "timestamp": 1234567890.123
}}
```

### 2. Get Command Result
```http
GET {base_url}/get_result/{{command_id}}
X-API-Token: your-session-token-here
```

**Response**:
```json
{{
  "command_id": "uuid-here",
  "stable_id": "target_machine_name", 
  "command": "Get-Process | Select-Object -First 5",
  "created_at": 1234567890.123,
  "scheduled_at": 1234567890.456,
  "finished_at": 1234567890.789,
  "status": "completed",
  "result": "ProcessName   CPU(s)   Id\n...",
  "result_type": "text",
  "files": []
}}
```

### 3. Command History
```http
GET {base_url}/command_history?stable_id={{client_id}}&limit=10
X-API-Token: your-session-token-here
```

### 4. List Available Clients
```http
GET {base_url}/client_registry
X-API-Token: your-session-token-here
```

**Response**:
```json
{{
  "clients": [
    {{
      "client_id": "client-id-123",
      "hostname": "WORKSTATION-01",
      "username": "admin",
      "stable_id": "client-id-123",
      "first_seen": 1234567890.123,
      "last_seen": 1234567890.456,
      "status": "online"
    }}
  ],
  "online_count": 1,
  "total_count": 1
}}
```

### 5. Agent Transcript Management

**List Agent Transcripts**:
```http
GET {base_url}/agent_transcripts?client_id={{client_id}}&limit=50
X-API-Token: your-session-token-here
```

**Get Agent Transcript Content**:
```http
GET {base_url}/agent_transcript/{{transcript_id}}?format=content
X-API-Token: your-session-token-here
```

**Get Agent Transcript Metadata**:
```http
GET {base_url}/agent_transcript/{{transcript_id}}?format=metadata
X-API-Token: your-session-token-here
```

**Response Example**:
```json
{{
  "transcripts": [
    {{
      "transcript_id": "client-id-123_20240914_143052_123",
      "client_id": "client-id-123",
      "session_id": "session-001",
      "upload_time": "2024-09-14T14:30:52.123456",
      "file_size": 2048,
      "created_time": "2024-09-14T14:30:50.000000"
    }}
  ],
  "count": 1,
  "filtered_by_client": "client-id-123"
}}
```

### 6. Download Result Files
```http
GET {base_url}/download_file/{{command_id}}/{{filename}}
X-API-Token: your-session-token-here
```

## Command Status Flow

1. **pending** → Command created and queued
2. **executing** → Client picked up the command 
3. **completed** → Command finished successfully
4. **failed** → Command execution failed

## Best Practices for AI Assistants

### ✅ DO

1. **Always check command status** before assuming completion:
   ```bash
   # Poll result endpoint until status is 'completed' or 'failed'
   curl -H "X-API-Token: your-session-token-here" "{base_url}/get_result/{{command_id}}"
   ```

2. **Use descriptive client_id** based on the target machine:
   - Use hostname or meaningful identifier
   - Client ID is automatically generated from hostname:username on client side

3. **Handle file results appropriately**:
   - Check `result_type` field: "text", "json", "file", "files", "mixed"
   - Download files using `/download_file/{{command_id}}/{{filename}}`
   - **Debugging**: Check `files` array for execution transcripts and output files
   - **Transcript logs**: May contain additional execution details not in `result` field

4. **Use appropriate PowerShell commands**:
   ```powershell
   # Good: Structured output
   Get-Process | ConvertTo-Json
   Get-Service | Export-Csv -Path "services.csv"

   # Good: Error handling
   try {{ Get-WmiObject -Class Win32_Service }} catch {{ $_.Exception.Message }}
   ```

5. **Monitor agent transcripts for debugging**:
   ```bash
   # List recent transcripts for a client
   curl -H "X-API-Token: your-session-token-here" \
     "{base_url}/agent_transcripts?client_id=client-id-123&limit=5"

   # Get full transcript content for debugging
   curl -H "X-API-Token: your-session-token-here" \
     "{base_url}/agent_transcript/{{transcript_id}}?format=content"

   # When to check transcripts:
   # - Command execution fails unexpectedly
   # - Agent appears offline but should be running
   # - Investigating session-level issues
   ```

### ❌ DON'T

1. **Don't assume immediate execution** - commands are queued and may take time
2. **Don't send sensitive data** without proper security measures
3. **Don't ignore error status** - always check if command completed successfully
4. **Don't flood with commands** - respect the queuing system

## Error Handling

### Common Scenarios

1. **Command not found**: Check if client_id exists and is online
2. **Execution timeout**: Command may still be running, check status periodically
3. **PowerShell errors**: Check the `result` field for error details
4. **File upload issues**: Verify file paths exist on client machine
5. **Additional debugging info**: Check command `files` array for transcript logs and output files

### Example Error Response
```json
{{
  "command_id": "uuid-here",
  "status": "failed",
  "result": "Get-InvalidCommand : The term 'Get-InvalidCommand' is not recognized...",
  "result_type": "text"
}}
```

## Security Considerations

⚠️ **Important**: This service requires API token authentication.

- **API Token Required**: All endpoints (except `/` and `/ai_guide`) require valid API token
- **Permissions**: Commands execute with client machine permissions
- **Best Practices**:
  - Keep your API tokens secure and confidential
  - Use different tokens for different clients/purposes
  - Be cautious with system-modifying commands
  - Avoid commands that require interactive input
  - Use HTTPS in production environments

## Client Setup

To add a new Windows machine as a client:

```powershell
# Production deployment (recommended)
iwr '{base_url}/win_agent.ps1' -UseBasicParsing | iex

# Direct execution (development/testing only)
iwr '{base_url}/client_install.ps1' -UseBasicParsing | iex
```

### Client Architecture

- **Production Agent (`win_agent.ps1`)**:
  - **Purpose**: Flow control and session management
  - **Features**: Auto-restart, self-healing, continuous operation
  - **Behavior**: Repeatedly calls the execution unit to maintain persistent connection

- **Execution Unit (`client_install.ps1`)**:
  - **Purpose**: Single command execution
  - **Behavior**: Executes one command, returns result, then exits
  - **Usage**: Called by production agent or used directly for testing

## Example Workflow

```bash
# Set your API token
API_TOKEN="your-secret-token-here"

# 1. Send command
COMMAND_ID=$(curl -s -X POST "{base_url}/send_command" \
  -H "Content-Type: application/json" \
  -H "X-API-Token: $API_TOKEN" \
  -d '{{"client_id": "workstation-01", "command": "Get-ComputerInfo"}}' \
  | jq -r '.command_id')

# 2. Wait and check result
curl -H "X-API-Token: $API_TOKEN" \
  "{base_url}/get_result/$COMMAND_ID"

# 3. If files were created, download them
curl -H "X-API-Token: $API_TOKEN" \
  "{base_url}/list_files/$COMMAND_ID"
curl -H "X-API-Token: $API_TOKEN" \
  "{base_url}/download_file/$COMMAND_ID/output.csv"

# 4. For debugging, check transcript files
curl -H "X-API-Token: $API_TOKEN" \
  "{base_url}/download_file/$COMMAND_ID/transcript_*.txt"
```

## Limitations

- **Memory-based storage**: Commands are lost on server restart
- **No command timeout**: Long-running commands may block client
- **Single PowerShell session**: No persistent variables between commands

---

*Generated by PowerShell Remote Execution Service*
*For support or issues, check the server logs or contact the administrator*