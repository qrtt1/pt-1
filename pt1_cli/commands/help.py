"""
Help Command

顯示命令說明文件
"""

import sys
from pt1_cli.core import Command

# 所有命令的說明文件
COMMAND_HELP = {
    "auth": """
pt1 auth - Verify API token

Usage:
  pt1 auth

Description:
  驗證 PT1_API_TOKEN 是否有效，並顯示 server 資訊。

  設定檔位置：~/.pt-1/.env
  需要設定：
    PT1_SERVER_URL - Server 位址
    PT1_API_TOKEN  - API token

Example:
  pt1 auth
""",
    "quickstart": """
pt1 quickstart - Generate client installation command

Usage:
  pt1 quickstart [client_id]

Arguments:
  client_id    自訂的 client ID（選填，不提供會自動生成）

Description:
  生成 Windows PowerShell 安裝命令，可直接複製到 Windows 機器執行。

  自訂 client_id 的好處：
  - 易於識別（例如：prod-server01）
  - 方便管理多台機器
  - 執行命令時更直觀

Examples:
  pt1 quickstart
  pt1 quickstart my-dev-pc
  pt1 quickstart prod-server01
""",
    "list-clients": """
pt1 list-clients - List all registered clients

Usage:
  pt1 list-clients

Description:
  列出所有已註冊的 Windows 客戶端，顯示：
  - Client ID
  - Hostname
  - Username
  - Last seen timestamp

Example:
  pt1 list-clients
""",
    "send": """
pt1 send - Send PowerShell command to a client

Usage:
  pt1 send <client_id> <command>

Arguments:
  client_id    目標 client 的 ID
  command      要執行的 PowerShell 命令

Description:
  發送 PowerShell 命令到指定的 Windows 客戶端執行。
  命令會排入佇列，client 會在下次輪詢時執行。

  回傳 command_id，可用於查詢執行結果。

Examples:
  pt1 send my-dev-pc "Get-Process"
  pt1 send prod-server01 "Get-Service | Select-Object -First 5"
  pt1 send example-pc "Get-ComputerInfo"

See also:
  pt1 wait <command_id>      等待命令完成
  pt1 get-result <command_id>  查詢執行結果
""",
    "get-result": """
pt1 get-result - Get command execution result

Usage:
  pt1 get-result <command_id>

Arguments:
  command_id    命令執行的 ID

Description:
  查詢命令的執行結果。

  狀態：
  - pending: 等待執行
  - completed: 執行完成
  - failed: 執行失敗

Example:
  pt1 get-result 1c424006-b72d-49fd-bdb9-109fb8d63d1e

See also:
  pt1 wait <command_id>    自動輪詢等待完成
""",
    "wait": """
pt1 wait - Wait for command completion

Usage:
  pt1 wait <command_id>

Arguments:
  command_id    命令執行的 ID

Description:
  自動輪詢等待命令執行完成，並顯示結果。
  每 2 秒檢查一次執行狀態，直到完成或失敗。

  按 Ctrl+C 可中斷等待。

Example:
  # 發送命令後立即等待
  COMMAND_ID=$(pt1 send example-pc "Get-Process" | grep "Command ID:" | awk '{print $3}')
  pt1 wait $COMMAND_ID

See also:
  pt1 send <client_id> <command>    發送命令
  pt1 get-result <command_id>        手動查詢結果
""",
    "history": """
pt1 history - Show command execution history

Usage:
  pt1 history [client_id] [limit]

Arguments:
  client_id    過濾特定 client（選填）
  limit        限制顯示筆數（選填，預設 50）

Description:
  顯示命令執行歷史記錄，包含：
  - Command ID
  - Client ID
  - Command text
  - Status
  - Timestamp

Examples:
  pt1 history                查看所有歷史
  pt1 history my-dev-pc      查看特定 client 的歷史
  pt1 history my-dev-pc 20   查看最近 20 筆
""",
    "list-files": """
pt1 list-files - List files from command result

Usage:
  pt1 list-files <command_id>

Arguments:
  command_id    命令執行的 ID

Description:
  列出命令執行過程中產生的檔案。

  顯示資訊：
  - 檔案名稱
  - 檔案大小
  - Content type

Example:
  pt1 list-files 1c424006-b72d-49fd-bdb9-109fb8d63d1e

See also:
  pt1 download <command_id> <filename>    下載檔案
""",
    "download": """
pt1 download - Download file from command result

Usage:
  pt1 download <command_id> <filename> [output_path]

Arguments:
  command_id     命令執行的 ID
  filename       要下載的檔案名稱
  output_path    輸出路徑（選填，預設為當前目錄）

Description:
  下載命令執行過程中產生的檔案。

  如果輸出路徑是目錄，會保留原始檔名。
  如果檔案已存在，會報錯避免覆蓋。

Examples:
  pt1 download 1c424006-b72d-49fd-bdb9-109fb8d63d1e output.csv
  pt1 download 1c424006-b72d-49fd-bdb9-109fb8d63d1e output.csv ./downloads/
  pt1 download 1c424006-b72d-49fd-bdb9-109fb8d63d1e output.csv ./reports/report.csv

See also:
  pt1 list-files <command_id>    查看可下載的檔案
""",
    "list-transcripts": """
pt1 list-transcripts - List agent execution transcripts

Usage:
  pt1 list-transcripts [client_id] [limit]

Arguments:
  client_id    過濾特定 client（選填）
  limit        限制顯示筆數（選填，預設 50，最大 200）

Description:
  列出 PowerShell agent 的執行記錄 (transcripts)。
  Transcript 是完整的 PowerShell session 記錄檔。

  顯示資訊：
  - Transcript ID
  - Client ID
  - 檔案大小
  - 建立時間

Examples:
  pt1 list-transcripts                列出所有 transcripts
  pt1 list-transcripts my-example-pc     列出特定 client 的 transcripts
  pt1 list-transcripts my-example-pc 10  列出最近 10 筆

See also:
  pt1 get-transcript <transcript_id>    查看 transcript 內容
""",
    "get-transcript": """
pt1 get-transcript - Get transcript content

Usage:
  pt1 get-transcript <transcript_id>

Arguments:
  transcript_id    Transcript 的 ID

Description:
  查看 PowerShell agent 執行記錄的完整內容。

  Transcript 包含：
  - PowerShell session 資訊
  - 執行的命令
  - 命令輸出
  - 錯誤訊息
  - Timestamp

Example:
  pt1 get-transcript my-example-pc_20251219_094532_123

See also:
  pt1 list-transcripts [client_id]    列出可用的 transcripts
""",
}


