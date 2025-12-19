"""
Get Transcript Command

取得 agent 執行記錄內容
"""

import sys
import requests
from pt1_cli.core import Command, PT1Config


class GetTranscriptCommand(Command):
    """取得 agent 執行記錄內容"""

    def execute(self) -> int:
        """執行取得 transcript"""
        config = PT1Config()

        # 檢查設定是否完整
        if not config.is_configured():
            config.show_config_help()
            return 1

        # 檢查是否提供 transcript_id
        if len(sys.argv) < 3:
            print("Error: transcript_id is required", file=sys.stderr)
            print("", file=sys.stderr)
            print(
                f"Usage: {sys.argv[0]} get-transcript <transcript_id>", file=sys.stderr
            )
            print("", file=sys.stderr)
            print("Example:", file=sys.stderr)
            print(
                f"  {sys.argv[0]} get-transcript test-pc_20251219_094532_123",
                file=sys.stderr,
            )
            return 1

        transcript_id = sys.argv[2]

        # 查詢 transcript（固定使用 content 格式）
        try:
            response = requests.get(
                f"{config.server_url}/agent_transcript/{transcript_id}",
                headers={"X-API-Token": config.api_token},
                params={"format": "content"},
                timeout=30,
            )

            if response.status_code == 401:
                print("Error: Authentication failed", file=sys.stderr)
                print(
                    "Please check your PT1_SERVER_URL and PT1_API_TOKEN",
                    file=sys.stderr,
                )
                return 1
            elif response.status_code == 404:
                print(f"Error: Transcript '{transcript_id}' not found", file=sys.stderr)
                print(
                    "Use 'pt1 list-transcripts' to see available transcripts",
                    file=sys.stderr,
                )
                return 1
            elif response.status_code != 200:
                print(
                    f"Error: Server returned status {response.status_code}",
                    file=sys.stderr,
                )
                print(f"Response: {response.text}", file=sys.stderr)
                return 1

            # 顯示 transcript 內容
            content = response.text
            print(f"Transcript: {transcript_id}")
            print("=" * 80)
            print(content)
            print("=" * 80)

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
