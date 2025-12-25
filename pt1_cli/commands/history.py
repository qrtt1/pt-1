"""
History Command

查詢 client 命令執行歷史
"""

import sys
import requests
from datetime import datetime
from pt1_cli.core import Command, PT1Config, PT1Client


class HistoryCommand(Command):
    """查詢命令執行歷史"""

    def execute(self) -> int:
        """執行查詢命令歷史"""
        config = PT1Config()

        # 檢查設定是否完整
        if not config.is_configured():
            config.show_config_help()
            return 1

        # 建立 API client
        client = PT1Client(config)

        args = sys.argv[2:]
        verbose = False

        if "-v" in args:
            verbose = True
            args = [arg for arg in args if arg != "-v"]

        # 檢查是否提供 client_id
        if len(args) < 1:
            print("Error: client_id is required", file=sys.stderr)
            print("", file=sys.stderr)
            print(
                f"Usage: {sys.argv[0]} history [-v] <client_id> [limit]",
                file=sys.stderr,
            )
            print("", file=sys.stderr)
            print("Arguments:", file=sys.stderr)
            print("  client_id    The client ID to query history for", file=sys.stderr)
            print(
                "  limit        Maximum number of commands to show (default: 50)",
                file=sys.stderr,
            )
            print("  -v           Show verbose client API calls", file=sys.stderr)
            print("", file=sys.stderr)
            print("Example:", file=sys.stderr)
            print(f"  {sys.argv[0]} history f008341b2b92", file=sys.stderr)
            print(f"  {sys.argv[0]} history -v f008341b2b92 10", file=sys.stderr)
            return 1

        client_id = args[0]
        limit = 50

        # 如果提供了 limit 參數
        if len(args) >= 2:
            try:
                limit = int(args[1])
                if limit <= 0:
                    print("Error: limit must be a positive integer", file=sys.stderr)
                    return 1
            except ValueError:
                print("Error: limit must be a valid integer", file=sys.stderr)
                return 1

        # 查詢命令歷史
        try:
            data = client.get_command_history(stable_id=client_id, limit=limit)
            commands = data.get("commands", [])
            total = data.get("total", 0)

            if not verbose:
                commands = [
                    cmd
                    for cmd in commands
                    if not (
                        cmd.get("status", "").startswith("client_call_")
                        and (
                            cmd.get("command", "").startswith("client_api GET /next_command")
                            or cmd.get("command", "").startswith("client_api POST /register_client")
                        )
                    )
                ]
                total = len(commands)

            # 顯示歷史記錄
            print(f"Command History for '{client_id}'")
            print("=" * 80)
            print(f"Total commands: {total}")
            print("")

            if not commands:
                print("No commands found.")
                return 0

            # 顯示命令列表
            print(f"{'TIME':<19} {'COMMAND ID':<36} {'STATUS':<16} {'TYPE':<10} {'DETAIL':<34}")
            print("-" * 80)

            for cmd in commands:
                command_id = cmd.get("command_id", "N/A")
                status = cmd.get("status", "N/A")
                command_text = cmd.get("command", "")
                created_at = cmd.get("created_at")
                time_str = "N/A"
                if isinstance(created_at, (int, float)):
                    time_str = datetime.fromtimestamp(created_at).strftime("%Y-%m-%d %H:%M:%S")

                entry_type = "command"
                detail = command_text
                args = cmd.get("result", "")
                if status.startswith("client_call_"):
                    entry_type = "client_api"
                    detail = command_text
                    if detail.startswith("client_api "):
                        detail = detail[len("client_api "):]
                    if args:
                        detail = f"{detail}?{args}"

                status_display = status
                if status.startswith("client_call_"):
                    status_display = status.split("_")[-1]

                print(f"{time_str:<19} {command_id:<36} {status_display:<16} {entry_type:<10} {detail:<34}")

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