class HelpCommand(Command):
    """顯示命令說明文件"""

    def execute(self) -> int:
        """執行 help 命令"""
        # 如果沒有指定命令，顯示命令列表
        if len(sys.argv) < 3:
            self._show_command_list()
            return 0

        command_name = sys.argv[2]

        # 顯示特定命令的說明
        if command_name in COMMAND_HELP:
            print(COMMAND_HELP[command_name].strip())
            return 0
        else:
            print(f"Error: Unknown command '{command_name}'", file=sys.stderr)
            print("", file=sys.stderr)
            print("Run 'pt1 help' to see all available commands.", file=sys.stderr)
            return 1

    def _show_command_list(self):
        """顯示所有命令列表"""
        print("PT-1 CLI - PowerShell Remote Execution Tool")
        print("=" * 80)
        print("")
        print("Usage: pt1 <command> [options]")
        print("")
        print("Available Commands:")
        print("")
        print("Setup & Authentication:")
        print("  auth              Verify API token")
        print("  quickstart        Generate client installation command")
        print("")
        print("Client Management:")
        print("  list-clients      List all registered clients")
        print("")
        print("Command Execution:")
        print("  send              Send PowerShell command to a client")
        print("  get-result        Get command execution result")
        print("  wait              Wait for command completion (auto-polling)")
        print("  history           Show command execution history")
        print("")
        print("File Management:")
        print("  list-files        List files from command result")
        print("  download          Download file from command result")
        print("")
        print("Debugging:")
        print("  list-transcripts  List agent execution transcripts")
        print("  get-transcript    Get transcript content")
        print("")
        print("Help:")
        print("  help [command]    Show detailed help for a command")
        print("")
        print("Examples:")
        print("  pt1 help send              Show detailed help for 'send' command")
        print("  pt1 quickstart my-dev-pc   Generate installation command")
        print("  pt1 list-clients           List all registered clients")
        print('  pt1 send pc001 "Get-Process"')
        print("")
        print("Configuration:")
        print("  Config file: ~/.pt-1/.env")
        print("  Required settings:")
        print("    PT1_SERVER_URL=https://your-server.com")
        print("    PT1_API_TOKEN=your-api-token-here")
        print("")
        print("For more information:")
        print("  Run 'pt1 help <command>' for detailed command documentation")
