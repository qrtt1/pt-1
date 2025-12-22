"""
List Clients Command

列出所有已註冊的客戶端及其狀態
"""

import sys
import json
from datetime import datetime
from pt1_cli.core import Command, PT1Config, PT1Client


class ListClientsCommand(Command):
    """列出所有已註冊的客戶端"""

    def execute(self) -> int:
        """執行列出客戶端命令"""
        config = PT1Config()

        # 檢查設定是否完整
        if not config.is_configured():
            config.show_config_help()
            return 1

        try:
            client = PT1Client(config)
            result = client.list_clients()

            clients = result.get("clients", [])

            if not clients:
                print("No clients registered.", file=sys.stderr)
                return 0

            # 顯示客戶端列表
            print(f"Total clients: {len(clients)}")
            print("")
            print(
                f"{'CLIENT ID':<20} {'STATUS':<15} {'HOSTNAME':<20} {'USERNAME':<15} {'LAST SEEN':<20}"
            )
            print("-" * 100)

            for c in clients:
                client_id = c.get("stable_id", "unknown")
                status = c.get("status", "unknown")
                terminated = c.get("terminated", False)
                hostname = c.get("hostname", "unknown")
                username = c.get("username", "unknown")
                last_seen = c.get("last_seen", "")

                # 格式化時間
                if last_seen:
                    try:
                        dt = datetime.fromisoformat(last_seen.replace("Z", "+00:00"))
                        last_seen_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        last_seen_str = last_seen
                else:
                    last_seen_str = "never"

                # 狀態標示
                if terminated:
                    status_display = "[TERMINATED]"
                else:
                    status_display = f"[{status.upper()}]"

                print(
                    f"{client_id:<20} {status_display:<15} {hostname:<20} {username:<15} {last_seen_str:<20}"
                )

            return 0

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
