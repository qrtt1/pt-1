# PT-1 部署與驗證指南

本文件說明從本地開發到遠端部署的完整流程。

## 環境資訊

- **Server Domain**: https://your-server.example.com
- **Server Port**: 5566
- **部署主機**: pt1
- **部署路徑**: `~/workspace/pt-1` (相對於 yourname 家目錄)
- **Service 名稱**: `powershell-executor.service`
- **Python 環境**: `~/workspace/venv`

## 前置條件

### 1. SSH 設定

使用 SSH Agent Forward 方式存取 pt1 主機，不使用 deploy key。

**本地 SSH config 設定** (`~/.ssh/config`):
```
Host your-server
    HostName <pt1-hostname>
    User yourname
    ForwardAgent yes
```

**驗證 SSH 連線**:
```bash
# 測試無密碼登入
ssh your-server "whoami"

# 測試 sudo 權限
ssh your-server "sudo systemctl status powershell-executor.service"
```

### 2. 本地 CLI 工具安裝

```bash
# 在專案目錄安裝
cd /Users/yourname/temp/pt-1
pip install -e .

# 驗證安裝
which pt1
pt1 --help
```

### 3. CLI 環境設定

建立 `~/.pt-1/.env` 檔案：

```bash
mkdir -p ~/.pt-1
cat > ~/.pt-1/.env << 'EOF'
PT1_SERVER_URL=https://your-server.example.com
PT1_API_TOKEN=your-api-token-here
EOF
```

驗證設定：
```bash
pt1 auth
```

應該看到 "✓ Authentication successful"。

## 開發部署流程

### 步驟 1: 本地開發與提交

```bash
# 確認工作目錄乾淨
git status

# 查看未 push 的 commits
git log origin/feature/cli..HEAD --oneline

# 如果有未 push 的 commits，先 push
git push origin feature/cli
```

### 步驟 2: 同步到遠端主機

```bash
# SSH 到 pt1 並 pull 最新代碼
ssh your-server "cd workspace/pt-1 && git pull"
```

**注意**: 路徑是 `workspace/pt-1`，不是 `~/workspace/pt-1`。SSH 命令會自動在家目錄執行。

### 步驟 3: 重啟服務

```bash
# 重啟 PowerShell executor service
ssh your-server "sudo systemctl restart powershell-executor.service"

# 確認服務狀態
ssh your-server "sudo systemctl status powershell-executor.service"
```

**成功訊息範例**:
```
● powershell-executor.service - PowerShell Remote Execution Service
     Loaded: loaded (/etc/systemd/system/powershell-executor.service; enabled)
     Active: active (running) since ...
```

### 步驟 4: 生成驗證指令

```bash
# 生成自動產生 client ID 的版本
pt1 quickstart

# 或生成自訂 client ID 的版本（推薦）
pt1 quickstart test-machine
```

## 完整的部署腳本

將以上步驟整合成單一腳本：

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
git push origin feature/cli

# 3. SSH 到 pt1 同步代碼
echo "3. 同步代碼到 pt1..."
ssh your-server "cd workspace/pt-1 && git pull"

# 4. 重啟服務
echo "4. 重啟 service..."
ssh your-server "sudo systemctl restart powershell-executor.service"

# 5. 確認服務狀態
echo "5. 確認服務狀態..."
if ssh your-server "sudo systemctl is-active --quiet powershell-executor.service"; then
    echo "✓ Service 運行正常"
else
    echo "✗ Service 啟動失敗"
    ssh your-server "sudo systemctl status powershell-executor.service"
    exit 1
fi

# 6. 顯示 quickstart 指令
echo ""
echo "=== 部署完成 ==="
echo ""
echo "驗證指令："
pt1 quickstart test-machine

echo ""
echo "✓ 部署流程完成"
```

使用方式：
```bash
chmod +x deploy.sh
./deploy.sh
```

## 驗證流程

### 給驗證人員的操作步驟

#### 1. 在 Windows 機器上執行 client

**基本版（自動生成 ID）**:
```powershell
iwr "https://your-server.example.com/win_agent.ps1" -Headers @{"X-API-Token"="your-api-token-here"} | iex
```

**自訂 ID 版（推薦）**:
```powershell
iwr "https://your-server.example.com/win_agent.ps1?client_id=test-pc" -Headers @{"X-API-Token"="your-api-token-here"} | iex
```

#### 2. 在開發機上驗證

```bash
# 查看註冊的 clients
pt1 list-clients

# 應該看到 test-pc（或自動生成的 ID）

# 發送測試命令
pt1 send test-pc "Get-ComputerInfo | Select-Object CsName, OsArchitecture, WindowsVersion"

# 記下 command_id，查詢結果
pt1 get-result <command_id>

# 查看命令歷史
pt1 history test-pc
```

#### 3. 測試 Phase 2 核心功能

```bash
# 測試 list-clients
pt1 list-clients

# 測試 send
COMMAND_ID=$(pt1 send test-pc "Get-Process | Select-Object -First 5" | grep "Command ID:" | awk '{print $3}')

