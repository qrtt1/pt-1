# Server 部署指南

本文件說明如何部署與設定 PT-1 PowerShell Remote Execution Service server 端。

## 系統需求

- Python 3.7+
- pip
- 可連線的網路環境（讓 Windows clients 可以連線）

## 快速安裝

### 1. 安裝相依套件

```bash
# Clone 專案
git clone https://github.com/your-org/pt-1.git
cd pt-1

# 安裝
pip install -e .
```

### 2. 設定 API Token

複製範本檔案並編輯：

```bash
cp tokens.json.example tokens.json
```

編輯 `tokens.json`，設定你的 refresh token：

```json
{
  "tokens": [
    {
      "name": "admin",
      "token": "your-secret-token-here",
      "description": "管理員用 refresh token",
      "rotation_seconds": 604800
    }
  ]
}
```

**Token 機制說明**：

PT-1 使用雙層 token 架構提升安全性：

1. **Refresh Token (PT1_API_TOKEN)**
   - 長效期 token，儲存在 `tokens.json` 中
   - 用於換取 session token
   - 預設 rotation 為 7 天 (604800 秒)
   - CLI 使用者在 `~/.pt-1/.env` 中設定此 token

2. **Session Token**
   - 短效期 token，有效期 1 小時（可用 `PT1_SESSION_TOKEN_DURATION_SECONDS` 環境變數調整）
   - 透過 `POST /auth/token/exchange` 從 refresh token 換取
   - 用於所有 API 呼叫
   - Server 端儲存在記憶體中（server 重啟後所有 session tokens 失效）
   - CLI 會自動快取在 `~/.pt-1/.session_cache`

**安全提醒**:
- 使用強度足夠的隨機字串作為 refresh token（建議使用 UUID）
- 不要將 `tokens.json` commit 到版本控制
- Session token 過期後自動失效，需重新換取
- Server 重啟會清空所有 session tokens（client 需重新連線）

### 3. 啟動 Server

#### 方式 1：使用 pt1-server 命令（推薦）

```bash
pt1-server
```

#### 方式 2：使用 uvicorn

```bash
uvicorn pt1_server.main:app --host 0.0.0.0 --port 5566
```

#### 環境變數設定

可透過環境變數調整 server 設定：

```bash
# 設定 host 與 port（僅適用於 pt1-server 命令）
export PT1_HOST=0.0.0.0
export PT1_PORT=5566
pt1-server

# 設定 session token 有效期（預設 3600 秒 = 1 小時）
export PT1_SESSION_TOKEN_DURATION_SECONDS=7200
pt1-server
```

啟動參數說明：
- `PT1_HOST`: Server 監聽位址（預設：`0.0.0.0`）
- `PT1_PORT`: Server 監聽 port（預設：`5566`）
- `--reload`: 開發模式，程式碼變更自動重載（僅適用 uvicorn，生產環境不建議）

### 4. 驗證 Server

訪問以下端點確認 server 正常運作：

```bash
# 服務概述（無需 token）
curl http://localhost:5566/

# AI 使用指南（無需 token）
curl http://localhost:5566/ai_guide

# 驗證 token（需要有效 token）
curl -H "X-API-Token: your-secret-token-here" \
     http://localhost:5566/client_registry
```

## 服務管理

### Production 環境（使用 systemd）

**程式碼位置**
```bash
# Production deployment path
cd $HOME/workspace/pt-1
```

**更新程式碼並重啟服務**
```bash
# 1. 進入專案目錄
cd $HOME/workspace/pt-1

# 2. 拉取最新程式碼
git fetch origin
git pull origin main

# 3. 重啟服務
sudo systemctl restart powershell-executor.service

# 4. 檢查服務狀態
sudo systemctl status powershell-executor.service
```

**常用 systemctl 命令**
```bash
# 檢查服務狀態
sudo systemctl status powershell-executor.service

# 啟動服務
sudo systemctl start powershell-executor.service

# 停止服務
sudo systemctl stop powershell-executor.service

# 重啟服務
sudo systemctl restart powershell-executor.service

# 查看服務日誌
sudo journalctl -u powershell-executor.service -f

# 開機自動啟動
sudo systemctl enable powershell-executor.service
```

### 開發環境

**直接執行（適合開發測試）**
```bash
# 在專案目錄下
uvicorn pt1_server.main:app --host 0.0.0.0 --port 5566 --reload
```

## API 認證方式

### 公開端點（無需認證）
- `GET /` - 服務概述
- `GET /ai_guide` - AI 助理使用指南

### Token Exchange（使用 Refresh Token）
- `POST /auth/token/exchange` - 用 refresh token 換取 session token

### 一般 API（使用 Session Token）
所有其他 API 端點都需要有效的 session token。

