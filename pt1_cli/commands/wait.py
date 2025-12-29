"""
Wait Command

等待命令執行完成並顯示結果
"""

import sys
import time
import requests
from pt1_cli.core import Command, PT1Config, PT1Client


class WaitCommand(Command):
    """等待命令執行完成"""

    def execute(self) -> int:
        """執行等待命令完成"""
        config = PT1Config()

        # 檢查設定是否完整
        if not config.is_configured():
            config.show_config_help()
            return 1

        # 建立 API client
        client = PT1Client(config)

        # 檢查是否提供 command_id
        if len(sys.argv) < 3:
            print("Error: command_id is required", file=sys.stderr)
            print("", file=sys.stderr)
            print(f"Usage: {sys.argv[0]} wait <command_id> [options]", file=sys.stderr)
            print("", file=sys.stderr)
            print("Options:", file=sys.stderr)
            print(
                "  --interval <seconds>  Polling interval (default: 0.5)",
                file=sys.stderr,
            )
            print(
                "  --max <seconds>       Maximum wait time (default: 30)",
                file=sys.stderr,
            )
            print("", file=sys.stderr)
            print("Example:", file=sys.stderr)
            print(
                f"  {sys.argv[0]} wait 1c424006-b72d-49fd-bdb9-109fb8d63d1e",
                file=sys.stderr,
            )
            print(
                f"  {sys.argv[0]} wait 1c424006-b72d-49fd-bdb9-109fb8d63d1e --interval 5 --max 600",
                file=sys.stderr,
            )
            return 1

        command_id = sys.argv[2]

        # 解析選項
        interval = 0.5  # 預設 0.5 秒
        timeout = 30  # 預設 30 秒

        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--interval":
                if i + 1 >= len(sys.argv):
                    print("Error: --interval requires a value", file=sys.stderr)
                    return 1
                try:
                    interval = float(sys.argv[i + 1])
                    if interval <= 0:
                        print("Error: interval must be positive", file=sys.stderr)
                        return 1
                except ValueError:
                    print("Error: interval must be a number", file=sys.stderr)
                    return 1
                i += 2
            elif sys.argv[i] == "--max":
                if i + 1 >= len(sys.argv):
                    print("Error: --max requires a value", file=sys.stderr)
                    return 1
                try:
                    timeout = float(sys.argv[i + 1])
                    if timeout <= 0:
                        print("Error: max must be positive", file=sys.stderr)
                        return 1
                except ValueError:
                    print("Error: max must be a number", file=sys.stderr)
                    return 1
                i += 2
            else:
                print(f"Error: Unknown option '{sys.argv[i]}'", file=sys.stderr)
                return 1

        # 開始輪詢
        start_time = time.time()
        dots = 0
        last_status_print = 0.0

        print(f"Waiting for command {command_id} to complete...")
        print(f"(polling every {interval}s, timeout: {timeout}s)")
        print("")

        try:
            while True:
                elapsed = time.time() - start_time

                # 檢查是否超時
                if elapsed > timeout:
                    print("\n")
                    print(f"Timeout after {timeout} seconds")
                    print(f"Command may still be running. Either:")
                    print(f"  - Check result: pt1 get-result {command_id}")
                    print(f"  - Wait again:   pt1 wait {command_id} --max 60")
                    return 0

                # 查詢命令狀態（使用 PT1Client 的 API）
                try:
                    result = client.get_result(command_id)
                except requests.HTTPError as e:
                    response_status = e.response.status_code if e.response else 500
                    response_text = e.response.text if e.response else str(e)

                    if response_status == 401:
                        print("\n", file=sys.stderr)
                        print("Error: Authentication failed", file=sys.stderr)
                        print(
                            "Please check your PT1_SERVER_URL and PT1_API_TOKEN",
                            file=sys.stderr,
                        )
                        return 1
                    elif response_status == 404:
                        print("\n", file=sys.stderr)
                        print(
                            f"Error: Command ID '{command_id}' not found",
                            file=sys.stderr,
                        )
                        return 1
                    else:
                        print("\n", file=sys.stderr)
                        print(
                            f"Error: Server returned status {response_status}",
                            file=sys.stderr,
                        )
                        print(f"Response: {response_text}", file=sys.stderr)
                        return 1

                # 檢查是否有錯誤
                if "error" in result:
                    print("\n", file=sys.stderr)
                    print(f"Error: {result['error']}", file=sys.stderr)
                    return 1

                status = result.get("status", "unknown")

                # 如果命令已完成，顯示結果
                if status in ["completed", "failed", "error"]:
                    print("\n")
                    print("=" * 80)
                    print(f"Command {status}!")
                    print("=" * 80)
                    print("")

                    # 顯示命令資訊
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

                    return 0 if status == "completed" else 1

                # 命令還在執行，狀態顯示最多每秒一次
                if elapsed - last_status_print >= 1:
                    last_status_print = elapsed
                    dots = (dots + 1) % 4
                    progress = "." * dots + " " * (3 - dots)
                    elapsed_str = f"{elapsed:.0f}s"
                    print(
                        f"\rStatus: {status:12} [{progress}] (elapsed: {elapsed_str})",
                        end="",
                        flush=True,
                    )

                # 等待下一次輪詢
                time.sleep(interval)

        except requests.exceptions.ConnectionError:
            print("\n", file=sys.stderr)
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
            print("\n", file=sys.stderr)
            print("Error: Request timed out", file=sys.stderr)
            return 1
        except KeyboardInterrupt:
            print("\n", file=sys.stderr)
            print("Interrupted by user", file=sys.stderr)
            print(f"Command may still be running. Check with:", file=sys.stderr)
            print(f"  pt1 get-result {command_id}", file=sys.stderr)
            return 130  # Standard exit code for SIGINT
        except Exception as e:
            print("\n", file=sys.stderr)
            print(f"Error: {str(e)}", file=sys.stderr)
            return 1
