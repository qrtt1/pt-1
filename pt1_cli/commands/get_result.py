"""
Get Result Command

查詢命令執行結果
"""

import sys
import requests
from pt1_cli.core import Command, PT1Config


class GetResultCommand(Command):
    """查詢命令執行結果"""

    def execute(self) -> int:
        """執行查詢命令結果"""
        config = PT1Config()

        # 檢查設定是否完整
        if not config.is_configured():
            config.show_config_help()
            return 1

        # 檢查是否提供 command_id
        if len(sys.argv) < 3:
            print("Error: command_id is required", file=sys.stderr)
            print("", file=sys.stderr)
            print(f"Usage: {sys.argv[0]} get-result <command_id>", file=sys.stderr)
            print("", file=sys.stderr)
            print("Example:", file=sys.stderr)
            print(
                f"  {sys.argv[0]} get-result 1c424006-b72d-49fd-bdb9-109fb8d63d1e",
                file=sys.stderr,
            )
            return 1

        command_id = sys.argv[2]

        # 查詢命令結果
        try:
            response = requests.get(
                f"{config.server_url}/get_result/{command_id}",
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
            elif response.status_code == 404:
                print(f"Error: Command ID '{command_id}' not found", file=sys.stderr)
                return 1
            elif response.status_code != 200:
                print(
                    f"Error: Server returned status {response.status_code}",
                    file=sys.stderr,
                )
                print(f"Response: {response.text}", file=sys.stderr)
                return 1

            result = response.json()

            # 檢查是否有錯誤
            if "error" in result:
                print(f"Error: {result['error']}", file=sys.stderr)
                return 1

            # 顯示命令資訊
            print("Command Result")
            print("=" * 80)
            print(f"Command ID:    {result['command_id']}")
            print(f"Client ID:     {result['stable_id']}")
            print(f"Status:        {result['status']}")
            print(f"Command:       {result['command']}")
            print("")

            # 顯示執行時間資訊
            if result.get("finished_at"):
                duration = result["finished_at"] - result["created_at"]
                print(f"Duration:      {duration:.2f} seconds")
                print("")

            # 顯示結果類型
            result_type = result.get("result_type", "text")
            print(f"Result Type:   {result_type}")
            print("")

            # 顯示文字結果
            if result.get("result"):
                print("Output:")
                print("-" * 80)
                print(result["result"])
                print("-" * 80)
                print("")

            # 顯示檔案資訊
            if result.get("files"):
                files = result["files"]
                print(f"Files: ({len(files)} file(s))")
                print("-" * 80)
                for file_info in files:
                    filename = file_info["filename"]
                    size = file_info["size"]
                    content_type = file_info.get("content_type", "unknown")
                    print(f"  - {filename}")
                    print(f"    Size: {size} bytes")
                    print(f"    Type: {content_type}")
                    print(
                        f"    Download: {config.server_url}/download_file/{command_id}/{filename}"
                    )
                    print("")

            # 如果命令還在執行中，提示使用 wait 命令
            if result["status"] in ["pending", "executing"]:
                print("Note: Command is still running")
                print(f"  Use 'pt1 wait {command_id}' to wait for completion")

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
