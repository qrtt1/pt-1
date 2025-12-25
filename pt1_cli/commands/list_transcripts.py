"""
List Transcripts Command

列出 agent 執行記錄
"""

import sys
import requests
from pt1_cli.core import Command, PT1Config, PT1Client


class ListTranscriptsCommand(Command):
    """列出 agent 執行記錄"""

    def execute(self) -> int:
        """執行列出 transcripts"""
        config = PT1Config()

        # 檢查設定是否完整
        if not config.is_configured():
            config.show_config_help()
            return 1

        # 建立 API client
        client = PT1Client(config)

        # 解析參數
        client_id = None
        limit = 50

        if len(sys.argv) >= 3:
            client_id = sys.argv[2]

        if len(sys.argv) >= 4:
            try:
                limit = int(sys.argv[3])
                if limit < 1 or limit > 200:
                    print("Error: limit must be between 1 and 200", file=sys.stderr)
                    return 1
            except ValueError:
                print("Error: limit must be a number", file=sys.stderr)
                return 1

        # 查詢 transcript 列表
        try:
            data = client.list_transcripts(stable_id=client_id, limit=limit)
            transcripts = data.get("transcripts", [])
            count = data.get("count", 0)
            filtered_by = data.get("filtered_by_client")

            # 顯示 transcript 列表
            if filtered_by:
                print(f"Transcripts for Client: {filtered_by}")
            else:
                print("All Transcripts")
            print("=" * 100)
            print(f"Total transcripts: {count}")
            print("")

            if not transcripts:
                print("No transcripts found.")
                print("")
                print(
                    "Transcripts are PowerShell session recordings uploaded by agents."
                )
                print(
                    f"Use 'pt1 list-transcripts [client_id] [limit]' to filter results."
                )
                return 0

            # 顯示 transcript 資訊
            print(f"{'TRANSCRIPT ID':<50} {'CLIENT':<20} {'SIZE':<12} {'CREATED':<20}")
            print("-" * 100)

            for transcript in transcripts:
                transcript_id = transcript.get("transcript_id", "N/A")
                client = transcript.get("client_id", "unknown")
                size = transcript.get("file_size", 0)
                created = transcript.get("created_time", "N/A")

                # 格式化檔案大小
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.2f} KB"
                else:
                    size_str = f"{size / (1024 * 1024):.2f} MB"

                # 截斷過長的 transcript_id
                display_id = (
                    transcript_id
                    if len(transcript_id) <= 47
                    else transcript_id[:44] + "..."
                )

                # 截斷過長的 client_id
                display_client = client if len(client) <= 17 else client[:14] + "..."

                # 格式化時間（只顯示日期和時間，去掉微秒）
                if created != "N/A" and "T" in created:
                    created_display = created.split(".")[0].replace("T", " ")
                else:
                    created_display = created

                print(
                    f"{display_id:<50} {display_client:<20} {size_str:<12} {created_display:<20}"
                )

            print("")
            print("To view transcript content:")
            print(f"  pt1 get-transcript <transcript_id>")
            print("")
            print("To filter by client:")
            print(f"  pt1 list-transcripts <client_id> [limit]")

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
