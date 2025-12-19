"""
Send Command

發送 PowerShell 命令到指定客戶端
"""

import sys
from pt1_cli.core import Command, PT1Config, PT1Client


class SendCommandCommand(Command):
    """發送命令到指定客戶端"""

    def execute(self) -> int:
        """執行發送命令"""
        # 檢查參數
        if len(sys.argv) < 4:
            print("Usage: pt1 send <client_id> <command>", file=sys.stderr)
            print("", file=sys.stderr)
            print("Example:", file=sys.stderr)
            print('  pt1 send my-dev-pc "Get-Process"', file=sys.stderr)
            print(
                '  pt1 send prod-server01 "Get-Service | Select-Object -First 5"',
                file=sys.stderr,
            )
            return 1

        client_id = sys.argv[2]
        command = sys.argv[3]

        config = PT1Config()

        # 檢查設定是否完整
        if not config.is_configured():
            config.show_config_help()
            return 1

        try:
            client = PT1Client(config)
            result = client.send_command(client_id, command)

            command_id = result.get("command_id")
            message = result.get("message", "")

            print(f"Command queued for '{client_id}'")
            print(f"Command ID: {command_id}")
            print("")
            print("Next steps:")
            print(f"  - Check result: pt1 get-result {command_id}")
            print(f"  - Wait for completion: pt1 wait {command_id}")

            return 0

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            print("", file=sys.stderr)
            print("Possible reasons:", file=sys.stderr)
            print("  - Client ID does not exist", file=sys.stderr)
            print("  - Server is not accessible", file=sys.stderr)
            print("  - Invalid API token", file=sys.stderr)
            print("", file=sys.stderr)
            print(
                "Tip: Run 'pt1 list-clients' to see available clients", file=sys.stderr
            )
            return 1
