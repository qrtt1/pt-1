#!/usr/bin/env python3
"""
PT-1 CLI Entry Point

命令列工具的主要入口點，負責命令分派
"""

import sys
from pathlib import Path

from pt1_cli.commands.auth import AuthCommand
from pt1_cli.commands.quickstart import QuickstartCommand
from pt1_cli.commands.list_clients import ListClientsCommand
from pt1_cli.commands.send_command import SendCommandCommand
from pt1_cli.commands.get_result import GetResultCommand
from pt1_cli.commands.wait import WaitCommand
from pt1_cli.commands.history import HistoryCommand
from pt1_cli.commands.list_files import ListFilesCommand
from pt1_cli.commands.download import DownloadCommand
from pt1_cli.commands.list_transcripts import ListTranscriptsCommand
from pt1_cli.commands.get_transcript import GetTranscriptCommand
from pt1_cli.commands.help import HelpCommand
from pt1_cli.commands.prompt import PromptCommand


def main():
    """CLI 主函式"""
    program_name = Path(sys.argv[0]).name if sys.argv else "pt1"

    # 檢查是否提供命令
    if len(sys.argv) < 2:
        print(f"Usage: {program_name} <command> [options]", file=sys.stderr)
        print("", file=sys.stderr)
        print("Available commands:", file=sys.stderr)
        print("  auth              Verify API token", file=sys.stderr)
        print("  quickstart        Generate client quickstart command", file=sys.stderr)
        print("  list-clients      List all registered clients", file=sys.stderr)
        print("  send              Send command to a client", file=sys.stderr)
        print("  get-result        Get command execution result", file=sys.stderr)
        print("  wait              Wait for command completion", file=sys.stderr)
        print("  history           Show command history for a client", file=sys.stderr)
        print("  list-files        List files from command result", file=sys.stderr)
        print(
            "  download          Download a file from command result", file=sys.stderr
        )
        print("  list-transcripts  List agent execution transcripts", file=sys.stderr)
        print("  get-transcript    Get transcript content", file=sys.stderr)
        print("  help              Show detailed help", file=sys.stderr)
        print("  prompt            Show AI agent quick reference", file=sys.stderr)
        print("", file=sys.stderr)
        print(f"Run '{program_name} help' for more information.", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]

    # 命令分派
    if command == "auth":
        cmd = AuthCommand()
        sys.exit(cmd.execute())
    elif command == "quickstart":
        cmd = QuickstartCommand()
        sys.exit(cmd.execute())
    elif command == "list-clients":
        cmd = ListClientsCommand()
        sys.exit(cmd.execute())
    elif command == "send":
        cmd = SendCommandCommand()
        sys.exit(cmd.execute())
    elif command == "get-result":
        cmd = GetResultCommand()
        sys.exit(cmd.execute())
    elif command == "wait":
        cmd = WaitCommand()
        sys.exit(cmd.execute())
    elif command == "history":
        cmd = HistoryCommand()
        sys.exit(cmd.execute())
    elif command == "list-files":
        cmd = ListFilesCommand()
        sys.exit(cmd.execute())
    elif command == "download":
        cmd = DownloadCommand()
        sys.exit(cmd.execute())
    elif command == "list-transcripts":
        cmd = ListTranscriptsCommand()
        sys.exit(cmd.execute())
    elif command == "get-transcript":
        cmd = GetTranscriptCommand()
        sys.exit(cmd.execute())
    elif command == "help":
        cmd = HelpCommand()
        sys.exit(cmd.execute())
    elif command == "prompt":
        cmd = PromptCommand()
        sys.exit(cmd.execute())
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print(f"Run '{program_name} help' for usage information.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
