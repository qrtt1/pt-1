"""
List Clients Command

列出所有已註冊的客戶端及其狀態
"""

import sys
import json
from datetime import datetime, timezone
import time
from pt1_cli.core import Command, PT1Config, PT1Client


class ListClientsCommand(Command):
    """列出所有已註冊的客戶端"""

    @staticmethod
    def format_last_seen(timestamp):
        """將時間戳格式化為 '時:分:秒 (X min/sec ago)' 的混合格式"""
        if not timestamp:
            return "never"

        try:
            # 轉換時間戳為 datetime
            dt = datetime.fromtimestamp(timestamp)
            now = datetime.now()

            # 計算相對時間
            elapsed = (now - dt).total_seconds()

            if elapsed < 60:
                relative = f"{int(elapsed)}s ago"
            elif elapsed < 3600:
                relative = f"{int(elapsed / 60)}m ago"
            else:
                relative = f"{int(elapsed / 3600)}h ago"

            # 格式化絕對時間
            absolute = dt.strftime("%H:%M:%S")

            return f"{absolute} ({relative})"
        except (ValueError, OSError):
            return str(timestamp)

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
                f"{'CLIENT ID':<20} {'STATUS':<15} {'HOSTNAME':<20} {'USERNAME':<15} {'LAST SEEN':<30}"
            )
            print("-" * 110)

            for c in clients:
                client_id = c.get("stable_id", "unknown")
                status = c.get("status", "unknown")
                terminated = c.get("terminated", False)
                hostname = c.get("hostname", "unknown")
                username = c.get("username", "unknown")
                last_seen = c.get("last_seen", "")

                # 格式化時間戳（混合格式）
                last_seen_str = self.format_last_seen(last_seen)

                # 狀態標示
                if terminated:
                    status_display = "[TERMINATED]"
                else:
                    status_display = f"[{status.upper()}]"

                print(
                    f"{client_id:<20} {status_display:<15} {hostname:<20} {username:<15} {last_seen_str}"
                )

            return 0

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
