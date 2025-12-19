# PT-1 CLI - PowerShell Remote Execution Tool

一個讓你從任何地方遠端執行 Windows PowerShell 命令的 CLI 工具。專為 AI 助理和開發者設計，提供簡單、直觀的命令列介面來管理遠端 Windows 機器。

## 核心功能

- 🎯 **遠端 PowerShell 執行**: 從 macOS/Linux 對 Windows 機器執行 PowerShell 命令
- 📊 **指令追蹤**: 完整的執行歷史、狀態監控與結果查詢
- 📁 **檔案傳輸**: 自動下載命令產生的檔案（CSV、JSON、logs）
- 🔍 **除錯工具**: 查看完整的 PowerShell session transcripts
- 🤖 **AI 友善**: 專為 AI agent 設計的清晰 API 與文件
- ⚡ **即時等待**: 自動輪詢命令狀態，無需手動檢查

## 使用場景

### 🏢 IT 管理與診斷
```bash
# 檢查遠端伺服器狀態
pt1 send prod-server01 "Get-Service | Where-Object {$_.Status -eq 'Running'}"
pt1 wait <command_id>

# 匯出系統資訊
pt1 send workstation-03 "Get-ComputerInfo | ConvertTo-Json"
pt1 wait <command_id>
```

### 📊 資料收集與分析
```bash
# 收集 process 資料並下載
pt1 send target-pc "Get-Process | Export-Csv processes.csv -NoTypeInformation"
pt1 wait <command_id>
pt1 download <command_id> processes.csv
```

### 🔧 自動化測試
```bash
# 在測試環境執行腳本
pt1 send test-env "& C:\Scripts\run-tests.ps1"
pt1 wait <command_id>

# 檢查執行歷史
pt1 history test-env 10
```

### 🤖 AI Agent 整合

PT-1 CLI 專為 AI agent 設計，提供清晰的使用指南。以下是典型的對話流程：

**使用者：**
> 我想要檢查遠端 Windows 機器的系統更新狀態，但我不知道怎麼用這個工具。
>
> 執行 `pt1 prompt` 的輸出：
> ```
> [pt1 prompt 的完整輸出內容...]
> ```

**AI Agent：**
> 我已經理解 PT-1 CLI 的使用方式。讓我幫你檢查 Windows 機器的更新狀態：
>
> 1. 首先驗證設定是否正確：
> ```bash
> pt1 auth
> ```
>
> 2. 查看可用的機器：
> ```bash
> pt1 list-clients
> ```
>
> 3. 向目標機器發送命令：
> ```bash
> pt1 send example-pc "Get-HotFix | Select-Object -First 10"
> ```
>
> 4. 等待結果：
> ```bash
> pt1 wait <command_id>
> ```

**為什麼使用 `pt1 prompt`？**
- 包含完整的命令列表和使用範例
- 展示常見的使用模式（execute-and-wait, generate-csv-download）
- 提供 PowerShell 命令範例
- AI agent 可以快速理解工具用法，無需查閱多份文件

## 快速開始

### 1. 安裝 CLI

```bash
pip install -e .
```

### 2. 設定連線

建立設定檔 `~/.pt-1/.env`：

```bash
PT1_SERVER_URL=https://your-server.example.com
PT1_API_TOKEN=your-api-token-here
```

驗證連線：

```bash
pt1 auth
```

### 3. 部署 Windows Client

在目標 Windows 機器上執行（PowerShell）：

```powershell
# 使用 quickstart 命令取得安裝指令
pt1 quickstart my-dev-pc

# 複製顯示的命令到 Windows 機器執行
```

### 4. 開始使用

```bash
# 查看已連線的 clients
pt1 list-clients

# 發送第一個命令
pt1 send my-dev-pc "Get-ComputerInfo | Select-Object CsName, WindowsVersion"

# 等待並查看結果
pt1 wait <command_id>
```

## 完整命令列表

### 設定與驗證
- `pt1 auth` - 驗證 API token 與伺服器連線
- `pt1 quickstart [client_id]` - 產生 Windows client 安裝命令

### 執行管理
- `pt1 list-clients` - 列出所有已註冊的 Windows clients
- `pt1 send <client_id> <command>` - 發送 PowerShell 命令
- `pt1 wait <command_id>` - 自動等待命令完成並顯示結果
- `pt1 get-result <command_id>` - 手動查詢命令結果
- `pt1 history [client_id] [limit]` - 查看執行歷史

### 檔案處理
- `pt1 list-files <command_id>` - 列出命令產生的檔案
- `pt1 download <command_id> <filename> [path]` - 下載檔案

### 除錯工具
- `pt1 list-transcripts [client_id] [limit]` - 列出執行記錄
- `pt1 get-transcript <transcript_id>` - 查看完整執行記錄

### 說明文件
- `pt1 help [command]` - 顯示命令說明
- `pt1 prompt` - AI agent 快速參考指南

## 實用 PowerShell 命令範例

```bash
# 系統資訊
pt1 send pc "Get-ComputerInfo | ConvertTo-Json"

# Process 管理
pt1 send pc "Get-Process | Select-Object -First 10 Name, CPU, Memory"

# Service 狀態
pt1 send pc "Get-Service | Export-Csv services.csv"

# 磁碟空間
pt1 send pc "Get-PSDrive -PSProvider FileSystem"

# 事件日誌
pt1 send pc "Get-EventLog -LogName System -Newest 5"

# 網路設定
pt1 send pc "Get-NetIPAddress | ConvertTo-Json"
```

## 專案結構

```
pt-1/
├── pt1_cli/              # CLI 主程式
│   ├── cli.py            # 命令分派器
│   ├── core.py           # 核心功能與設定
│   └── commands/         # 各命令實作
├── main.py               # FastAPI server 入口
├── routers/              # API 路由
├── services/             # 業務邏輯
├── templates/            # PowerShell client 腳本
└── setup.py              # Python package 設定
```

## 文件

- **CLI 使用**: 執行 `pt1 help` 查看完整命令說明
- **AI Agent 指南**: 執行 `pt1 prompt` 取得 AI 專用快速參考
- **Server 部署**: 請參考 [SERVER_SETUP.md](SERVER_SETUP.md)
- **環境驗證**: 請參考 [VERIFICATION.md](VERIFICATION.md)
- **API 文件**: 啟動 server 後訪問 `/ai_guide` 端點

## 系統需求

- Python 3.7+
- Windows PowerShell 5.1+ (client 端)
- 網路連線 (client 與 server 需可互通)

## 授權

此專案供學習與開發使用。
