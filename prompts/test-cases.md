# PT-1 CLI 測試案例

這個文件包含多個真實使用情境的測試案例，用於驗證 PT-1 CLI 的完整工作流程。

## 前置條件

1. Server 已經啟動並正常運行
2. CLI 已安裝並設定完成（`~/.pt-1/.env` 包含正確的 `PT1_SERVER_URL` 和 `PT1_API_TOKEN`）
3. 至少有一個 Windows client 已註冊並在線

**重要提醒**: 所有測試案例都設計為使用一般使用者權限執行，**不需要管理員（Administrator）權限**。測試命令僅讀取系統資訊和在使用者 temp 目錄建立檔案。

---

## Baseline 檢查：建立測試專用 Client

**重要**: 在執行任何測試案例前，請先確保有一個專門用於測試的 client。

### 步驟 1: 檢查是否存在 e2e-tests client

```bash
# 查詢所有 clients
pt1 list-clients

# 檢查是否有 client_id 為 "e2e-tests" 的 client
pt1 list-clients | grep "e2e-tests"
```

### 步驟 2: 如果不存在，建立測試 client

如果上述命令沒有找到 `e2e-tests` client，請執行以下步驟建立：

```bash
# 1. 產生安裝命令
pt1 quickstart e2e-tests

# 2. 複製顯示的 PowerShell oneliner
# 輸出類似：
# iwr "https://server/win_agent.ps1?client_id=e2e-tests" -UseBasicParsing -Headers @{"X-API-Token"="..."} | iex

# 3. 在 Windows 測試機器上執行該命令（PowerShell）
# 注意：以一般使用者權限執行即可，不需要管理員權限
```

### 步驟 3: 驗證 client 已上線

```bash
# 等待約 5-10 秒後檢查
pt1 list-clients | grep "e2e-tests"

# 預期輸出：
# e2e-tests            [ONLINE]        <HOSTNAME>           <USERNAME>      <TIMESTAMP>
```

### 步驟 4: 執行基本健康檢查

```bash
# 發送簡單測試命令
pt1 send e2e-tests "Write-Output 'Test connection successful'"

# 等待結果
pt1 wait <command_id>

# 預期輸出應包含：
# Output:
# --------------------------------------------------------------------------------
# Test connection successful
# --------------------------------------------------------------------------------
```

### 如果 client 建立失敗

**問題排查**：

1. **Server 無法連線**
   ```bash
   # 檢查 server 狀態
   pt1 auth

   # 如果失敗，檢查設定
   cat ~/.pt-1/.env
   ```

2. **PowerShell 腳本執行被阻擋**
   - 在 Windows 上檢查執行原則：
   ```powershell
   Get-ExecutionPolicy

   # 如果是 Restricted，暫時允許：
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
   ```

3. **防火牆問題**
   - 確認 Windows 機器可以連接到 server URL
   - 測試連線：
   ```powershell
   Test-NetConnection -ComputerName <server_hostname> -Port 5566
   ```

4. **Token 過期**
   ```bash
   # 清除 session cache 並重新驗證
   rm ~/.pt-1/.session_cache
   pt1 auth

   # 重新產生 quickstart 命令
   pt1 quickstart e2e-tests
   ```

### Baseline 完成確認

當你看到以下輸出，表示 baseline 已經準備完成：

```bash
$ pt1 list-clients | grep "e2e-tests"
e2e-tests            [ONLINE]        CC827F8BC7AA         testuser        13:45:23 (5s ago)
```

現在可以開始執行以下的測試案例。

**注意**: 後續所有測試案例中的 `<client_id>` 都應該替換為 `e2e-tests`。

---

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

**驗收標準 (Acceptance Criteria)**:
- [ ] `pt1 auth` 回傳 exit code 0，輸出包含 "Authentication successful"
- [ ] `pt1 list-clients` 顯示至少一個狀態為 `[ONLINE]` 的 client
- [ ] `pt1 send` 回傳 exit code 0，輸出包含 "Command ID: <uuid>"
- [ ] `pt1 wait` 回傳 exit code 0，status 顯示 "completed"
- [ ] 輸出包含至少 4 個欄位：CsName, WindowsVersion, OsArchitecture, TotalPhysicalMemory
- [ ] `pt1 history` 顯示表格，包含至少 1 筆記錄，最多 5 筆

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

**驗收標準 (Acceptance Criteria)**:
- [ ] `pt1 send` 回傳 exit code 0
- [ ] `pt1 wait` 回傳 exit code 0，status 為 "completed"
- [ ] `pt1 list-files` 顯示檔案列表，包含 "processes.csv"，檔案大小 > 0
- [ ] `pt1 download` 回傳 exit code 0，檔案儲存至 `./downloads/processes.csv`
- [ ] CSV 檔案包含 header: "Name","CPU","WorkingSet"
- [ ] CSV 檔案至少包含 1 筆資料（不含 header）

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

