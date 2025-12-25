from typing import Dict, Optional
from fastapi import HTTPException
from pydantic import BaseModel
from enum import Enum
import uuid
import time


class ResultType(Enum):
    TEXT = "text"
    JSON = "json" 
    FILE = "file"
    FILES = "files"
    MIXED = "mixed"


class FileInfo(BaseModel):
    filename: str
    size: int
    content_type: str
    upload_timestamp: float


class CommandInfo(BaseModel):
    command_id: str
    stable_id: str
    command: str
    created_at: float
    scheduled_at: Optional[float] = None
    finished_at: Optional[float] = None
    status: str  # 'pending', 'executing', 'completed', 'failed'
    result: str = ""
    result_type: ResultType = ResultType.TEXT
    files: list[FileInfo] = []


class CommandManager:
    """統一管理所有 command 相關操作"""

    def __init__(self):
        self.command_history: Dict[str, CommandInfo] = {}
        # 移除 command_queues，所有狀態都透過 command_history 管理

    def _generate_short_id(self) -> str:
        """產生簡短的 command ID（使用 UUID 前 8 字元）"""
        return str(uuid.uuid4())[:8]
    
    def get_pending_commands_count(self, stable_id: str) -> int:
        """取得 client 的 pending/executing 命令數量"""
        count = 0
        for command_info in self.command_history.values():
            if (command_info.stable_id == stable_id and 
                command_info.status in ['pending', 'executing']):
                count += 1
        return count
    
    def queue_command(self, stable_id: str, command: str) -> str:
        """排隊新的 command（允許多個並行命令）"""
        # 建立新的 command（使用簡短 ID）
        command_id = self._generate_short_id()
        created_at = time.time()
        
        command_info = CommandInfo(
            command_id=command_id,
            stable_id=stable_id,
            command=command,
            created_at=created_at,
            status='pending'
        )
        
        # 儲存到 command history
        self.command_history[command_id] = command_info
        
        # 不再需要 command_queues，所有命令都透過 command_history 管理
        
        return command_id
    
    def get_next_pending_command_id(self, stable_id: str) -> Optional[str]:
        """取得 client 的下一個 pending command ID（按時間順序）"""
        # 找出所有該 client 的 pending 命令，按時間排序
        pending_commands = []
        
        for command_id, command_info in self.command_history.items():
            if (command_info.stable_id == stable_id and 
                command_info.status == 'pending'):
                pending_commands.append((command_info.created_at, command_id))
        
        if not pending_commands:
            return None
        
        # 按時間排序，取最早的
        pending_commands.sort()
        _, earliest_command_id = pending_commands[0]
        
        return earliest_command_id
    
    def get_next_command(self, stable_id: str) -> Optional[tuple]:
        """取得 client 的下一個 pending 命令（返回 command, command_id）"""
        command_id = self.get_next_pending_command_id(stable_id)
        if not command_id:
            return None
        
        command_info = self.command_history[command_id]
        return command_info.command, command_id
    
    def complete_command(self, command_id: str, result: str, status: str, result_type: ResultType) -> bool:
        """完成 command"""
        if command_id not in self.command_history:
            return False
        
        # 更新 command 資訊
        command_info = self.command_history[command_id]
        command_info.result = result
        command_info.status = status
        command_info.result_type = result_type
        command_info.finished_at = time.time()
        
        # 不需要從 queue 中移除，因為 get_pending_commands_count 會自動清理
        
        return True
    
    def get_command(self, command_id: str) -> Optional[CommandInfo]:
        """取得 command 資訊"""
        return self.command_history.get(command_id)
    
    def update_command_status(self, command_id: str, status: str) -> bool:
        """更新 command 狀態"""
        if command_id not in self.command_history:
            return False
        
        command_info = self.command_history[command_id]
        command_info.status = status
        
        # 當狀態變成 executing 時，記錄 scheduled_at
        if status == 'executing' and command_info.scheduled_at is None:
            command_info.scheduled_at = time.time()
            
        return True

    def check_timed_out_commands(self, timeout_seconds: int = 120) -> list:
        """檢查已超時的命令（2 分鐘內未完成的 executing 狀態命令）

        參數：
            timeout_seconds: 命令超時秒數（預設 120 秒）

        返回：
            超時命令的列表
        """
        now = time.time()
        timed_out = []

        for command_id, command_info in self.command_history.items():
            if command_info.status == 'executing' and command_info.scheduled_at:
                elapsed = now - command_info.scheduled_at
                if elapsed > timeout_seconds:
                    timed_out.append({
                        'command_id': command_id,
                        'stable_id': command_info.stable_id,
                        'command': command_info.command,
                        'elapsed': elapsed
                    })

        return timed_out

    def log_client_event(self, stable_id: Optional[str], event: str, status_code: int, detail: str = "") -> str:
        """Log a client API call as history event."""
        event_id = str(uuid.uuid4())
        created_at = time.time()
        status = f"client_call_{status_code}"

        command_info = CommandInfo(
            command_id=event_id,
            stable_id=stable_id or "unknown",
            command=event,
            created_at=created_at,
            finished_at=created_at,
            status=status,
            result=detail or "",
        )

        self.command_history[event_id] = command_info
        return event_id
