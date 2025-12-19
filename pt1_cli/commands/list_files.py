"""
List Files Command

列出命令產生的檔案
"""

import sys
import requests
from pt1_cli.core import Command, PT1Config


class ListFilesCommand(Command):
    """列出命令產生的檔案"""

    def execute(self) -> int:
        """執行列出檔案"""
        config = PT1Config()

        # 檢查設定是否完整
        if not config.is_configured():
            config.show_config_help()
            return 1

        # 檢查是否提供 command_id
        if len(sys.argv) < 3:
            print("Error: command_id is required", file=sys.stderr)
            print("", file=sys.stderr)
            print(f"Usage: {sys.argv[0]} list-files <command_id>", file=sys.stderr)
            print("", file=sys.stderr)
            print("Example:", file=sys.stderr)
            print(
                f"  {sys.argv[0]} list-files 1c424006-b72d-49fd-bdb9-109fb8d63d1e",
                file=sys.stderr,
            )
            return 1

        command_id = sys.argv[2]

        # 查詢檔案列表
        try:
            response = requests.get(
                f"{config.server_url}/list_files/{command_id}",
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

            data = response.json()
            files = data.get("files", [])
            total_files = data.get("total_files", 0)

            # 顯示檔案列表
            print(f"Files for Command {command_id}")
            print("=" * 80)
            print(f"Total files: {total_files}")
            print("")

            if not files:
                print("No files found.")
                return 0

            # 顯示檔案資訊
            print(f"{'FILENAME':<40} {'SIZE':<15} {'TYPE':<25}")
            print("-" * 80)

            for file_info in files:
                filename = file_info.get("filename", "N/A")
                size = file_info.get("size", 0)
                content_type = file_info.get("content_type", "unknown")

                # 格式化檔案大小
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.2f} KB"
                else:
                    size_str = f"{size / (1024 * 1024):.2f} MB"

                # 截斷過長的檔名
                display_name = (
                    filename if len(filename) <= 37 else filename[:34] + "..."
                )

                print(f"{display_name:<40} {size_str:<15} {content_type:<25}")

            print("")
            print("To download a file:")
            print(f"  pt1 download {command_id} <filename> [output_path]")

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
