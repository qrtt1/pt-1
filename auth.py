import os
import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Header, HTTPException, status

# 旋轉間隔（秒），可透過環境變數覆蓋
def _get_rotation_seconds() -> int:
    default_seconds = 86400  # 24 小時
    value = os.getenv("PT1_TOKEN_ROTATION_SECONDS")
    if not value:
        return default_seconds
    try:
        parsed = int(value)
        return parsed if parsed > 0 else default_seconds
    except ValueError:
        return default_seconds


TOKEN_ROTATION_SECONDS = _get_rotation_seconds()

# 全域追蹤當前 token 與到期時間
_current_token: Optional[str] = None
_token_expiry: Optional[datetime] = None


def is_valid_uuid(token: str) -> bool:
    """檢查字串是否為合法的 UUID 格式"""
    try:
        uuid.UUID(token)
        return True
    except (ValueError, AttributeError):
        return False


def _log_active_token():
    """將目前 token 與到期時間印到 log，便於 journalctl/systemctl 查看"""
    expiry_str = _token_expiry.isoformat() + "Z" if _token_expiry else "unknown"
    print(
        f"[Auth] Active API token: {_current_token} (expires at UTC {expiry_str}, rotation every {TOKEN_ROTATION_SECONDS}s)"
    )


def rotate_token(force: bool = False) -> str:
    """
    旋轉並取得新的 token。若尚未到期且未強制，則維持當前 token。
    回傳目前有效的 token。
    """
    global _current_token, _token_expiry
    now = datetime.utcnow()

    if _current_token and _token_expiry and _token_expiry > now and not force:
        return _current_token

    _current_token = str(uuid.uuid4())
    _token_expiry = now + timedelta(seconds=TOKEN_ROTATION_SECONDS)
    _log_active_token()
    return _current_token


def get_active_token() -> str:
    """確保有有效 token 並回傳"""
    return rotate_token(force=False)


def get_token_info(token: str) -> dict:
    """
    取得 token 的 metadata

    Returns:
        dict: 包含 name 和 description，如果找不到則返回預設值
    """
    active_token = get_active_token()
    if token == active_token:
        expiry_str = _token_expiry.isoformat() + "Z" if _token_expiry else "unknown"
        return {
            "name": "rotating-token",
            "description": f"Auto-rotated in-memory token (expires at UTC {expiry_str})",
        }

    return {"name": "unknown", "description": ""}


def get_token_expiry() -> Optional[datetime]:
    """取得目前 token 的到期時間（UTC）。"""
    get_active_token()
    return _token_expiry


async def verify_token(
    x_api_token: Optional[str] = Header(None), authorization: Optional[str] = Header(None)
) -> str:
    """
    驗證 API token 的 dependency function

    支援兩種方式：
    1. X-API-Token header
    2. Authorization: Bearer <token> header

    如果 token 無效，會拋出 401 錯誤
    """
    token = None

    # 優先使用 X-API-Token
    if x_api_token:
        token = x_api_token
    # 其次嘗試從 Authorization header 提取
    elif authorization and authorization.startswith("Bearer "):
        token = authorization[7:]  # 移除 "Bearer " 前綴

    # 如果沒有提供 token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供 API token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 驗證 token 是否有效
    active_token = get_active_token()
    if token != active_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效的 API token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token
