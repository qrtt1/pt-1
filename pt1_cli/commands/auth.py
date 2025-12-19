"""
Auth Command

驗證 API token 是否有效
"""

import sys
from pt1_cli.core import Command, PT1Config, PT1Client


class AuthCommand(Command):
    """驗證 API token"""

    def execute(self) -> int:
        """執行驗證"""
        config = PT1Config()

        # 檢查設定是否完整
        if not config.is_configured():
            config.show_config_help()
            return 1

        # 嘗試連線並驗證
        try:
            client = PT1Client(config)
            result = client.verify_auth()

            # 驗證成功
            print(f"✓ Authentication successful")
            print(f"  Server: {config.server_url}")
            print(f"  Token Name: {result.get('token_name', 'unknown')}")
            token_desc = result.get("token_description", "")
            if token_desc:
                print(f"  Description: {token_desc}")
            print(f"  Status: {result.get('message', 'OK')}")
            return 0

        except Exception as e:
            # 驗證失敗
            print("✗ Authentication failed", file=sys.stderr)
            print(f"  Server: {config.server_url}", file=sys.stderr)
            print(f"  Error: {e}", file=sys.stderr)
            print("", file=sys.stderr)
            print("Please check:", file=sys.stderr)
            print("  1. Server URL is correct and accessible", file=sys.stderr)
            print("  2. API token is valid", file=sys.stderr)
            print("  3. Server is running", file=sys.stderr)
            return 1
