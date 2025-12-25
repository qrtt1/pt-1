# 開發備忘

## 伺服器設定
- 預設 port：5566
- 啟動指令：`uvicorn main:app --host 0.0.0.0 --port 5566`
- 環境變數：`PUBLIC_URL` - 設定公開存取的 URL（選用）

### 啟動方式
```bash
# 方式 1：先設定環境變數
export PUBLIC_URL=https://your-server.example.com
uvicorn main:app --host 0.0.0.0 --port 5566

# 方式 2：同時設定環境變數和啟動
PUBLIC_URL=https://your-server.example.com uvicorn main:app --host 0.0.0.0 --port 5566
```

如果沒有設定 PUBLIC_URL，伺服器會提示使用者先設定再重啟。

## 客戶端安裝指令
伺服器啟動後會自動顯示安裝指令，統一使用 Public URL：

```powershell
# 標準模式（持續執行）
iwr {PUBLIC_URL}/client_install.ps1 -UseBasicParsing | iex

# 單次執行模式（開發用）
iwr '{PUBLIC_URL}/client_install.ps1?single_run=true' -UseBasicParsing | iex

# 生產環境 agent（自動重啟）
iwr {PUBLIC_URL}/win_agent.ps1 -UseBasicParsing | iex
```

`-UseBasicParsing` 參數用於避免 IE 相容性問題並確保腳本正確下載。

## 測試建議
- `pt1 auth` 驗證 token 與連線
- `pt1 list-clients` 確認 client 連線狀態
- `pt1 send` / `pt1 get-result` 驗證指令傳遞

## 專案結構規範

### 1. 範本檔案管理
- PowerShell 腳本應放在 `templates/` 目錄中，不要直接在 Python 程式碼中撰寫
- 使用範本檔案可以提高可維護性和可讀性
- 範本檔案應使用適當的格式化參數（如 `{client_id}`, `{base_url}` 等）

### 2. Router 模組化
- 每個 endpoint 群組必須建立獨立的 router module 在 `routers/` 目錄中
- 各個 router 透過 `main.py` 使用 `include_router()` 方式引入
- Router 分類建議：
  - `routers/root.py` - 根路由（如首頁）
  - `routers/clients.py` - 客戶端 PowerShell 腳本分發 endpoints
  - `routers/client_registry.py` - 客戶端註冊與狀態管理 endpoints
  - `routers/commands.py` - 命令執行相關 endpoints

### 3. 目錄結構
```
project/
├── main.py              # 主應用程式，負責整合各 router
├── templates/           # PowerShell 腳本範本
│   ├── client_install.ps1
│   └── dev_client_install.ps1
├── routers/             # API 路由模組
│   ├── __init__.py
│   ├── root.py
│   ├── clients.py
│   └── commands.py
└── requirements.txt     # 依賴套件清單
```

### 4. 程式碼組織原則
- 保持 `main.py` 簡潔，主要負責應用程式設定和 router 整合
- 共享狀態（如 `command_queue`）應集中管理
- 每個 router 模組應專注於特定功能領域
- 使用適當的 import 結構避免循環引用

### 5. 開發最佳實踐
- 範本檔案使用 UTF-8 編碼
- Router 使用語義化的標籤和前綴
- 保持一致的錯誤處理格式
- 適當的日誌記錄和除錯資訊
