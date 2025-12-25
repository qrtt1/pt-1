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
            print(
                "  The client will shutdown gracefully after completing current task",
                file=sys.stderr,
            )
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

            print("=" * 80)
            print(f"✓ Termination signal sent to '{client_id}'")
            print("=" * 80)
            print(f"Command ID: {command_id}")
            print(f"Status: {message}")
            print("")
            print("The client has been marked as TERMINATED on the server.")
            print("The graceful shutdown signal is now queued for the client.")
            print("")

            # 提供非同步檢查選項
            print("What happens next:")
            print("  1. Client will receive the termination signal")
            print("  2. Client will complete current task (if any)")
            print("  3. Client will shut down gracefully")
            print("")
            print("To check current status:")
            print(f"  pt1 list-clients          (check if [TERMINATED])")
            print(f"  pt1 get-result {command_id}")
            print("")

            # 可選的短暫等待（5 秒）以觀察立即反應
            print("Checking immediate status...")
            for attempt in range(3):
                time.sleep(2)

                # 取得 client registry
                registry_result = client.list_clients()
                clients = registry_result.get("clients", [])

                # 尋找目標 client
                target_client = None
                for c in clients:
                    if (
                        c.get("client_id") == client_id
                        or c.get("stable_id") == client_id
                    ):
                        target_client = c
                        break

                if not target_client:
                    print(f"✓ Client '{client_id}' has been removed from registry")
                    return 0

                # 檢查是否已標記為 terminated
                if target_client.get("terminated"):
                    terminated_status = "[TERMINATED]"
                else:
                    terminated_status = (
                        f"[{target_client.get('status', 'unknown').upper()}]"
                    )

                client_status = target_client.get("status", "unknown")
                print(
                    f"  Current status: {terminated_status} (last seen {attempt * 2 + 2}s ago)"
                )

                if client_status == "offline":
                    print(f"✓ Client '{client_id}' is now offline")
                    print("")
                    print("Termination completed successfully")
                    return 0

            # 非超時，而是「已發送，繼續進行中」
            print("")
            print("✓ Termination signal is queued and being processed")
            print("  The client may take a moment to shut down depending on")
            print("  whether it's busy with a long-running command.")
            print("")
            return 0

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
                print(
                    "Tip: Run 'pt1 list-clients' to see available clients",
                    file=sys.stderr,
                )
            elif "401" in error_msg or "403" in error_msg:
                print(
                    "Authentication failed. Please check your API token.",
                    file=sys.stderr,
                )
            else:
                print("Possible reasons:", file=sys.stderr)
                print("  - Server is not accessible", file=sys.stderr)
                print("  - Network connection issue", file=sys.stderr)

            return 1
