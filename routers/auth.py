from fastapi import APIRouter, Depends
from auth import verify_token, get_token_info

router = APIRouter()


@router.post("/auth/verify")
def verify_auth(token: str = Depends(verify_token)):
    """
    驗證 API token 是否有效

    用於 CLI 工具測試連線和認證
    """
    token_info = get_token_info(token)

    return {
        "authenticated": True,
        "message": "Token is valid",
        "token_name": token_info["name"],
        "token_description": token_info["description"],
    }
