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

編輯 `tokens.json`，設定你的 API token：

```json
{
  "tokens": [
    {
      "name": "admin",
      "token": "your-secret-token-here",
      "description": "管理員用 token"
    },
    {
      "name": "ai-agent",
      "token": "another-token-for-ai",
      "description": "AI agent 專用 token"
    }
  ]
}
```

**安全提醒**:
- 使用強度足夠的隨機字串作為 token
- 不要將 `tokens.json` commit 到版本控制
- 不同用途使用不同 token，方便追蹤與管理

### 3. 啟動 Server

```bash
uvicorn main:app --host 0.0.0.0 --port 5566
```

啟動參數說明：
- `--host 0.0.0.0`: 監聽所有網路介面（允許外部連線）
- `--port 5566`: 使用 port 5566（可自訂）
- `--reload`: 開發模式，程式碼變更自動重載（生產環境不建議）

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

## API Token 驗證

除了以下公開端點外，所有 API 都需要提供有效的 API token：
- `GET /` - 服務概述
- `GET /ai_guide` - AI 助理使用指南

### Token 使用方式

支援兩種驗證方式：

**方式 1：X-API-Token header（推薦）**
```bash
curl -H "X-API-Token: your-secret-token-here" \
     http://localhost:5566/command_history
```

**方式 2：Authorization Bearer header**
```bash
curl -H "Authorization: Bearer your-secret-token-here" \
     http://localhost:5566/command_history
```

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

### 服務管理
```bash
# 使用 systemd（Linux）
sudo systemctl enable pt1-server
sudo systemctl start pt1-server

# 使用 supervisor
supervisorctl start pt1-server

# 使用 screen（開發環境）
screen -S pt1
uvicorn main:app --host 0.0.0.0 --port 5566
# Ctrl+A, D to detach
```

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
uvicorn main:app \
  --host 0.0.0.0 \
  --port 5566 \
  --workers 4

# 使用 Gunicorn + Uvicorn workers
gunicorn main:app \
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
├── main.py                    # FastAPI 應用程式入口
├── tokens.json               # API token 設定（不應 commit）
├── routers/                  # API 路由模組
│   ├── commands.py           # 命令管理 API
│   ├── clients.py            # 客戶端管理 API
│   ├── client_registry.py    # Client 註冊與狀態
│   ├── dev_logs.py           # 開發日誌 API
│   └── auth.py               # 驗證邏輯
├── services/                 # 業務邏輯服務
│   ├── command_manager.py    # 命令管理核心
│   └── providers.py          # 依賴注入
├── templates/                # PowerShell 客戶端腳本
│   ├── client_install.ps1    # Client 執行單元
│   ├── win_agent.ps1         # 生產環境 agent
│   └── ai_guide.md           # AI 使用指南範本
└── uploads/                  # 檔案上傳目錄
```

## 更多資源

- **CLI 使用**: 請參考 [README.md](README.md)
- **環境驗證**: 請參考 [VERIFICATION.md](VERIFICATION.md)
- **API 文件**: 啟動 server 後訪問 `/ai_guide`