**驗收標準 (Acceptance Criteria)**:
- [ ] 第一個 `pt1 wait` 回傳 exit code 0，status 為 "completed"
- [ ] 輸出包含 1-10 個 services，每個都有 Name, DisplayName, Status 欄位
- [ ] 所有顯示的 services Status 都是 "Running"
- [ ] 第二個 `pt1 wait` 回傳 exit code 0，status 為 "completed"
- [ ] 輸出包含 wuauserv service 的資訊（Name, DisplayName, Status, StartType）

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

**驗收標準 (Acceptance Criteria)**:
- [ ] `pt1 wait` 回傳 exit code 0，status 為 "completed"
- [ ] `pt1 list-files` 顯示 "disk_report.json"
- [ ] `pt1 download` 成功下載檔案
- [ ] JSON 檔案可被 `jq '.'` 正確解析（valid JSON）
- [ ] JSON 包含至少一個磁碟，每個磁碟有 Name, Used, Free, UsedGB, FreeGB 欄位
- [ ] UsedGB 和 FreeGB 為數字型態

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

**驗收標準 (Acceptance Criteria)**:
- [ ] `pt1 wait` 回傳 exit code 1（命令失敗）
- [ ] 輸出 status 為 "failed" 或 "error"
- [ ] 錯誤訊息包含 "Get-NonExistentCommand" 或類似的錯誤說明
- [ ] `pt1 history -v` 顯示該命令，status 欄位標示為失敗
- [ ] Verbose mode 顯示完整的錯誤資訊
- [ ] `pt1 list-transcripts` 顯示 1-5 筆記錄
- [ ] `pt1 get-transcript` 顯示完整 transcript，包含錯誤輸出和 PowerShell 錯誤堆疊

---

## 測試案例 6: 多 Client Runtime 隔離驗證

**目的**: 驗證同一台機器上的多個 client agents 在 runtime 期間完全獨立運作，互不影響

**前置條件**: 在同一台 Windows 機器上建立兩個 client agents

**步驟**:
```bash
# 1. 建立第二個測試 client（在原有的 Windows 機器上另開 PowerShell）
pt1 quickstart e2e-tests-2

# 2. 在 Windows 機器的新 PowerShell 視窗執行上述命令
# （第一個 e2e-tests client 繼續運行）

# 3. 等待 5-10 秒後，列出所有 clients
pt1 list-clients

# 4. 對兩個 clients 同時發送長時間運行的命令（測試並行執行）
pt1 send e2e-tests "1..10 | ForEach-Object { Start-Sleep -Seconds 1; Write-Output \"Client1-Step-\$_\" }"
CMD1_ID=<command_id_1>

pt1 send e2e-tests-2 "1..10 | ForEach-Object { Start-Sleep -Seconds 1; Write-Output \"Client2-Step-\$_\" }"
CMD2_ID=<command_id_2>

# 5. 同時等待兩個命令（驗證並行執行）
pt1 wait $CMD1_ID &
pt1 wait $CMD2_ID &
wait  # 等待兩個 wait 命令完成

# 6. 驗證兩個命令都成功完成且輸出不混淆
pt1 get-result $CMD1_ID | grep "Client1-Step"
pt1 get-result $CMD2_ID | grep "Client2-Step"

# 7. 對第一個 client 發送會產生檔案的命令
pt1 send e2e-tests "Write-Output 'File from client 1' | Out-File client1.txt"
pt1 wait <command_id_3>

# 8. 對第二個 client 發送會產生檔案的命令（驗證檔案隔離）
pt1 send e2e-tests-2 "Write-Output 'File from client 2' | Out-File client2.txt"
pt1 wait <command_id_4>

# 9. 列出兩個 clients 的檔案（驗證工作目錄隔離）
pt1 list-files <command_id_3>
pt1 list-files <command_id_4>

# 10. 驗證命令歷史完全隔離
pt1 history e2e-tests 10
pt1 history e2e-tests-2 10

# 11. 清理：終止第二個 client
pt1 terminate e2e-tests-2

# 12. 驗證終止一個 client 不影響另一個
sleep 5
pt1 list-clients
pt1 send e2e-tests "Write-Output 'Client 1 still alive'"
pt1 wait <command_id_5>
```

