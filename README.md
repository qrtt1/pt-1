# PowerShell Remote Execution Service

一個用於 AI 助理遠端執行 PowerShell 指令的診斷服務系統。

## 功能特色

- 🔄 **多 Client 支援**: 基於 hostname:username 的穩定識別
- 📋 **指令佇列管理**: 支援多指令並行執行與狀態追蹤
- 📁 **檔案傳輸**: 支援指令結果檔案上傳與下載
- 🕒 **完整時間線**: created_at → scheduled_at → finished_at
- 🔧 **開發友善**: 一行指令部署、自動日誌上傳
- 🏗️ **模組化架構**: 依賴注入、服務分離

## 快速開始

### 啟動 Server

```bash
# 安裝依賴
pip install -e .

# 啟動服務
uvicorn main:app --host 0.0.0.0 --port 5566
```

### 部署 Client

```powershell
# 標準模式（持續運行）
iwr http://your-server:5566/client_install.ps1 -UseBasicParsing | iex

# 單次執行模式（開發測試）
iwr 'http://your-server:5566/client_install.ps1?single_run=true' -UseBasicParsing | iex
```

## API Token 設定

除了 `/` 與 `/ai_guide` 以外的所有 API 端點都需要提供有效的 API token 進行驗證。

### 設定 Token

1. 複製範本檔案：
```bash
cp tokens.json.example tokens.json
```

2. 編輯 `tokens.json`，加入你的 token：
```json
{
  "tokens": [
    {
      "name": "admin",
      "token": "your-secret-token-here",
      "description": "管理員用 token"
    }
  ]
}
```

### Token 使用方式

API token 支援兩種驗證方式：

**方式 1：使用 X-API-Token header**
```bash
curl -H "X-API-Token: your-secret-token-here" http://localhost:5566/command_history
```

**方式 2：使用 Authorization Bearer header**
```bash
curl -H "Authorization: Bearer your-secret-token-here" http://localhost:5566/command_history
```

### 公開端點（不需要 Token）

以下端點可以直接存取，不需要驗證：
- `GET /` - 服務概述
- `GET /ai_guide` - AI 助理使用指南

## API 使用

所有 API 呼叫（除了 `/` 和 `/ai_guide`）都需要提供 API token。

### 發送指令
```bash
curl -X POST "http://localhost:5566/send_command" \
  -H "Content-Type: application/json" \
  -H "X-API-Token: your-secret-token-here" \
  -d '{"client_id": "client_name", "command": "Get-Process"}'
```

### 查詢結果
```bash
curl -H "X-API-Token: your-secret-token-here" \
  "http://localhost:5566/get_result/{command_id}"
```

### 指令歷史
```bash
curl -H "X-API-Token: your-secret-token-here" \
  "http://localhost:5566/command_history?stable_id=client_name&limit=10"
```

### AI 助理使用指南
```bash
curl "http://localhost:5566/ai_guide"
```
*回傳完整的 Markdown 格式使用指南，包含 API 說明、最佳實踐與範例*

## 專案結構

```
├── main.py              # FastAPI 應用程式入口
├── routers/             # API 路由模組
│   ├── commands.py      # 指令管理 API
│   ├── clients.py       # 客戶端管理
│   └── dev_logs.py      # 開發日誌
├── services/            # 業務邏輯服務
│   ├── command_manager.py  # 指令管理核心
│   └── providers.py     # 依賴注入提供者
├── templates/           # PowerShell 客戶端腳本
└── uploads/            # 檔案上傳目錄
```

## 開發說明

- **完整度**: 75% - 適合開發測試使用
- **架構**: 基於 FastAPI + PowerShell HTTP Client
- **儲存**: 目前使用記憶體暫存，計畫加入持久化
- **部署指南**: 請參考 [VERIFICATION.md](VERIFICATION.md)

## 授權

此專案供學習與開發使用。