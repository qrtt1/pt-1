import json
import os
import uuid
from typing import Optional
from fastapi import Header, HTTPException, status

# 全局變數來快取 tokens
_tokens_cache: Optional[set] = None


def is_valid_uuid(token: str) -> bool:
    """檢查字串是否為合法的 UUID 格式"""
    try:
        uuid.UUID(token)
        return True
    except (ValueError, AttributeError):
        return False


def load_tokens() -> set:
    """載入 tokens.json 檔案並回傳有效的 token 集合"""
    global _tokens_cache

    # 如果已經載入過，直接回傳快取
    if _tokens_cache is not None:
        return _tokens_cache

    tokens_file = os.path.join(os.path.dirname(__file__), "tokens.json")
    tokens_file_abs = os.path.abspath(tokens_file)

    print(f"[Auth] Loading tokens from: {tokens_file_abs}")

    # 如果檔案不存在，回傳空集合
    if not os.path.exists(tokens_file):
        print(f"[Auth] Warning: tokens.json not found at {tokens_file_abs}")
        _tokens_cache = set()
        return _tokens_cache

    try:
        with open(tokens_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            tokens_data = data.get("tokens", [])

            # 驗證每個 token 是否為合法的 UUID
            valid_tokens = set()
            invalid_count = 0

            for item in tokens_data:
                token = item.get("token", "")
                token_name = item.get("name", "unknown")

                if is_valid_uuid(token):
                    valid_tokens.add(token)
                else:
                    invalid_count += 1
                    print(
                        f"[Auth] Warning: Invalid UUID token '{token}' for '{token_name}', skipping"
                    )

            _tokens_cache = valid_tokens

            if invalid_count > 0:
                print(
                    f"[Auth] Successfully loaded {len(_tokens_cache)} valid token(s), skipped {invalid_count} invalid token(s)"
                )
            else:
                print(f"[Auth] Successfully loaded {len(_tokens_cache)} token(s)")

            return _tokens_cache
    except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
        # 如果檔案格式錯誤，回傳空集合
        print(f"[Auth] Error loading tokens: {e}")
        _tokens_cache = set()
        return _tokens_cache


def reload_tokens():
    """重新載入 tokens（用於手動更新 tokens.json 後）"""
    global _tokens_cache
    _tokens_cache = None
    return load_tokens()


def get_token_info(token: str) -> dict:
    """
    取得 token 的 metadata

    Returns:
        dict: 包含 name 和 description，如果找不到則返回預設值
    """
    tokens_file = os.path.join(os.path.dirname(__file__), "tokens.json")

    try:
        with open(tokens_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            tokens_data = data.get("tokens", [])

            for item in tokens_data:
                if item.get("token") == token:
                    return {
                        "name": item.get("name", "unknown"),
                        "description": item.get("description", ""),
                    }
    except:
        pass

    return {"name": "unknown", "description": ""}


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
    valid_tokens = load_tokens()
    if token not in valid_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效的 API token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token
