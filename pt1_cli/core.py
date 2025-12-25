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
        self.session_cache_path = Path.home() / ".pt-1" / ".session_cache"
        load_dotenv(self.env_path, override=True)

        self.server_url = os.getenv("PT1_SERVER_URL")
        self.api_token = os.getenv("PT1_API_TOKEN")  # This is now the refresh token
        self.session_token = None  # Session token (loaded from cache or exchanged)
        self.session_expires_at = None  # Session expiry time

        # Load cached session token if available
        self._load_session_cache()

    def is_configured(self) -> bool:
        """檢查是否已設定完整的連線資訊"""
        return bool(self.server_url and self.api_token)

    def _load_session_cache(self):
        """從檔案載入 cached session token"""
        import json
        from datetime import datetime

        if not self.session_cache_path.exists():
            return

        try:
            with open(self.session_cache_path, "r") as f:
                cache = json.load(f)

            # Verify cache is for current server and refresh token
            if (
                cache.get("server_url") != self.server_url
                or cache.get("refresh_token") != self.api_token
            ):
                # Cache is for different configuration, ignore it
                return

            expires_str = cache.get("expires_at")
            if not expires_str:
                return

            # Parse expiry time
            expires_at = datetime.fromisoformat(expires_str.rstrip("Z"))

            # Check if token is still valid (with 60 seconds buffer)
            now = datetime.utcnow()
            if expires_at > now:
                self.session_token = cache.get("session_token")
                self.session_expires_at = expires_at
                # Don't print message here to avoid noise in normal operations

        except (json.JSONDecodeError, ValueError, KeyError):
            # Invalid cache file, ignore it
            pass

    def _save_session_cache(self):
        """儲存 session token 到檔案"""
        import json

        if not self.session_token or not self.session_expires_at:
            return

        cache = {
            "server_url": self.server_url,
            "refresh_token": self.api_token,
            "session_token": self.session_token,
            "expires_at": self.session_expires_at.isoformat() + "Z",
        }

        # Ensure directory exists
        self.session_cache_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.session_cache_path, "w") as f:
                json.dump(cache, f)
            # Set restrictive permissions (owner read/write only)
            os.chmod(self.session_cache_path, 0o600)
        except Exception:
            # Silently fail if we can't save cache
            pass

    def get_headers(self, use_refresh_token: bool = False) -> dict:
        """
        取得 HTTP headers

        Args:
            use_refresh_token: 是否使用 refresh token（用於 token exchange）

        Returns:
            dict: HTTP headers
        """
        if use_refresh_token:
            token = self.api_token
        else:
            token = self.session_token

        return {"X-API-Token": token, "Content-Type": "application/json"}

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

    def _ensure_session_token(self, force_refresh: bool = False):
        """確保有有效的 session token，必要時進行 token exchange

        Args:
            force_refresh: 強制取得新的 session token，忽略 cache
        """
        from datetime import datetime, timedelta

        # Check if we already have a valid session token (with 60 seconds buffer)
        if (
            not force_refresh
            and self.config.session_token
            and self.config.session_expires_at
        ):
            buffer_time = self.config.session_expires_at - timedelta(seconds=60)
            if datetime.utcnow() < buffer_time:
                return

        # Need to exchange for a new session token
        try:
            headers = self.config.get_headers(use_refresh_token=True)
            response = requests.post(
                f"{self.base_url}/auth/token/exchange", headers=headers
            )
            response.raise_for_status()
            data = response.json()

            self.config.session_token = data["session_token"]
            # Parse expires_at
            expires_str = data["expires_at"].rstrip("Z")
            self.config.session_expires_at = datetime.fromisoformat(expires_str)

            # Save to cache
            self.config._save_session_cache()

            print(f"✓ Session token obtained (expires in {data['expires_in']} seconds)")

        except requests.HTTPError as e:
            if e.response.status_code == 401:
                raise Exception(
                    "Refresh token (PT1_API_TOKEN) 無效或已過期，請檢查設定"
                )
            raise Exception(f"Token exchange 失敗: {e}")

    def get_fresh_session_token(self) -> str:
        """取得全新的 session token（用於 quickstart 等需要完整有效期的場景）

        Returns:
            str: 新的 session token
        """
        self._ensure_session_token(force_refresh=True)
        return self.config.session_token

    def verify_auth(self) -> dict:
        """
        驗證 session token 是否有效

        Returns:
            dict: API 回應

        Raises:
            requests.HTTPError: 當請求失敗時
        """
        self._ensure_session_token()
        headers = self.config.get_headers()
        response = requests.post(f"{self.base_url}/auth/verify", headers=headers)
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
        self._ensure_session_token()
        headers = self.config.get_headers()
        response = requests.post(
            f"{self.base_url}/send_command",
            headers=headers,
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
        self._ensure_session_token()
        headers = self.config.get_headers()
        response = requests.get(
            f"{self.base_url}/get_result/{command_id}", headers=headers
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
        self._ensure_session_token()
        headers = self.config.get_headers()
        response = requests.get(f"{self.base_url}/client_registry", headers=headers)
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
        self._ensure_session_token()
        headers = self.config.get_headers()
        params = {"limit": limit}
        if stable_id:
            params["stable_id"] = stable_id

        response = requests.get(
            f"{self.base_url}/command_history", headers=headers, params=params
        )
        response.raise_for_status()
        return response.json()

    def list_files(self, command_id: str) -> dict:
        """
        列出命令產生的檔案

        Args:
            command_id: 命令 ID

        Returns:
            dict: 檔案列表

        Raises:
            requests.HTTPError: 當請求失敗時
        """
        self._ensure_session_token()
        headers = self.config.get_headers()
        response = requests.get(
            f"{self.base_url}/list_files/{command_id}", headers=headers
        )
        response.raise_for_status()
        return response.json()

    def download_file(self, command_id: str, filename: str) -> requests.Response:
        """
        下載命令產生的檔案

        Args:
            command_id: 命令 ID
            filename: 檔案名稱

        Returns:
            requests.Response: 檔案內容（需要使用 stream=True）

        Raises:
            requests.HTTPError: 當請求失敗時
        """
        self._ensure_session_token()
        headers = self.config.get_headers()
        response = requests.get(
            f"{self.base_url}/download_file/{command_id}/{filename}",
            headers=headers,
            stream=True,
        )
        response.raise_for_status()
        return response

    def list_transcripts(
        self, stable_id: Optional[str] = None, limit: int = 50
    ) -> dict:
        """
        列出 agent 執行記錄

        Args:
            stable_id: 客戶端 ID（可選）
            limit: 限制結果數量

        Returns:
            dict: Transcript 列表

        Raises:
            requests.HTTPError: 當請求失敗時
        """
        self._ensure_session_token()
        headers = self.config.get_headers()
        params = {"limit": limit}
        if stable_id:
            params["stable_id"] = stable_id

        response = requests.get(
            f"{self.base_url}/agent_transcripts", headers=headers, params=params
        )
        response.raise_for_status()
        return response.json()

    def get_transcript(self, transcript_id: str, format: str = "content") -> dict:
        """
        取得 transcript 內容

        Args:
            transcript_id: Transcript ID
            format: 格式（content 或 metadata）

        Returns:
            dict: Transcript 內容

        Raises:
            requests.HTTPError: 當請求失敗時
        """
        self._ensure_session_token()
        headers = self.config.get_headers()
        response = requests.get(
            f"{self.base_url}/agent_transcript/{transcript_id}",
            headers=headers,
            params={"format": format},
        )
        response.raise_for_status()

        # When format is "content", API returns plain text
        if format == "content":
            return {"content": response.text}
        else:
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
        self._ensure_session_token()
        headers = self.config.get_headers()
        response = requests.post(
            f"{self.base_url}/terminate_client/{client_id}", headers=headers
        )
        response.raise_for_status()
        return response.json()


# 為了讓 show_config_help 使用 sys.stderr
import sys