### 使用流程

1. **取得 Session Token**
```bash
# 使用 refresh token 換取 session token
curl -X POST -H "X-API-Token: your-refresh-token-here" \
     http://localhost:5566/auth/token/exchange

# 回應
{
  "session_token": "uuid-here",
  "expires_at": "2025-12-25T12:00:00Z",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

2. **使用 Session Token 呼叫 API**

支援兩種驗證方式：

**方式 1：X-API-Token header（推薦）**
```bash
curl -H "X-API-Token: your-session-token-here" \
     http://localhost:5566/command_history
```

**方式 2：Authorization Bearer header**
```bash
curl -H "Authorization: Bearer your-session-token-here" \
     http://localhost:5566/command_history
```

### CLI 自動處理
CLI 工具（`pt1`）會自動處理 token exchange 與 session token 快取，使用者無需手動管理。

## 主要 API 端點

### 客戶端管理
- `GET /client_registry` - 列出所有註冊的 clients
- `GET /client_install.ps1` - 下載 PowerShell client 腳本
- `GET /win_agent.ps1` - 下載生產環境 agent 腳本

### 命令執行
- `POST /send_command` - 發送 PowerShell 命令到 client
- `GET /get_result/{command_id}` - 查詢命令執行結果
- `GET /command_history` - 查看命令執行歷史

### 檔案管理
- `GET /list_files/{command_id}` - 列出命令產生的檔案
- `GET /download_file/{command_id}/{filename}` - 下載檔案

### 除錯工具
- `GET /agent_transcripts` - 列出 agent 執行記錄
- `GET /agent_transcript/{transcript_id}` - 查看 transcript 內容

完整 API 文件請訪問：`http://your-server:5566/ai_guide`

## 部署 Windows Client

有兩種方式在 Windows 機器上部署 client：

### 方式 1：使用 PT-1 CLI（推薦）

如果已安裝 PT-1 CLI：

```bash
# 產生安裝命令（可自訂 client_id）
pt1 quickstart my-dev-pc

# 複製顯示的命令到 Windows PowerShell 執行
```

### 方式 2：直接使用 Server 端點

在 Windows PowerShell 中執行：

```powershell
# 生產環境部署（持續運行，自動重啟）
iwr http://your-server:5566/win_agent.ps1 -UseBasicParsing | iex

# 開發測試（單次執行）
iwr 'http://your-server:5566/client_install.ps1?single_run=true' -UseBasicParsing | iex
```

### Client 架構說明

- **win_agent.ps1**: 生產環境 agent
  - 提供 session 管理與自動重啟
  - 持續運行，確保連線穩定
  - 推薦用於長期部署

- **client_install.ps1**: 執行單元
  - 單次命令執行
  - 執行完成後退出
  - 適合開發測試

## 資料儲存

目前版本使用記憶體儲存：
- 命令歷史與結果儲存在記憶體
- Server 重啟後資料會遺失
- 上傳的檔案儲存在 `uploads/` 目錄

**注意事項**：
- 定期備份重要的上傳檔案
- 生產環境建議實作持久化儲存
- 考慮設定檔案上傳大小限制

## 生產環境建議

### 安全性
1. 使用 HTTPS（建議搭配 nginx/caddy reverse proxy）
2. 設定強度足夠的 API tokens
3. 限制 server 的網路存取範圍
4. 定期更新 tokens
5. 監控異常的 API 呼叫

### 監控與日誌
```bash
# 查看 uvicorn logs
tail -f /var/log/pt1-server.log

# 監控 client 連線狀態
curl -H "X-API-Token: your-token" \
     http://localhost:5566/client_registry | jq
```

### 效能調校
```bash
# 使用多個 worker processes
uvicorn pt1_server.main:app \
  --host 0.0.0.0 \
  --port 5566 \
  --workers 4

# 使用 Gunicorn + Uvicorn workers
gunicorn pt1_server.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:5566
```

## 疑難排解

### Client 無法連線
1. 檢查 server 是否正常運行：`curl http://your-server:5566/`
2. 確認防火牆設定允許 port 5566
3. 檢查 Windows client 網路連線
4. 確認 client 使用正確的 server URL

### Token 驗證失敗
1. 確認 `tokens.json` 格式正確
2. 檢查 token 字串是否完全一致（注意空白字元）
3. 確認使用正確的 header 格式
4. Server 重啟後 tokens.json 會重新載入

### 檔案上傳失敗
1. 檢查 `uploads/` 目錄權限
2. 確認磁碟空間充足
3. 檢查檔案大小是否超過限制

## 專案結構

