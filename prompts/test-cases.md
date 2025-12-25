# PT-1 CLI 測試案例

這個文件包含多個真實使用情境的測試案例，用於驗證 PT-1 CLI 的完整工作流程。

## 前置條件

1. Server 已經啟動並正常運行
2. CLI 已安裝並設定完成（`~/.pt-1/.env` 包含正確的 `PT1_SERVER_URL` 和 `PT1_API_TOKEN`）
3. 至少有一個 Windows client 已註冊並在線

## 測試案例 1: 系統資訊收集

**目的**: 收集遠端 Windows 機器的基本系統資訊

**步驟**:
```bash
# 1. 驗證連線
pt1 auth

# 2. 查看可用的 clients
pt1 list-clients

# 3. 發送系統資訊查詢命令（替換 <client_id> 為實際的 client ID）
pt1 send <client_id> "Get-ComputerInfo | Select-Object CsName, WindowsVersion, OsArchitecture, TotalPhysicalMemory"

# 4. 等待命令完成並查看結果
pt1 wait <command_id>

# 5. 查看該 client 的命令歷史
pt1 history <client_id> 5
```

**預期結果**:
- `auth` 成功驗證
- `list-clients` 顯示至少一個 ONLINE 的 client
- `send` 返回 command_id
- `wait` 顯示系統資訊（電腦名稱、Windows 版本、架構、記憶體）
- `history` 顯示最近 5 條命令記錄

---

## 測試案例 2: Process 監控與 CSV 匯出

**目的**: 收集 process 資訊並匯出為 CSV 檔案下載

**步驟**:
```bash
# 1. 發送命令產生 CSV 檔案
pt1 send <client_id> "Get-Process | Select-Object -First 20 Name, CPU, WorkingSet | Export-Csv -Path processes.csv -NoTypeInformation"

# 2. 等待命令完成
pt1 wait <command_id>

# 3. 列出命令產生的檔案
pt1 list-files <command_id>

# 4. 下載 CSV 檔案
pt1 download <command_id> processes.csv ./downloads/

# 5. 驗證下載的檔案
cat ./downloads/processes.csv
```

**預期結果**:
- 命令成功執行
- `list-files` 顯示 `processes.csv`
- 檔案成功下載到 `./downloads/` 目錄
- CSV 檔案包含 process 資訊（Name, CPU, WorkingSet）

---

## 測試案例 3: Service 狀態檢查

**目的**: 檢查特定 Windows service 的狀態

**步驟**:
```bash
# 1. 查詢所有執行中的 services
pt1 send <client_id> "Get-Service | Where-Object {`$_.Status -eq 'Running'} | Select-Object -First 10 Name, DisplayName, Status"

# 2. 等待並查看結果
pt1 wait <command_id>

# 3. 查詢特定 service（例如 Windows Update）
pt1 send <client_id> "Get-Service -Name wuauserv | Select-Object Name, DisplayName, Status, StartType"

# 4. 等待並查看結果
pt1 wait <command_id>
```

**預期結果**:
- 第一個命令顯示前 10 個執行中的 services
- 第二個命令顯示 Windows Update service 的詳細資訊

---

## 測試案例 4: 磁碟空間檢查與報告

**目的**: 檢查磁碟使用情況並產生 JSON 報告

**步驟**:
```bash
# 1. 收集磁碟資訊並匯出為 JSON
pt1 send <client_id> "Get-PSDrive -PSProvider FileSystem | Select-Object Name, Used, Free, @{Name='UsedGB';Expression={[math]::Round(`$_.Used/1GB,2)}}, @{Name='FreeGB';Expression={[math]::Round(`$_.Free/1GB,2)}} | ConvertTo-Json | Out-File disk_report.json"

# 2. 等待命令完成
pt1 wait <command_id>

# 3. 列出產生的檔案
pt1 list-files <command_id>

# 4. 下載 JSON 報告
pt1 download <command_id> disk_report.json

# 5. 查看報告內容
cat disk_report.json | jq '.'
```

**預期結果**:
- 命令成功執行
- JSON 檔案包含磁碟資訊（Name, Used, Free, UsedGB, FreeGB）
- 檔案格式正確可被 jq 解析

---

## 測試案例 5: 錯誤處理與 Transcript 查看

**目的**: 測試錯誤命令的處理並查看執行記錄

**步驟**:
```bash
# 1. 發送一個會失敗的命令
pt1 send <client_id> "Get-NonExistentCommand"

