"""
History Command

查詢 client 命令執行歷史
"""

import sys
import requests
from datetime import datetime
from pt1_cli.core import Command, PT1Config


class HistoryCommand(Command):
    """查詢命令執行歷史"""

    def execute(self) -> int:
        """執行查詢命令歷史"""
        config = PT1Config()

        # 檢查設定是否完整
        if not config.is_configured():
            config.show_config_help()
            return 1

        # 檢查是否提供 client_id
        if len(sys.argv) < 3:
            print("Error: client_id is required", file=sys.stderr)
            print("", file=sys.stderr)
            print(f"Usage: {sys.argv[0]} history <client_id> [limit]", file=sys.stderr)
            print("", file=sys.stderr)
            print("Arguments:", file=sys.stderr)
            print("  client_id    The client ID to query history for", file=sys.stderr)
            print(
                "  limit        Maximum number of commands to show (default: 50)",
                file=sys.stderr,
            )
            print("", file=sys.stderr)
            print("Example:", file=sys.stderr)
            print(f"  {sys.argv[0]} history f008341b2b92", file=sys.stderr)
            print(f"  {sys.argv[0]} history f008341b2b92 10", file=sys.stderr)
            return 1

        client_id = sys.argv[2]
        limit = 50

        # 如果提供了 limit 參數
        if len(sys.argv) >= 4:
            try:
                limit = int(sys.argv[3])
                if limit <= 0:
                    print("Error: limit must be a positive integer", file=sys.stderr)
                    return 1
            except ValueError:
                print("Error: limit must be a valid integer", file=sys.stderr)
                return 1

        # 查詢命令歷史
        try:
            response = requests.get(
                f"{config.server_url}/command_history",
                params={"stable_id": client_id, "limit": limit},
                headers={"X-API-Token": config.api_token},
                timeout=10,
            )

            if response.status_code == 401:
                print("Error: Authentication failed", file=sys.stderr)
                print(
                    "Please check your PT1_SERVER_URL and PT1_API_TOKEN",
                    file=sys.stderr,
                )
                return 1
            elif response.status_code != 200:
                print(
                    f"Error: Server returned status {response.status_code}",
                    file=sys.stderr,
                )
                print(f"Response: {response.text}", file=sys.stderr)
                return 1

            data = response.json()
            commands = data.get("commands", [])
            total = data.get("total", 0)

            # 顯示歷史記錄
            print(f"Command History for '{client_id}'")
            print("=" * 80)
            print(f"Total commands: {total}")
            print("")

            if not commands:
                print("No commands found.")
                return 0

            # 顯示命令列表
            print(f"{'COMMAND ID':<38} {'STATUS':<12} {'COMMAND':<30}")
            print("-" * 80)

            for cmd in commands:
                command_id = cmd.get("command_id", "N/A")
                status = cmd.get("status", "N/A")
                command_text = cmd.get("command", "")

                # 截斷過長的命令
                if len(command_text) > 27:
                    command_text = command_text[:27] + "..."

                print(f"{command_id:<38} {status:<12} {command_text:<30}")

            print("")
            print("To view details of a command:")
            print("  pt1 get-result <command_id>")

            return 0

        except requests.exceptions.ConnectionError:
            print(
                f"Error: Cannot connect to server at {config.server_url}",
                file=sys.stderr,
            )
            print(
                "Please check if the server is running and the URL is correct",
                file=sys.stderr,
            )
            return 1
        except requests.exceptions.Timeout:
            print("Error: Request timed out", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error: {str(e)}", file=sys.stderr)
            return 1
