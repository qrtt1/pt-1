from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse, Response
import uuid
from typing import Dict, Optional

router = APIRouter()

# 儲存待執行的指令
command_queue: Dict[str, Optional[str]] = {}

def load_template(template_name: str) -> str:
    with open(f"templates/{template_name}", "r", encoding="utf-8") as f:
        return f.read()

@router.get("/win_agent.ps1", response_class=PlainTextResponse) 
def get_win_agent_script(request: Request):
    """Get Windows production agent script with transcript logging"""
    # 自動取得當前伺服器 URL
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    
    # 載入並格式化 Windows 生產版代理人腳本
    template = load_template("win_agent.ps1")
    script = template.format(base_url=base_url)
    
    return script


@router.get("/client_install.ps1", response_class=PlainTextResponse)
def get_install_script(request: Request):
    """PowerShell execution unit script (called by win_agent.ps1)"""
    # 自動取得當前伺服器 URL
    base_url = f"{request.url.scheme}://{request.url.netloc}"

    # 載入並格式化 PowerShell script 範本
    template = load_template("client_install.ps1")
    script = template.format(base_url=base_url)

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