# 2. 等待命令完成（預期失敗）
pt1 wait <command_id>

# 3. 查看詳細的命令歷史（verbose mode）
pt1 history -v <client_id> 3

# 4. 列出該 client 的 transcripts
pt1 list-transcripts <client_id> 5

# 5. 查看最新的 transcript 內容
pt1 get-transcript <transcript_id>
```

**預期結果**:
- 命令執行失敗，顯示錯誤訊息
- `history -v` 顯示詳細的命令執行資訊包括錯誤
- `list-transcripts` 顯示最近的 5 個執行記錄
- `get-transcript` 顯示完整的 PowerShell session transcript，包含錯誤輸出

---

## 測試案例 6: 多 Client 管理

**目的**: 在多個 clients 上執行相同命令並比較結果

**前置條件**: 至少有兩個 clients 在線

**步驟**:
```bash
# 1. 列出所有 clients
pt1 list-clients

# 2. 對第一個 client 執行命令
pt1 send <client_id_1> "Get-ComputerInfo | Select-Object CsName, WindowsVersion"
pt1 wait <command_id_1>

# 3. 對第二個 client 執行相同命令
pt1 send <client_id_2> "Get-ComputerInfo | Select-Object CsName, WindowsVersion"
pt1 wait <command_id_2>

# 4. 比較兩個 clients 的命令歷史
pt1 history <client_id_1> 3
pt1 history <client_id_2> 3
```

**預期結果**:
- 兩個 clients 都成功執行命令
- 各自返回自己的系統資訊
- History 顯示各自的執行記錄

---

## 測試案例 7: Quickstart 工作流程

**目的**: 測試 quickstart 命令產生的安裝指令

**步驟**:
```bash
# 1. 產生 quickstart 安裝命令（自動產生 client ID）
pt1 quickstart

# 2. 產生帶有自訂 client ID 的安裝命令
pt1 quickstart test-machine-01

# 3. 驗證 session token（檢查快取）
cat ~/.pt-1/.session_cache | jq '.'

# 4. 驗證產生的命令格式正確
# 命令格式應為: iwr "https://server/win_agent.ps1?client_id=..." -UseBasicParsing -Headers @{"X-API-Token"="..."} | iex
```

**預期結果**:
- `quickstart` 顯示完整的 PowerShell oneliner
- 自訂 client ID 正確出現在 URL query parameter 中
- Session token 是新產生的（有完整 1 小時有效期）
- `.session_cache` 包含最新的 session token

---

## 測試案例 8: Session Token 自動更新

**目的**: 驗證 session token 的自動 exchange 和快取機制

**步驟**:
```bash
# 1. 清除現有的 session token 快取
rm ~/.pt-1/.session_cache

# 2. 執行需要認證的命令（會自動取得 session token）
pt1 list-clients

# 3. 驗證 session token 已被快取
cat ~/.pt-1/.session_cache | jq '.'

# 4. 再次執行命令（應該 reuse cached token）
pt1 list-clients

# 5. 執行 quickstart（應該強制取得新 token）
pt1 quickstart test-refresh

# 6. 檢查 session token 是否更新
cat ~/.pt-1/.session_cache | jq '.expires_at'
```

**預期結果**:
- 第一次 `list-clients` 取得新的 session token
- `.session_cache` 包含 session token 和過期時間
- 第二次 `list-clients` reuse cached token（不會顯示 "Session token obtained" 訊息）
- `quickstart` 強制取得新 token（顯示 "Session token obtained"）
- 快取中的 `expires_at` 時間更新

---

## 測試案例 9: 長時間運行命令

**目的**: 測試需要較長執行時間的命令

**步驟**:
```bash
# 1. 發送一個需要較長時間的命令
pt1 send <client_id> "Start-Sleep -Seconds 10; Get-Date"

# 2. 使用 wait 等待完成（預設 timeout 5 分鐘）
pt1 wait <command_id>

# 3. 發送另一個長時間命令
pt1 send <client_id> "1..5 | ForEach-Object { Start-Sleep -Seconds 2; Write-Output \"Step `$_\" }"

# 4. 使用自訂 polling interval
pt1 wait <command_id> --interval 1
```

**預期結果**:
- 第一個命令等待 10 秒後顯示當前時間
- `wait` 正確輪詢並在命令完成時顯示結果
- 第二個命令顯示 5 個步驟的輸出
- 自訂 interval 讓輪詢更頻繁

---

## 測試案例 10: 完整工作流程 - 系統健康檢查

**目的**: 綜合多個命令進行完整的系統健康檢查

**步驟**:
```bash
# 1. 驗證環境
pt1 auth
pt1 list-clients

