from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/")
def read_root(request: Request):
    """Root endpoint with service overview and quick links"""
    base_url = f"{request.url.scheme}://{request.url.netloc}"

    return {
        "service": "PowerShell Remote Execution Service",
        "description": "Remote PowerShell command execution for AI assistants",
        "status": "running",
        "endpoints": {
            "ai_guide": f"{base_url}/ai_guide",
            "send_command": f"{base_url}/send_command",
            "command_history": f"{base_url}/command_history",
            "client_registry": f"{base_url}/client_registry",
        },
        "quick_start": {
            "ai_assistant_guide": f"{base_url}/ai_guide",
            "production_agent": f"{base_url}/win_agent.ps1",
            "execution_unit": f"{base_url}/client_install.ps1",
        },
        "documentation": f"{base_url}/ai_guide",
    }
