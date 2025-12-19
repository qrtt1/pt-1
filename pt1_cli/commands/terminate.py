"""
Terminate Client

發送優雅終止信號給指定客戶端
"""

import sys
import time
from pt1_cli.core import Command, PT1Config, PT1Client


class TerminateCommand(Command):
    """終止指定客戶端"""

    def execute(self) -> int:
        """執行終止命令"""
        # 檢查參數
        if len(sys.argv) < 3:
            print("Usage: pt1 terminate <client_id>", file=sys.stderr)
            print("", file=sys.stderr)
            print("Description:", file=sys.stderr)
            print("  Send graceful termination signal to a client", file=sys.stderr)
            print("  The client will shutdown gracefully after completing current task", file=sys.stderr)
            print("", file=sys.stderr)
            print("Example:", file=sys.stderr)
            print("  pt1 terminate my-dev-pc", file=sys.stderr)
            print("  pt1 terminate builder", file=sys.stderr)
            return 1

        client_id = sys.argv[2]

        config = PT1Config()

        # 檢查設定是否完整
        if not config.is_configured():
            config.show_config_help()
            return 1

        try:
            client = PT1Client(config)

            # 發送終止信號
            result = client.terminate_client(client_id)

            command_id = result.get("command_id")
            message = result.get("message", "")

            print(f"✓ Termination signal sent to '{client_id}'")
            print(f"Command ID: {command_id}")
            print(f"Status: {message}")
            print("")
            print("Waiting for client to shut down...")

            # 輪詢確認 client 離線（最多等待 30 秒）
            max_attempts = 15
            for attempt in range(max_attempts):
                time.sleep(2)

                # 取得 client registry
                registry_result = client.list_clients()
                clients = registry_result.get("clients", [])

                # 尋找目標 client
                target_client = None
                for c in clients:
                    if c.get("client_id") == client_id or c.get("stable_id") == client_id:
                        target_client = c
                        break

                if not target_client:
                    print(f"✓ Client '{client_id}' has been removed from registry")
                    return 0

                if target_client.get("status") == "offline":
                    print(f"✓ Client '{client_id}' is now offline")
                    print("")
                    print("Termination completed successfully")
                    return 0

            # 超時
            print(f"⚠ Timeout: Client '{client_id}' may still be running")
            print("The termination signal was sent, but the client has not yet confirmed shutdown")
            print("")
            print("Possible reasons:")
            print("  - Client is still processing a long-running command")
            print("  - Client lost network connection")
            print("  - Client agent is not responding")
            print("")
            print("You can check client status with: pt1 list-clients")
            return 1

        except Exception as e:
            error_msg = str(e)

            print(f"✗ Error: {error_msg}", file=sys.stderr)
            print("", file=sys.stderr)

            # 提供更具體的錯誤訊息
            if "404" in error_msg or "not found" in error_msg.lower():
                print("Possible reasons:", file=sys.stderr)
                print(f"  - Client '{client_id}' does not exist", file=sys.stderr)
                print("  - Client has already been terminated", file=sys.stderr)
                print("", file=sys.stderr)
                print("Tip: Run 'pt1 list-clients' to see available clients", file=sys.stderr)
            elif "401" in error_msg or "403" in error_msg:
                print("Authentication failed. Please check your API token.", file=sys.stderr)
            else:
                print("Possible reasons:", file=sys.stderr)
                print("  - Server is not accessible", file=sys.stderr)
                print("  - Network connection issue", file=sys.stderr)

            return 1
