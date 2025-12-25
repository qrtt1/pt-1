import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict
from fastapi import Header, HTTPException, status

# Path to tokens file (persistent source of truth)
TOKENS_FILE = os.path.join(os.path.dirname(__file__), "tokens.json")

# Session token storage (in-memory)
_session_tokens: Dict[str, Dict] = {}  # session_token -> {refresh_token, expires_at, created_at}

# In-memory state
_active_token: Optional[str] = None
_active_expiry: Optional[datetime] = None
_active_name: str = "rotating-token"
_active_description: str = "Auto-rotated token (persistent)"

# Session token duration (default 1 hour)
def _session_token_duration_seconds() -> int:
    default_seconds = 3600  # 1 hour
    value = os.getenv("PT1_SESSION_TOKEN_DURATION_SECONDS")
    if not value:
        return default_seconds
    try:
        parsed = int(value)
        return parsed if parsed > 0 else default_seconds
    except ValueError:
        return default_seconds


# Default rotation interval (seconds) if not specified on token
def _default_rotation_seconds() -> int:
    default_seconds = 604800  # 7 days
    value = os.getenv("PT1_TOKEN_ROTATION_SECONDS")
    if not value:
        return default_seconds
    try:
        parsed = int(value)
        return parsed if parsed > 0 else default_seconds
    except ValueError:
        return default_seconds


def is_valid_uuid(token: str) -> bool:
    """Check if string is a valid UUID."""
    try:
        uuid.UUID(token)
        return True
    except (ValueError, AttributeError):
        return False


