"""
PT-1 CLI Core Module

包含：
- Command 抽象基礎類別
- PT1Config 設定管理
- PT1Client API 客戶端
"""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv


class Command(ABC):
    """命令的抽象基礎類別"""

    @abstractmethod
    def execute(self) -> int:
        """
        執行命令

        Returns:
            int: Exit code (0=成功, 1=失敗)
        """
        pass


class PT1Config:
    """PT-1 CLI 設定管理"""

    def __init__(self):
        """從 ~/.pt-1/.env 載入設定"""
        self.env_path = Path.home() / ".pt-1" / ".env"
        load_dotenv(self.env_path, override=True)

        self.server_url = os.getenv("PT1_SERVER_URL")
        self.api_token = os.getenv("PT1_API_TOKEN")

    def is_configured(self) -> bool:
        """檢查是否已設定完整的連線資訊"""
        return bool(self.server_url and self.api_token)

    def get_headers(self) -> dict:
        """取得 HTTP headers（包含 API token）"""
        return {"X-API-Token": self.api_token, "Content-Type": "application/json"}

    def show_config_help(self):
        """顯示設定說明"""
        print("Error: PT-1 CLI not configured.", file=sys.stderr)
        print("", file=sys.stderr)
        print(f"Please create a .env file at: {self.env_path}", file=sys.stderr)
        print("", file=sys.stderr)
        print("Content:", file=sys.stderr)
        print("  PT1_SERVER_URL=https://your-server.example.com", file=sys.stderr)
        print("  PT1_API_TOKEN=your-api-token-here", file=sys.stderr)
        print("", file=sys.stderr)
        print(
            "You can get your API token from the server administrator.", file=sys.stderr
        )
        print("", file=sys.stderr)
        print("Example:", file=sys.stderr)
        print(f"  mkdir -p {self.env_path.parent}", file=sys.stderr)
        print(f"  cat > {self.env_path} << 'EOF'", file=sys.stderr)
        print("  PT1_SERVER_URL=https://your-server.example.com", file=sys.stderr)
        print("  PT1_API_TOKEN=your-api-token-here", file=sys.stderr)
        print("  EOF", file=sys.stderr)


class PT1Client:
    """PT-1 API 客戶端"""

    def __init__(self, config: PT1Config):
        """
        初始化 API 客戶端

        Args:
            config: PT1Config 實例
        """
        self.config = config
        self.base_url = config.server_url.rstrip("/")
        self.headers = config.get_headers()

    def verify_auth(self) -> dict:
        """
        驗證 API token 是否有效

        Returns:
            dict: API 回應

        Raises:
            requests.HTTPError: 當請求失敗時
        """
        response = requests.post(f"{self.base_url}/auth/verify", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def send_command(self, client_id: str, command: str) -> dict:
        """
        發送命令到指定客戶端

        Args:
            client_id: 客戶端 ID
            command: PowerShell 命令

        Returns:
            dict: API 回應，包含 command_id

        Raises:
            requests.HTTPError: 當請求失敗時
        """
        response = requests.post(
            f"{self.base_url}/send_command",
            headers=self.headers,
            json={"client_id": client_id, "command": command},
        )
        response.raise_for_status()
        return response.json()

    def get_result(self, command_id: str) -> dict:
        """
        取得命令執行結果

        Args:
            command_id: 命令 ID

        Returns:
            dict: 命令執行結果

        Raises:
            requests.HTTPError: 當請求失敗時
        """
        response = requests.get(
            f"{self.base_url}/get_result/{command_id}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def list_clients(self) -> dict:
        """
        列出所有已註冊的客戶端

        Returns:
            dict: 客戶端列表

        Raises:
            requests.HTTPError: 當請求失敗時
        """
        response = requests.get(
            f"{self.base_url}/client_registry", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_command_history(
        self, stable_id: Optional[str] = None, limit: int = 50
    ) -> dict:
        """
        取得命令歷史

        Args:
            stable_id: 客戶端 ID（可選）
            limit: 限制結果數量

        Returns:
            dict: 命令歷史

        Raises:
            requests.HTTPError: 當請求失敗時
        """
        params = {"limit": limit}
        if stable_id:
            params["stable_id"] = stable_id

        response = requests.get(
            f"{self.base_url}/command_history", headers=self.headers, params=params
        )
        response.raise_for_status()
        return response.json()

    def terminate_client(self, client_id: str) -> dict:
        """
        發送優雅終止信號給指定客戶端

        Args:
            client_id: 客戶端 ID

        Returns:
            dict: API 回應，包含 command_id 和狀態

        Raises:
            requests.HTTPError: 當請求失敗時
        """
        response = requests.post(
            f"{self.base_url}/terminate_client/{client_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()


# 為了讓 show_config_help 使用 sys.stderr
import sys