**驗收標準 (Acceptance Criteria)**:
- [ ] `pt1 quickstart e2e-tests-2` 回傳 exit code 0
- [ ] `pt1 list-clients` 顯示 2 個 `[ONLINE]` 的 clients，HOSTNAME 相同但 client_id 不同
- [ ] 兩個長時間命令可以**並行執行**（同時運行，不會互相阻塞）
- [ ] Client1 的輸出只包含 "Client1-Step-1" 到 "Client1-Step-10"
- [ ] Client2 的輸出只包含 "Client2-Step-1" 到 "Client2-Step-10"
- [ ] 兩個輸出沒有混淆（Client1 輸出不包含 Client2 的內容，反之亦然）
- [ ] `pt1 list-files <cmd3>` 只顯示 "client1.txt"
- [ ] `pt1 list-files <cmd4>` 只顯示 "client2.txt"
- [ ] 兩個 client 的工作目錄互相獨立（不同的 temp 目錄）
- [ ] `pt1 history e2e-tests` 只顯示 client 1 的 3 個命令
- [ ] `pt1 history e2e-tests-2` 只顯示 client 2 的 2 個命令
- [ ] History 記錄沒有交叉或混淆
- [ ] `pt1 terminate e2e-tests-2` 成功後，e2e-tests 仍然 ONLINE 且可接收命令
- [ ] 終止 client 2 後，client 1 仍可正常執行命令

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

**驗收標準 (Acceptance Criteria)**:
- [ ] `pt1 quickstart` 回傳 exit code 0
- [ ] 輸出包含 "PowerShell Client Quickstart" 標題
- [ ] 輸出包含完整的 PowerShell oneliner（以 `iwr` 開頭，以 `| iex` 結尾）
- [ ] `pt1 quickstart test-machine-01` 的 URL 包含 `?client_id=test-machine-01`
- [ ] 每次執行 quickstart 都顯示 "Session token obtained" 訊息
- [ ] `~/.pt-1/.session_cache` 的 `expires_at` 時間約為當前時間 + 1 小時
- [ ] PowerShell oneliner 包含 `X-API-Token` header

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

**驗收標準 (Acceptance Criteria)**:
- [ ] 執行 `rm ~/.pt-1/.session_cache` 成功
- [ ] 第一次 `pt1 list-clients` 顯示 "Session token obtained" 訊息
- [ ] `~/.pt-1/.session_cache` 檔案存在且可讀
- [ ] Cache 包含 `session_token`, `expires_at`, `server_url`, `refresh_token` 欄位
- [ ] 第二次 `pt1 list-clients` 不顯示 "Session token obtained" 訊息（reuse）
- [ ] `pt1 quickstart` 顯示 "Session token obtained" 訊息（強制更新）
- [ ] 執行 quickstart 後 `expires_at` 時間更新為新的時間

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

**驗收標準 (Acceptance Criteria)**:
- [ ] 第一個 `pt1 wait` 等待約 10 秒（可觀察到輪詢進度）
- [ ] 命令完成後顯示當前日期時間
- [ ] Status 顯示 "completed"，Duration 約為 10 秒
- [ ] 第二個 `pt1 wait --interval 1` 使用 1 秒輪詢間隔
- [ ] 輸出包含 "Step 1" 到 "Step 5" 五行
- [ ] 兩個命令都回傳 exit code 0

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

**驗收標準 (Acceptance Criteria)**:
- [ ] `pt1 auth` 和 `pt1 list-clients` 都回傳 exit code 0
- [ ] 三個 `pt1 send` 命令都成功，各返回不同的 command_id
- [ ] 三個 `pt1 wait` 都回傳 exit code 0，status 為 "completed"
- [ ] 三個 `pt1 download` 都成功，檔案存在於 `./health_check/` 目錄
- [ ] `system_info.json` 是 valid JSON，包含系統資訊
- [ ] `services.csv` 是 valid CSV，包含至少一筆 service 記錄
- [ ] `disk_info.json` 是 valid JSON，包含磁碟資訊
- [ ] `pt1 history` 顯示至少 3 筆記錄（剛才執行的命令）
- [ ] 所有檔案大小 > 0 bytes

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

# 2. 檢查測試專用 client (e2e-tests)
echo "2. 檢查測試 client..."
CLIENT_ID="e2e-tests"
if ! pt1 list-clients | grep -q "$CLIENT_ID.*ONLINE"; then
    echo "錯誤: 測試 client '$CLIENT_ID' 不存在或未上線"
    echo ""
    echo "請先執行 Baseline 檢查建立測試 client："
    echo "  1. pt1 quickstart e2e-tests"
    echo "  2. 在 Windows 機器執行產生的 PowerShell 命令"
    echo "  3. 確認 client 上線：pt1 list-clients | grep e2e-tests"
    echo ""
    exit 1
fi
echo "✓ 使用測試 client: $CLIENT_ID"

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
