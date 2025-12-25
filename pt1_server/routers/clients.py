from fastapi import APIRouter, Request, Depends
from fastapi.responses import PlainTextResponse, Response
from pt1_server.auth import verify_token
import uuid
from typing import Dict, Optional

router = APIRouter()

# 儲存待執行的指令
command_queue: Dict[str, Optional[str]] = {}


def load_template(template_name: str) -> str:
    import os
    from pathlib import Path

    # Get the directory containing this file
    current_dir = Path(__file__).parent.parent
    template_path = current_dir / "templates" / template_name
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


@router.get("/win_agent.ps1", response_class=PlainTextResponse)
def get_win_agent_script(
    request: Request,
    client_id: Optional[str] = None,
    session_token: str = Depends(verify_token),
):
    """Get Windows production agent script with transcript logging

    Query parameters:
        client_id: Optional custom client ID (e.g., ?client_id=my-dev-pc)

    Note: This endpoint accepts session token and embeds it directly in the script.
    The CLI ensures a fresh token is used for full validity period.
    """
    # 自動取得當前伺服器 URL
    base_url = f"{request.url.scheme}://{request.url.netloc}"

    # 載入並格式化 Windows 生產版代理人腳本
    template = load_template("win_agent.ps1")
    script = template.format(
        base_url=base_url, client_id=client_id or "", api_token=session_token
    )

    return script


@router.get("/client_install.ps1", response_class=PlainTextResponse)
def get_install_script(request: Request, session_token: str = Depends(verify_token)):
    """PowerShell execution unit script (called by win_agent.ps1)

    Note: This endpoint expects a session token (not refresh token).
    The win_agent.ps1 script downloads this with its embedded session token.
    """
    # 自動取得當前伺服器 URL
    base_url = f"{request.url.scheme}://{request.url.netloc}"

    # 載入並格式化 PowerShell script 範本
    template = load_template("client_install.ps1")
    script = template.format(base_url=base_url, api_token=session_token)

    return script


# Removed /clients endpoint - use /client_registry instead for complete client information


@router.get("/ai_guide", response_class=Response)
def get_ai_guide(request: Request):
    """Get AI assistant usage guide in markdown format"""
    # 自動取得當前伺服器 URL
    base_url = f"{request.url.scheme}://{request.url.netloc}"

    # 載入並格式化 AI 指南範本
    template = load_template("ai_guide.md")
    guide = template.format(base_url=base_url)

    return Response(content=guide, media_type="text/markdown")
