"""
Quickstart Command

產生 PowerShell client 的 oneliner 快速啟動命令
"""

import sys
from pt1_cli.core import Command, PT1Config, PT1Client


class QuickstartCommand(Command):
    """產生 PowerShell client 快速啟動命令"""

    def execute(self) -> int:
        """執行產生安裝命令"""
        config = PT1Config()

        # 檢查設定是否完整
        if not config.is_configured():
            config.show_config_help()
            return 1

        # 取得全新的 session token（確保有完整的有效期）
        client = PT1Client(config)
        try:
            session_token = client.get_fresh_session_token()
        except Exception as e:
            print(f"Error: Failed to obtain session token: {e}", file=sys.stderr)
            return 1

        # 檢查是否提供 client_id 參數
        client_id = None
        if len(sys.argv) >= 3:
            client_id = sys.argv[2]

        # 建立基本 URL
        base_url = config.server_url.rstrip("/")
        script_url = f"{base_url}/win_agent.ps1"

        # 如果有 client_id，加入 query parameter
        if client_id:
            script_url += f"?client_id={client_id}"

        # 產生 PowerShell oneliner
        print("")
        print("PowerShell Client Quickstart")
        print("=" * 80)
        print("")

        if client_id:
            print(f"Client ID: {client_id}")
        else:
            print("Client ID: (auto-generated)")
        print("")

        print("Copy and run this command on your Windows machine:")
        print("-" * 80)
        print(
            f'iwr "{script_url}" -UseBasicParsing -Headers @{{"X-API-Token"="{session_token}"}} | iex'
        )
        print("-" * 80)
        print("")

        print("Tips:")
        print(f"  - To specify a custom client ID: pt1 quickstart <client_id>")
        print(f"  - Example: pt1 quickstart my-dev-pc")
        print(f"  - Example: pt1 quickstart prod-server01")
        print("")
        print("After running the command, the client will:")
        print("  1. Register with the server")
        print("  2. Wait for commands")
        print("  3. Auto-restart on failure")
        print("  4. Upload execution transcripts")

        return 0