def _load_tokens_file() -> dict:
    """Load tokens.json content, return dict with 'tokens' list."""
    if not os.path.exists(TOKENS_FILE):
        return {"tokens": []}

    with open(TOKENS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _persist_tokens(data: dict):
    """Persist tokens.json (overwrites file)."""
    with open(TOKENS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _parse_token_entry(item: dict) -> Optional[Tuple[str, str, str, Optional[int], Optional[datetime]]]:
    """
    Parse a token entry.

    Returns:
        tuple: (token, name, description, rotation_seconds, expires_at)
    """
    token = item.get("token", "")
    name = item.get("name", "unknown")
    description = item.get("description", "")
    rotation_seconds = item.get("rotation_seconds")
    expires_at_raw = item.get("expires_at")

    if not is_valid_uuid(token):
        print(f"[Auth] Warning: Invalid UUID token '{token}' for '{name}', skipping")
        return None

    expires_at = None
    if expires_at_raw:
        try:
            expires_at = datetime.fromisoformat(expires_at_raw.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            print(f"[Auth] Warning: Invalid expires_at '{expires_at_raw}' for '{name}', ignoring expiry")
            expires_at = None

    return token, name, description, rotation_seconds, expires_at


def _select_active_token(tokens_data: List[dict]) -> Tuple[str, str, str, datetime, List[dict]]:
    """
    Select an active token from tokens.json with rotation support.

    Returns:
        tuple: (active_token, name, description, expiry, updated_tokens_data)
    """
    now = datetime.utcnow()
    default_rotation = _default_rotation_seconds()
    updated_entries = []
    active_candidate = None

    for item in tokens_data:
        parsed = _parse_token_entry(item)
        if not parsed:
            continue

        token, name, description, rotation_seconds, expires_at = parsed
        rotation = rotation_seconds or default_rotation

        if expires_at and expires_at > now:
            # Not expired; keep as-is
            updated_entries.append(
                {
                    "token": token,
                    "name": name,
                    "description": description,
                    "rotation_seconds": rotation_seconds,
                    "expires_at": expires_at.isoformat() + "Z",
                }
            )
            if not active_candidate:
                active_candidate = (token, name, description, expires_at)
            continue

        # Expired or no expiry; rotate if rotation is defined
        new_token = str(uuid.uuid4())
        new_expiry = now + timedelta(seconds=rotation)
        updated_entries.append(
            {
                "token": new_token,
                "name": name,
                "description": description,
                "rotation_seconds": rotation_seconds,
                "expires_at": new_expiry.isoformat() + "Z",
            }
        )
        if not active_candidate:
            active_candidate = (new_token, name, description, new_expiry)

    if not active_candidate:
        # No valid tokens; generate a default one
        new_token = str(uuid.uuid4())
        new_expiry = now + timedelta(seconds=default_rotation)
        generated = {
            "token": new_token,
            "name": "generated-default",
            "description": "Generated because tokens.json had no valid entries",
            "rotation_seconds": default_rotation,
            "expires_at": new_expiry.isoformat() + "Z",
        }
        updated_entries.append(generated)
        active_candidate = (
            generated["token"],
            generated["name"],
            generated["description"],
            new_expiry,
        )

    return active_candidate[0], active_candidate[1], active_candidate[2], active_candidate[3], updated_entries


def get_active_token_with_metadata() -> Tuple[str, datetime, dict]:
    """Get active token and metadata; rotates/persists if needed."""
    global _active_token, _active_expiry, _active_name, _active_description

    now = datetime.utcnow()
    if _active_token and _active_expiry and _active_expiry > now:
        return _active_token, _active_expiry, {"name": _active_name, "description": _active_description}

    data = _load_tokens_file()
    tokens_data = data.get("tokens", [])

    active_token, name, description, expiry, updated_entries = _select_active_token(tokens_data)
    data["tokens"] = updated_entries
    _persist_tokens(data)

    _active_token = active_token
    _active_expiry = expiry
    _active_name = name
    _active_description = description

    expiry_str = expiry.isoformat() + "Z" if expiry else "unknown"
    print(
        f"[Auth] Active API token: {_active_token} (expires at UTC {expiry_str}, rotation every {_default_rotation_seconds()}s)"
    )

    return _active_token, _active_expiry, {"name": _active_name, "description": _active_description}


def get_token_info(token: str) -> dict:
    """
    Retrieve token metadata for auth verification endpoint.
    """
    active_token, expiry, metadata = get_active_token_with_metadata()
    if token == active_token:
        expiry_str = expiry.isoformat() + "Z" if expiry else "unknown"
        desc = metadata.get("description", "")
        if desc:
            desc = f"{desc} (expires at UTC {expiry_str})"
        else:
            desc = f"Expires at UTC {expiry_str}"
        return {
            "name": metadata.get("name", "unknown"),
            "description": desc,
        }

    return {"name": "unknown", "description": ""}


def get_token_expiry() -> Optional[datetime]:
    """Get current token expiry (UTC)."""
    _, expiry, _ = get_active_token_with_metadata()
    return expiry


def get_active_token_with_metadata() -> Tuple[str, datetime, dict]:
    """Get active token and metadata; rotates/persists if needed."""
    global _active_token, _active_expiry, _active_name, _active_description

    now = datetime.utcnow()
    if _active_token and _active_expiry and _active_expiry > now:
        return _active_token, _active_expiry, {"name": _active_name, "description": _active_description}

    data = _load_tokens_file()
    tokens_data = data.get("tokens", [])

    active_token, name, description, expiry, updated_entries = _select_active_token(tokens_data)
    data["tokens"] = updated_entries
    _persist_tokens(data)

    _active_token = active_token
    _active_expiry = expiry
    _active_name = name
    _active_description = description

    expiry_str = expiry.isoformat() + "Z" if expiry else "unknown"
    print(
        f"[Auth] Active API token: {_active_token} (expires at UTC {expiry_str}, rotation every {_default_rotation_seconds()}s)"
    )

    return _active_token, _active_expiry, {"name": _active_name, "description": _active_description}


def create_session_token(refresh_token: str) -> Tuple[str, datetime]:
    """
    Create a new session token from a refresh token.

    Args:
        refresh_token: The refresh token (PT1_API_TOKEN)

    Returns:
        Tuple of (session_token, expires_at)
    """
    # Verify refresh token is valid
    active_token, _, _ = get_active_token_with_metadata()
    if refresh_token != active_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效的 refresh token",
        )

    # Generate session token
    session_token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(seconds=_session_token_duration_seconds())

    # Store session token
    _session_tokens[session_token] = {
        "refresh_token": refresh_token,
        "expires_at": expires_at,
        "created_at": datetime.utcnow(),
    }

    print(f"[Auth] Created session token {session_token[:8]}... (expires at {expires_at.isoformat()}Z)")

    return session_token, expires_at


def verify_session_token(session_token: str) -> bool:
    """
    Verify if a session token is valid and not expired.

    Args:
        session_token: The session token to verify

    Returns:
        True if valid, False otherwise
    """
    if session_token not in _session_tokens:
        return False

    token_data = _session_tokens[session_token]
    now = datetime.utcnow()

    # Check if expired
    if token_data["expires_at"] <= now:
        # Clean up expired token
        del _session_tokens[session_token]
        return False

    return True


def cleanup_expired_sessions():
    """Remove expired session tokens from memory."""
    now = datetime.utcnow()
    expired = [
        token for token, data in _session_tokens.items()
        if data["expires_at"] <= now
    ]
    for token in expired:
        del _session_tokens[token]

    if expired:
        print(f"[Auth] Cleaned up {len(expired)} expired session token(s)")


async def verify_refresh_token(
    x_api_token: Optional[str] = Header(None), authorization: Optional[str] = Header(None)
) -> str:
    """
    Validate refresh token (PT1_API_TOKEN) for token exchange endpoint only.

    Supported headers:
    1. X-API-Token
    2. Authorization: Bearer <token>
    """
    token = None

    if x_api_token:
        token = x_api_token
    elif authorization and authorization.startswith("Bearer "):
        token = authorization[7:]  # Remove "Bearer " prefix

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供 refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    active_token, _, _ = get_active_token_with_metadata()
    if token != active_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效的 refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token


async def verify_token(
    x_api_token: Optional[str] = Header(None), authorization: Optional[str] = Header(None)
) -> str:
    """
    Validate session token (FastAPI dependency).

    This now ONLY accepts session tokens, not refresh tokens.

    Supported headers:
    1. X-API-Token
    2. Authorization: Bearer <token>
    """
    token = None

    if x_api_token:
        token = x_api_token
    elif authorization and authorization.startswith("Bearer "):
        token = authorization[7:]  # Remove "Bearer " prefix

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供 session token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify session token
    if not verify_session_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token 無效或已過期，請使用 refresh token 重新取得",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token
