from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse
import uuid
from typing import Dict, Optional

router = APIRouter()

# 儲存待執行的指令
command_queue: Dict[str, Optional[str]] = {}

def load_template(template_name: str) -> str:
    with open(f"templates/{template_name}", "r", encoding="utf-8") as f:
        return f.read()

@router.get("/client_install.ps1", response_class=PlainTextResponse)
def get_install_script(request: Request, single_run: bool = False):
    # 產生唯一的 client ID
    client_id = str(uuid.uuid4())
    
    # 初始化該 client 的指令佇列
    command_queue[client_id] = None
    
    # 自動取得當前伺服器 URL
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    
    # 載入並格式化 PowerShell script 範本
    template = load_template("client_install.ps1")
    script = template.format(
        client_id=client_id, 
        base_url=base_url,
        single_run="$true" if single_run else "$false"
    )
    
    return script

@router.get("/dev_client_install.ps1", response_class=PlainTextResponse)
def get_dev_install_script(request: Request):
    # 自動取得當前伺服器 URL
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    
    # 載入並格式化開發版 PowerShell script 範本
    template = load_template("dev_client_install.ps1")
    script = template.format(base_url=base_url)
    
    return script

@router.get("/clients")
def list_clients():
    return {"clients": list(command_queue.keys())}