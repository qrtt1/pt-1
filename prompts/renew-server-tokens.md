# Renew Server Tokens 指南

本文件說明如何更新 PT-1 Server 的 API tokens，包含完整的觀察、確認、執行與驗證流程。

## Token 機制概述

PT-1 使用雙層 token 架構：

1. **Refresh Token** (`tokens.json`)
   - 長效期 token，預設 7 天輪替
   - 用於換取 session token
   - 儲存在 server 端 `tokens.json` 檔案

2. **Session Token** (`.session_tokens.json`)
   - 短效期 token，預設 1 小時
   - 用於 API 呼叫
   - Server 重啟會從檔案載入未過期的 sessions

## Renew Token 完整流程

### 第一步：觀察當前狀態

在執行 renew 前，先觀察當前 token 狀態並回報給使用者：

```bash
# 1. 查看當前 tokens.json 內容
ssh pt1 "cd workspace/pt-1 && cat tokens.json"

# 2. 查看服務日誌中的 token 時效資訊
ssh pt1 "sudo journalctl -u powershell-executor.service -n 100 | grep -E 'Active API token|expires at'"

# 3. 檢查 session tokens 數量與詳細資訊
ssh pt1 "cd workspace/pt-1 && if [ -f .session_tokens.json ]; then cat .session_tokens.json | jq 'length'; else echo '0'; fi"

ssh pt1 "cd workspace/pt-1 && if [ -f .session_tokens.json ]; then cat .session_tokens.json | jq -r 'to_entries[] | \"\(.key[0:8])... expires: \(.value.expires_at)\"'; else echo 'No session tokens file'; fi"
```

**觀察重點：**
- 當前 token 的 UUID
- Token 過期時間（UTC）
- 多少個 session tokens 仍有效
- 最後一次 token 輪替時間

### 第二步：回報給使用者

整理觀察結果，回報給使用者確認：

```
當前 Token 狀態報告

Refresh Token 資訊：
- Token UUID: abc123... (前 8 碼)
- 名稱: rotated-token
- 過期時間: 2026-01-07 06:35:03 UTC
- 自動輪替: 604800 秒（7 天）

Session Tokens：
- 檔案中有 N 個 session tokens
- abc123... 已過期（2025-12-30 05:20 UTC）
- def456... 仍有效（2025-12-31 18:00 UTC）

服務狀態：
- 最後重啟: 12 天前
- 服務運行正常

---

執行 Renew 的影響

如果現在執行 renew，會：
✗ 撤銷當前 token
✗ 清除所有 session tokens
✗ 強制所有使用此 token 的 clients/CLI 重新設定
✓ 生成新的隨機 UUID token
✓ 新 token 預設 7 天後過期

確認執行 renew token 嗎？
```

### 第三步：執行 Renew

使用者確認後，執行 renew 操作：

```bash
# 方法 1：一行命令（推薦）
ssh pt1 "cd workspace/pt-1 && rm -f tokens.json .session_tokens.json && sudo systemctl restart powershell-executor.service"

# 方法 2：分步執行（適合除錯）
ssh pt1 "cd workspace/pt-1 && rm -f tokens.json .session_tokens.json"
ssh pt1 "sudo systemctl restart powershell-executor.service"
```

**執行說明：**
- `rm -f tokens.json`: 刪除 refresh token 檔案
- `rm -f .session_tokens.json`: 刪除 session tokens 檔案
- `systemctl restart`: 重啟服務，觸發 token 自動生成

### 第四步：驗證新狀態

確認 renew 成功並取得新 token：

```bash
# 1. 取得新生成的 token
ssh pt1 "cd workspace/pt-1 && cat tokens.json"

# 2. 確認服務正常啟動
ssh pt1 "sudo systemctl status powershell-executor.service"

# 3. 查看日誌確認新 token 已載入
ssh pt1 "sudo journalctl -u powershell-executor.service -n 20"
```

**驗證重點：**
- 新 token UUID 已生成
- 服務狀態為 `active (running)`
- 日誌顯示 `Active API token: <new-uuid>`
- Token 過期時間正確（通常是 7 天後）

### 第五步：更新 Client 配置

所有使用舊 token 的 clients 需要更新：

**方法 1：手動更新（本地 CLI）**

編輯 `~/.pt-1/.env`：
```bash
PT1_SERVER_URL=https://your-server.example.com
PT1_API_TOKEN=<new-token-uuid>
```

驗證更新：
```bash
pt1 auth
```

**方法 2：重新部署（Windows Clients）**

使用新 token 重新生成安裝命令：
```bash
pt1 quickstart <client_id>
```

複製新命令到 Windows PowerShell 執行。

## 完整範例

以下是完整的 renew token 互動範例：

```bash
# === 第一步：觀察 ===
$ ssh pt1 "cd workspace/pt-1 && cat tokens.json"
{
  "tokens": [
    {
      "token": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
      "name": "rotated-token",
      "expires_at": "2026-01-01T00:00:00Z"
    }
  ]
}

# === 第二步：回報並確認 ===
當前 Token: xxxxxxxx... 過期時間: 2026-01-01 00:00:00 UTC
確認執行 renew token 嗎？
> 使用者回覆: renew

# === 第三步：執行 ===
$ ssh pt1 "cd workspace/pt-1 && rm -f tokens.json .session_tokens.json && sudo systemctl restart powershell-executor.service"

# === 第四步：驗證 ===
$ ssh pt1 "cd workspace/pt-1 && cat tokens.json"
{
  "tokens": [
    {
      "token": "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy",
      "name": "generated-default",
      "expires_at": "2026-01-07T06:35:03Z"
    }
  ]
}

$ ssh pt1 "sudo systemctl status powershell-executor.service"
● powershell-executor.service - PowerShell Remote Execution Service
     Active: active (running) since <timestamp>
     ...

# === 第五步：更新本地 CLI ===
$ vim ~/.pt-1/.env
# 將 PT1_API_TOKEN 改為新 token

$ pt1 auth
✓ Authentication successful
```

