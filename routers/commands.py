from fastapi import APIRouter
from routers.clients import command_queue

router = APIRouter()

@router.get("/next_command")
def get_next_command(client_id: str, session_id: str = "unknown"):
    if client_id not in command_queue:
        # 自動重新註冊無效的 client ID
        command_queue[client_id] = None
        print(f"[{session_id}] Auto-registered client ID: {client_id[:8]}...")
    
    command = command_queue[client_id]
    if command:
        # 清除已發送的指令
        command_queue[client_id] = None
        print(f"[{session_id}] Sending command to {client_id[:8]}...: {command}")
        return {"command": command}
    
    # 只在 session_id 不是 unknown 時顯示等待訊息
    if session_id != "unknown":
        print(f"[{session_id}] No command for {client_id[:8]}...")
    return {"command": None}

@router.post("/send_command")
def send_command(client_id: str, command: str):
    if client_id not in command_queue:
        return {"error": "Invalid client ID"}
    
    command_queue[client_id] = command
    return {"status": "Command queued"}