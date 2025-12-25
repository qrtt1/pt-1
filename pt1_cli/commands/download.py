"""
Download Command

下載命令產生的檔案
"""

import sys
import os
import requests
from pathlib import Path
from pt1_cli.core import Command, PT1Config, PT1Client


class DownloadCommand(Command):
    """下載命令產生的檔案"""

    def execute(self) -> int:
        """執行下載檔案"""
        config = PT1Config()

        # 檢查設定是否完整
        if not config.is_configured():
            config.show_config_help()
            return 1

        # 建立 API client
        client = PT1Client(config)

        # 檢查是否提供必要參數
        if len(sys.argv) < 4:
            print("Error: command_id and filename are required", file=sys.stderr)
            print("", file=sys.stderr)
            print(
                f"Usage: {sys.argv[0]} download <command_id> <filename> [output_path]",
                file=sys.stderr,
            )
            print("", file=sys.stderr)
            print("Arguments:", file=sys.stderr)
            print("  command_id    The command ID", file=sys.stderr)
            print("  filename      The filename to download", file=sys.stderr)
            print(
                "  output_path   Optional output path (default: current directory)",
                file=sys.stderr,
            )
            print("", file=sys.stderr)
            print("Example:", file=sys.stderr)
            print(
                f"  {sys.argv[0]} download 1c424006-b72d-49fd-bdb9-109fb8d63d1e output.txt",
                file=sys.stderr,
            )
            print(
                f"  {sys.argv[0]} download 1c424006-b72d-49fd-bdb9-109fb8d63d1e output.txt ./downloads/",
                file=sys.stderr,
            )
            return 1

        command_id = sys.argv[2]
        filename = sys.argv[3]

        # 決定輸出路徑
        if len(sys.argv) >= 5:
            output_path = Path(sys.argv[4])
            # 如果是目錄，使用原始檔名
            if output_path.is_dir() or output_path.suffix == "":
                output_path = output_path / filename
        else:
            # 預設存到當前目錄
            output_path = Path(filename)

        # 檢查輸出檔案是否已存在
        if output_path.exists():
            print(f"Error: Output file '{output_path}' already exists", file=sys.stderr)
            print(
                "Please specify a different output path or delete the existing file",
                file=sys.stderr,
            )
            return 1

        # 確保輸出目錄存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 下載檔案
        try:
            print(f"Downloading {filename} from command {command_id}...")

            response = client.download_file(command_id, filename)

            # 寫入檔案
            total_size = 0
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        total_size += len(chunk)

            # 格式化檔案大小
            if total_size < 1024:
                size_str = f"{total_size} B"
            elif total_size < 1024 * 1024:
                size_str = f"{total_size / 1024:.2f} KB"
            else:
                size_str = f"{total_size / (1024 * 1024):.2f} MB"

            print(f"✓ Downloaded successfully: {output_path}")
            print(f"  Size: {size_str}")

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
            # 清理未完成的檔案
            if output_path.exists():
                output_path.unlink()
            return 1
        except requests.exceptions.Timeout:
            print("Error: Request timed out", file=sys.stderr)
            # 清理未完成的檔案
            if output_path.exists():
                output_path.unlink()
            return 1
        except Exception as e:
            print(f"Error: {str(e)}", file=sys.stderr)
            # 清理未完成的檔案
            if output_path.exists():
                output_path.unlink()
            return 1
