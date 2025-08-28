# FastAPI 診斷伺服器功能清單

## 核心架構

### 🏗️ 模組化設計
- **Router 分離**：按功能區分為獨立的 router 模組
- **範本系統**：PowerShell 腳本使用 templates/ 目錄管理
- **環境變數配置**：透過 `PUBLIC_URL` 環境變數設定公開存取 URL

---

## API Endpoints

### 🏠 根路由 (Root Router)
| Endpoint | Method | 功能 | 回應格式 |
|----------|--------|------|----------|
| `/` | GET | 基本健康檢查 | `{"message": "Hello, World!"}` |

### 👥 客戶端管理 (Client Router)

#### PowerShell 腳本下載
| Endpoint | Method | 功能 | 參數 | 回應格式 |
|----------|--------|------|------|----------|
| `/client_install.ps1` | GET | 下載標準客戶端腳本 | `single_run`: boolean (可選) | PowerShell Script (text/plain) |
| `/dev_client_install.ps1` | GET | 下載開發版自動更新腳本 | 無 | PowerShell Script (text/plain) |

**功能特色：**
- 動態生成唯一 client_id
- 支援環境變數覆蓋伺服器 URL
- 自動格式化範本參數

#### 客戶端資訊
| Endpoint | Method | 功能 | 回應格式 |
|----------|--------|------|----------|
| `/clients` | GET | 列出所有已註冊的客戶端 | `{"clients": ["client_id1", "client_id2", ...]}` |

### 🔧 指令管理 (Command Router)

| Endpoint | Method | 功能 | 參數 | 回應格式 |
|----------|--------|------|------|----------|
| `/next_command` | GET | 客戶端取得下一個指令 | `client_id`: string (必要)<br>`session_id`: string (可選) | `{"command": "cmd"}` 或 `{"command": null}` |
| `/send_command` | POST | 發送指令給特定客戶端 | `client_id`: string (必要)<br>`command`: string (必要) | `{"status": "Command queued"}` 或錯誤訊息 |

**功能特色：**
- 指令佇列系統：每個客戶端一個指令佇列
- 自動客戶端註冊：無效 client_id 會自動重新註冊
- Session 追蹤：支援 session_id 用於日誌追蹤

### 📋 開發日誌 (Dev Log Router)

| Endpoint | Method | 功能 | 請求格式 | 回應格式 |
|----------|--------|------|----------|----------|
| `/dev_log` | POST | 上傳客戶端執行日誌 | JSON: `{"client_id": "id", "session_id": "sid", "content": "log_content"}` | `{"status": "Log uploaded successfully"}` |
| `/dev_log` | GET | 讀取並清空日誌佇列 (消費模式) | 無 | `{"logs": [...], "count": N}` |
| `/dev_log/peek` | GET | 查看日誌但不消費 | 無 | `{"logs": [...], "count": N}` |

**功能特色：**
- 簡單佇列系統：讀取後自動清空 (消費模式)
- Peek 功能：只查看不消費，適合監控
- 自動時間戳：上傳時自動加入 timestamp

---

## 客戶端功能模式

### 📱 標準模式 (Continuous Mode)
```powershell
iwr https://your-url/client_install.ps1 -UseBasicParsing | iex
```
- **持續執行**：持續輪詢伺服器等待指令
- **5秒輪詢間隔**：每 5 秒檢查一次新指令
- **錯誤重連**：連線失敗時自動退出

### ⚡ 單次執行模式 (Single Run Mode)
```powershell
iwr 'https://your-url/client_install.ps1?single_run=true' -UseBasicParsing | iex
```
- **單指令執行**：執行一個指令後立即退出
- **10秒超時**：未收到指令時 10 秒後自動退出
- **開發友好**：適合快速測試和除錯

### 🔄 開發版自動更新器 (Dev Auto-Updater)
```powershell
iwr https://your-url/dev_client_install.ps1 -UseBasicParsing | iex
```
- **自動重啟**：每次執行完成後 3 秒重啟
- **最新腳本**：每次都下載最新版本的客戶端腳本
- **Transcript 記錄**：完整記錄每個 session 的執行過程
- **自動上傳**：執行完成後自動上傳 transcript 到 `/dev_log`
- **錯誤處理**：執行失敗後 10 秒重試

---

## 開發工具功能

### 🔍 Transcript 記錄系統
- **Start-Transcript**：自動記錄完整的 PowerShell session
- **UTF-8 編碼**：正確處理中文等多位元組字元
- **自動清理**：上傳後自動清理暫存檔案
- **錯誤復原**：即使執行失敗也會上傳可用的 transcript

### 📊 日誌佇列管理
- **FIFO 佇列**：使用 `collections.deque` 實現先進先出
- **消費模式**：讀取後自動從佇列移除
- **監控模式**：peek 功能可查看但不移除
- **JSON 格式**：統一的日誌格式，包含 client_id, session_id, content, timestamp

### 🎯 開發循環支援
1. **即時回饋**：透過 transcript 即時查看執行結果
2. **自動化測試**：dev client 持續執行，無需手動重啟
3. **版本同步**：確保測試最新版本的腳本
4. **狀態透明**：透過 log 系統追蹤客戶端狀態

---

## 技術規格

### 🔧 後端技術
- **FastAPI**：現代 Python Web 框架
- **Uvicorn**：ASGI 伺服器
- **Pydantic**：資料驗證和序列化
- **Collections.deque**：高效能佇列實現

### 📝 前端腳本
- **PowerShell 5.1+**：相容 Windows PowerShell
- **Template 系統**：使用 Python `str.format()` 動態生成
- **UseBasicParsing**：避免 IE 相容性問題
- **錯誤處理**：完整的異常捕獲和重試機制

### 🌐 網路通訊
- **REST API**：標準 HTTP/HTTPS 通訊
- **JSON 格式**：結構化資料交換
- **Query Parameters**：簡單參數傳遞
- **ngrok 支援**：透過環境變數設定公開 URL

---

## 未來擴展性

### 🚀 可能的增強功能
- **身份驗證**：加入 API key 或 JWT 認證
- **指令歷史**：儲存和查詢執行歷史
- **多使用者**：支援多個管理者同時操作
- **Web UI**：提供網頁介面管理客戶端
- **檔案傳輸**：支援檔案上傳下載功能
- **定時任務**：支援 cron-like 定時指令執行

### 📊 監控擴展
- **效能指標**：客戶端效能監控
- **警報系統**：異常情況自動通知
- **圖表視覺化**：執行統計和趨勢分析
- **日誌分析**：進階日誌搜尋和分析功能