# 2. 收集系統資訊
pt1 send <client_id> "Get-ComputerInfo | ConvertTo-Json | Out-File system_info.json"
SYSINFO_CMD=$!

# 3. 收集 service 狀態
pt1 send <client_id> "Get-Service | Export-Csv services.csv -NoTypeInformation"
SERVICE_CMD=$!

# 4. 收集磁碟資訊
pt1 send <client_id> "Get-PSDrive -PSProvider FileSystem | ConvertTo-Json | Out-File disk_info.json"
DISK_CMD=$!

# 5. 等待所有命令完成（按順序）
pt1 wait <sysinfo_command_id>
pt1 wait <service_command_id>
pt1 wait <disk_command_id>

# 6. 下載所有產生的檔案
pt1 download <sysinfo_command_id> system_info.json ./health_check/
pt1 download <service_command_id> services.csv ./health_check/
pt1 download <disk_command_id> disk_info.json ./health_check/

# 7. 產生報告
ls -lh ./health_check/

# 8. 查看執行歷史
pt1 history <client_id> 10
```

**預期結果**:
- 所有命令成功執行
- 三個檔案都正確產生並下載
- 檔案內容格式正確
- History 顯示完整的執行記錄

---

## 測試環境清理

測試完成後執行：

```bash
# 清理下載的測試檔案
rm -rf ./downloads/ ./health_check/

# （可選）清理 session token 快取
# rm ~/.pt-1/.session_cache
```

---

## 注意事項

1. **Command ID**: 每次執行 `pt1 send` 會返回新的 command_id，需要記錄下來用於後續命令
2. **Client ID**: 使用 `pt1 list-clients` 查看實際的 client ID
3. **PowerShell 語法**: Windows PowerShell 的變數使用 `$` 符號，在 bash 中需要跳脫或使用反引號
4. **檔案路徑**: PowerShell 預設工作目錄為 `C:\Users\<username>\AppData\Local\Temp\pt1_agent_*`
5. **Timeout**: `pt1 wait` 預設 timeout 為 5 分鐘，可用 `--max` 參數調整

---

## 自動化測試腳本範例

```bash
#!/bin/bash
# test_pt1_workflow.sh - 自動化測試腳本

set -e  # 遇到錯誤立即停止

echo "=== PT-1 CLI 自動化測試 ==="

# 1. 驗證連線
echo "1. 驗證連線..."
pt1 auth || exit 1

# 2. 取得第一個 online client
echo "2. 取得 client ID..."
CLIENT_ID=$(pt1 list-clients | grep ONLINE | head -1 | awk '{print $1}')
if [ -z "$CLIENT_ID" ]; then
    echo "錯誤: 沒有 online 的 client"
    exit 1
fi
echo "使用 client: $CLIENT_ID"

# 3. 測試基本命令
echo "3. 測試基本命令..."
CMD_ID=$(pt1 send "$CLIENT_ID" "Get-ComputerInfo | Select-Object CsName" | grep "Command ID:" | awk '{print $3}')
echo "Command ID: $CMD_ID"

# 4. 等待結果
echo "4. 等待命令完成..."
pt1 wait "$CMD_ID"

# 5. 測試檔案操作
echo "5. 測試檔案操作..."
CMD_ID=$(pt1 send "$CLIENT_ID" "Get-Process | Select-Object -First 5 | Export-Csv test.csv -NoTypeInformation" | grep "Command ID:" | awk '{print $3}')
pt1 wait "$CMD_ID"

echo "6. 列出檔案..."
pt1 list-files "$CMD_ID"

echo "7. 下載檔案..."
mkdir -p ./test_output
pt1 download "$CMD_ID" test.csv ./test_output/

# 8. 驗證結果
echo "8. 驗證結果..."
if [ -f "./test_output/test.csv" ]; then
    echo "✓ 檔案下載成功"
    cat ./test_output/test.csv
else
    echo "✗ 檔案下載失敗"
    exit 1
fi

# 清理
rm -rf ./test_output

echo ""
echo "=== 測試完成 ==="
```

執行自動化測試：
```bash
chmod +x test_pt1_workflow.sh
./test_pt1_workflow.sh
```