```
pt-1/
├── pt1_cli/                  # CLI Component
│   ├── cli.py                # CLI 命令分派器
│   ├── core.py               # 核心功能與設定
│   └── commands/             # 各命令實作
├── pt1_server/               # Server Component
│   ├── main.py               # FastAPI 應用程式入口
│   ├── auth.py               # 認證與 token 管理
│   ├── routers/              # API 路由模組
│   │   ├── commands.py       # 命令管理 API
│   │   ├── clients.py        # 客戶端管理 API
│   │   ├── client_registry.py # Client 註冊與狀態
│   │   ├── transcripts.py    # Transcript 管理 API
│   │   └── auth.py           # 認證邏輯
│   ├── services/             # 業務邏輯服務
│   │   ├── command_manager.py # 命令管理核心
│   │   ├── client_history.py  # 客戶端歷史記錄
│   │   ├── transcript_manager.py # Transcript 管理
│   │   └── providers.py       # 依賴注入
│   └── templates/            # PowerShell 客戶端腳本
│       ├── client_install.ps1 # Client 執行單元
│       ├── win_agent.ps1      # 生產環境 agent
│       └── ai_guide.md        # AI 使用指南範本
├── setup.py                  # Python package 設定
├── tokens.json               # API token 設定（不應 commit）
└── uploads/                  # 檔案上傳目錄
```

專案採用模組化架構，清楚區分 CLI 與 Server 兩個主要 components：

- **pt1_cli**: 客戶端命令列工具，提供使用者介面
- **pt1_server**: 伺服器端 API，處理命令執行與 client 管理

兩個 components 透過 HTTP API 進行通訊。

## Technical Details

### SSH 設定

使用 SSH Agent Forward 方式存取部署主機，不使用 deploy key。

**本地 SSH config 設定** (`~/.ssh/config`):
```
Host pt1
    HostName <your-server-hostname>
    User yourname
    ForwardAgent yes
```

**驗證 SSH 連線**:
```bash
# 測試無密碼登入
ssh pt1 "whoami"

# 測試 sudo 權限
ssh pt1 "sudo systemctl status powershell-executor.service"

# 測試 agent forwarding
ssh pt1 "ssh-add -l"
```

### CLI 工具安裝與設定

```bash
# 在專案目錄安裝
cd /path/to/pt-1
pip install -e .

# 驗證安裝
which pt1
pt1 --help
```

建立 `~/.pt-1/.env` 設定檔：
```bash
mkdir -p ~/.pt-1
cat > ~/.pt-1/.env << 'EOF'
PT1_SERVER_URL=https://your-server.example.com
PT1_API_TOKEN=your-api-token-here
EOF

# 驗證設定
pt1 auth
```

### 部署腳本

完整的自動化部署腳本：

```bash
#!/bin/bash
# deploy.sh - PT-1 部署腳本

set -e  # 遇到錯誤立即停止

echo "=== PT-1 部署流程 ==="

# 1. 檢查本地狀態
echo "1. 檢查本地 git 狀態..."
if ! git diff-index --quiet HEAD --; then
    echo "錯誤：有未提交的修改"
    exit 1
fi

# 2. Push 到 origin
echo "2. Push 到 origin..."
git push origin main

# 3. SSH 到 pt1 同步代碼
echo "3. 同步代碼到 pt1..."
ssh pt1 "cd workspace/pt-1 && git pull"

# 4. 重啟服務
echo "4. 重啟 service..."
ssh pt1 "sudo systemctl restart powershell-executor.service"

# 5. 確認服務狀態
echo "5. 確認服務狀態..."
if ssh pt1 "sudo systemctl is-active --quiet powershell-executor.service"; then
    echo "✓ Service 運行正常"
else
    echo "✗ Service 啟動失敗"
    ssh pt1 "sudo systemctl status powershell-executor.service"
    exit 1
fi

echo ""
echo "=== 部署完成 ==="
echo "✓ 部署流程完成"
```

### 版本管理

```bash
# 查看當前部署版本
ssh pt1 "cd workspace/pt-1 && git log -1 --oneline"

# 切換到特定 commit（回滾）
ssh pt1 "cd workspace/pt-1 && git fetch && git checkout <commit-hash>"
ssh pt1 "sudo systemctl restart powershell-executor.service"

# 回到最新版本
ssh pt1 "cd workspace/pt-1 && git checkout main && git pull"
ssh pt1 "sudo systemctl restart powershell-executor.service"
```

### 驗證部署

```bash
# 查看註冊的 clients
pt1 list-clients

# 發送測試命令
pt1 send test-pc "Get-ComputerInfo | Select-Object CsName, OsArchitecture"

# 查詢結果
pt1 get-result <command_id>

# 查看命令歷史
pt1 history test-pc
```

## 更多資源

- **CLI 使用**: 請參考 [README.md](README.md)
- **API 文件**: 啟動 server 後訪問 `/ai_guide`
