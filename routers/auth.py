from fastapi import APIRouter, Depends
from auth import verify_token, verify_refresh_token, get_token_info, create_session_token, cleanup_expired_sessions

router = APIRouter()


@router.post("/auth/token/exchange")
def exchange_token(refresh_token: str = Depends(verify_refresh_token)):
    """
    使用 refresh token (PT1_API_TOKEN) 換取 session token

    用於 CLI 工具和 PowerShell client 取得短效期 session token
    """
    # Clean up expired sessions first
    cleanup_expired_sessions()

    # Create new session token
    session_token, expires_at = create_session_token(refresh_token)

    return {
        "session_token": session_token,
        "expires_at": expires_at.isoformat() + "Z",
        "token_type": "Bearer",
        "expires_in": int((expires_at - __import__('datetime').datetime.utcnow()).total_seconds()),
    }


@router.post("/auth/verify")
def verify_auth(token: str = Depends(verify_token)):
    """
    驗證 session token 是否有效

    用於 CLI 工具測試連線和認證
    注意：此 endpoint 現在只接受 session token，不接受 refresh token
    """
    return {
        "authenticated": True,
        "message": "Session token is valid",
    }
