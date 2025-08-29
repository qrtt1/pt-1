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

## API 使用

### 發送指令
```bash
curl -X POST "http://localhost:5566/send_command" \
  -H "Content-Type: application/json" \
  -d '{"client_id": "client_name", "command": "Get-Process"}'
```

### 查詢結果
```bash
curl "http://localhost:5566/get_result/{command_id}"
```

### 指令歷史
```bash
curl "http://localhost:5566/command_history?stable_id=client_name&limit=10"
```

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
- **改善計畫**: 請參考 [TODO.md](TODO.md)

## 授權

此專案供學習與開發使用。