## 常見場景

### 場景 1：Token 洩漏

當懷疑 token 洩漏時，立即執行 renew：

```bash
# 緊急撤銷舊 token
ssh pt1 "cd workspace/pt-1 && rm -f tokens.json .session_tokens.json && sudo systemctl restart powershell-executor.service"

# 取得新 token 並更新所有 clients
ssh pt1 "cd workspace/pt-1 && cat tokens.json"
```

### 場景 2：定期安全更新

建議定期（如每月）執行 token renew 作為安全措施：

```bash
# 可以保留 .session_tokens.json 讓現有 sessions 繼續有效
ssh pt1 "cd workspace/pt-1 && rm -f tokens.json && sudo systemctl restart powershell-executor.service"
```

### 場景 3：測試 Token 機制

在開發或測試環境驗證 token 輪替機制：

```bash
# 執行 renew
ssh pt1 "cd workspace/pt-1 && rm -f tokens.json && sudo systemctl restart powershell-executor.service"

# 驗證舊 token 已失效
pt1 auth  # 應該失敗

# 更新後驗證新 token
pt1 auth  # 應該成功
```

### 場景 4：延長現有 Token 到期時間

當 token 快到期但不想更換 UUID 時，可以只修改到期時間：

**優點：**
- 保留現有 token UUID
- Clients 不需要更新配置
- 不會撤銷 session tokens

**操作步驟：**

```bash
# 1. 查看當前 token 資訊
ssh pt1 "cd workspace/pt-1 && cat tokens.json"

# 2. 備份現有檔案
ssh pt1 "cd workspace/pt-1 && cp tokens.json tokens.json.backup"

# 3. 使用 jq 修改到期時間（延長 30 天）
ssh pt1 "cd workspace/pt-1 && cat tokens.json | jq '.tokens[0].expires_at = \"2026-02-07T00:00:00Z\"' > tokens.json.tmp && mv tokens.json.tmp tokens.json"

# 4. 重啟服務載入新的到期時間
ssh pt1 "sudo systemctl restart powershell-executor.service"

# 5. 驗證更新
ssh pt1 "sudo journalctl -u powershell-executor.service -n 20 | grep 'expires at'"
```

**手動編輯方式（如果沒有 jq）：**

```bash
# 1. 在 server 上直接編輯
ssh pt1 "cd workspace/pt-1 && vim tokens.json"

# 2. 修改 expires_at 欄位到想要的日期
#    例如：從 "2026-01-07T00:00:00Z" 改為 "2026-02-07T00:00:00Z"

# 3. 重啟服務
ssh pt1 "sudo systemctl restart powershell-executor.service"
```

**驗證 token 仍然有效：**

```bash
# 本地 CLI 驗證（不需要更新配置）
pt1 auth

# 應該顯示：
# ✓ Authentication successful
# Token Name: <原本的名稱>
```

**注意事項：**
- 確保 expires_at 格式正確：`YYYY-MM-DDTHH:MM:SSZ`
- 時間必須是 UTC 時區
- **時間必須是未來的日期**，如果設定成過去的時間，系統會自動輪替生成新 token（UUID 會改變）
- 如果 JSON 格式錯誤，server 會無法啟動
- 建議先備份再修改

**如何確認延長成功：**
```bash
# 檢查日誌，應該看到：
# [Auth] Active API token: <原本的UUID> (expires at UTC <新的日期>, rotation every 604800s)

# 如果看到 token UUID 改變了，表示系統認為 token 已過期並自動輪替
# 這種情況下需要：
# 1. 恢復備份：cp tokens.json.backup tokens.json
# 2. 確認日期是未來時間
# 3. 重新修改並重啟
```

## 注意事項

1. **影響範圍**
   - 刪除 `tokens.json` 後，所有使用舊 refresh token 的 clients 會立即失效
   - 現有的 session tokens 也會被清除（如果刪除 `.session_tokens.json`）
   - 需要手動更新所有 clients 的配置

2. **Token 自動生成**
   - 當 `tokens.json` 不存在時，server 啟動會自動生成隨機 UUID
   - 新 token 的預設過期時間為 7 天（可透過 `PT1_TOKEN_ROTATION_SECONDS` 環境變數調整）
   - Token 資訊會在服務啟動日誌中顯示

3. **回滾方案**
   - 建議在 renew 前備份當前 `tokens.json`：
     ```bash
     ssh pt1 "cd workspace/pt-1 && cp tokens.json tokens.json.backup"
     ```
   - 如需回滾，還原備份並重啟：
     ```bash
     ssh pt1 "cd workspace/pt-1 && cp tokens.json.backup tokens.json && sudo systemctl restart powershell-executor.service"
     ```

4. **最佳實踐**
   - 總是先觀察當前狀態再執行
   - 在低峰時段執行 renew
   - 準備好更新所有 clients 的流程
   - 記錄每次 renew 的時間與原因

## 相關檔案

- `tokens.json`: Refresh tokens（手動管理或自動生成）
- `.session_tokens.json`: Session tokens（系統自動管理）
- `tokens.json.example`: Token 檔案範本

## 相關文件

- [Server 部署指南](server-setup.md) - Server 基本部署與設定
- [README.md](../README.md) - CLI 使用說明