# 測試 get-result
pt1 get-result $COMMAND_ID

# 測試 history
pt1 history test-pc

# 測試 quickstart
pt1 quickstart my-test-machine
```

## Service 管理

### 查看 Service 日誌

```bash
# 即時查看日誌
ssh your-server "sudo journalctl -u powershell-executor.service -f"

# 查看最近 50 行
ssh your-server "sudo journalctl -u powershell-executor.service -n 50"

# 查看特定時間範圍
ssh your-server "sudo journalctl -u powershell-executor.service --since '10 minutes ago'"
```

### Service 狀態管理

```bash
# 查看狀態
ssh your-server "sudo systemctl status powershell-executor.service"

# 停止服務
ssh your-server "sudo systemctl stop powershell-executor.service"

# 啟動服務
ssh your-server "sudo systemctl start powershell-executor.service"

# 重啟服務
ssh your-server "sudo systemctl restart powershell-executor.service"

# 查看是否開機自動啟動
ssh your-server "sudo systemctl is-enabled powershell-executor.service"
```

## 常見問題排查

### 問題 1: Service 啟動失敗

```bash
# 查看詳細錯誤訊息
ssh your-server "sudo journalctl -u powershell-executor.service -n 100"

# 檢查 Python 環境
ssh your-server "cd workspace/pt-1 && source ../venv/bin/activate && python -c 'import fastapi'"

# 檢查 port 是否被佔用
ssh your-server "sudo netstat -tlnp | grep 5566"
```

### 問題 2: Git pull 失敗

```bash
# 查看遠端狀態
ssh your-server "cd workspace/pt-1 && git status"

# 如果有本地修改，先 stash
ssh your-server "cd workspace/pt-1 && git stash"
ssh your-server "cd workspace/pt-1 && git pull"

# 如果需要，重新套用 stash
ssh your-server "cd workspace/pt-1 && git stash pop"
```

### 問題 3: SSH 連線問題

```bash
# 測試基本連線
ssh -v pt1

# 確認 SSH agent
ssh-add -l

# 測試 agent forwarding
ssh -A pt1 "ssh-add -l"
```

### 問題 4: API Token 驗證失敗

```bash
# 檢查本地設定
cat ~/.pt-1/.env

# 測試 API 連線
curl -H "X-API-Token: $(grep PT1_API_TOKEN ~/.pt-1/.env | cut -d= -f2)" \
     https://your-server.example.com/auth/verify

# 使用 CLI 驗證
pt1 auth
```

### 問題 5: Client 無法註冊

```bash
# 查看 server 日誌
ssh your-server "sudo journalctl -u powershell-executor.service -f"

# 檢查 API token 是否正確（在 Windows PowerShell 上）
$headers = @{"X-API-Token"="your-api-token-here"}
Invoke-RestMethod -Uri "https://your-server.example.com/auth/verify" -Headers $headers

# 測試基本連線
Test-NetConnection -ComputerName your-server.example.com -Port 443
```

## 版本管理

### 切換到特定版本

如果需要部署特定版本（例如回到穩定版本）：

```bash
# 在 pt1 上切換到特定 commit
ssh your-server "cd workspace/pt-1 && git fetch && git checkout <commit-hash>"
ssh your-server "sudo systemctl restart powershell-executor.service"

# 或切換到特定 branch
ssh your-server "cd workspace/pt-1 && git fetch && git checkout main"
ssh your-server "sudo systemctl restart powershell-executor.service"

# 回到最新的 feature/cli
ssh your-server "cd workspace/pt-1 && git checkout feature/cli && git pull"
ssh your-server "sudo systemctl restart powershell-executor.service"
```

### 查看當前部署版本

```bash
# 查看當前 commit
ssh your-server "cd workspace/pt-1 && git log -1 --oneline"

# 查看當前 branch
ssh your-server "cd workspace/pt-1 && git branch --show-current"

# 比較與本地的差異
LOCAL_COMMIT=$(git rev-parse HEAD)
REMOTE_COMMIT=$(ssh your-server "cd workspace/pt-1 && git rev-parse HEAD")
echo "本地: $LOCAL_COMMIT"
echo "遠端: $REMOTE_COMMIT"
```

## 安全注意事項

1. **API Token 保護**
   - 不要將 API token 提交到 git repository
   - 定期更換 API token
   - 不同環境使用不同的 token

2. **SSH 安全**
   - 使用 SSH agent forward，不要複製私鑰到 server
   - 定期檢查 authorized_keys
   - 使用 SSH config 管理連線設定

3. **Service 權限**
   - Service 以特定用戶執行，不使用 root
   - 定期檢查 service 執行權限
   - 限制可執行的 PowerShell 命令範圍（未來功能）

## 參考資料

- [CLI 功能規劃](cli-plan.md)
- [功能特色說明](features.md)
- [改善計畫](TODO.md)
- [API 使用指南](templates/ai_guide.md)
