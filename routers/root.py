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
            "clients": f"{base_url}/clients"
        },
        "quick_start": {
            "ai_assistant_guide": f"{base_url}/ai_guide",
            "windows_agent": f"{base_url}/win_agent.ps1",
            "windows_agent_dev": f"{base_url}/win_agent_dev.ps1", 
            "single_run_mode": f"{base_url}/client_install.ps1?single_run=true"
        },
        "documentation": f"{base_url}/ai_guide"
    }