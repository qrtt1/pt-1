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
    timestamp: float
    status: str  # 'pending', 'executing', 'completed', 'failed'
    result: str = ""
    result_type: ResultType = ResultType.TEXT
    result_timestamp: Optional[float] = None
    files: list[FileInfo] = []


class CommandManager:
    """統一管理所有 command 相關操作"""
    
    def __init__(self):
        self.command_history: Dict[str, CommandInfo] = {}
        self.command_queues: Dict[str, List[str]] = {}  # stable_id -> [command_id1, command_id2, ...]
    
    def get_pending_commands_count(self, stable_id: str) -> int:
        """取得 client 的 pending/executing 命令數量"""
        if stable_id not in self.command_queues:
            return 0
        
        count = 0
        queue = self.command_queues[stable_id]
        
        # 清理已完成的命令並計算 pending/executing 數量
        valid_commands = []
        for command_id in queue:
            if command_id in self.command_history:
                command_info = self.command_history[command_id]
                if command_info.status in ['pending', 'executing']:
                    valid_commands.append(command_id)
                    count += 1
                elif command_info.status in ['completed', 'failed']:
                    # 已完成的命令保留在歷史中但從 queue 移除
                    pass
            
        # 更新 queue 只保留有效的命令
        self.command_queues[stable_id] = valid_commands
        return count
    
    def queue_command(self, stable_id: str, command: str) -> str:
        """排隊新的 command（允許多個並行命令）"""
        # 建立新的 command
        command_id = str(uuid.uuid4())
        timestamp = time.time()
        
        command_info = CommandInfo(
            command_id=command_id,
            stable_id=stable_id,
            command=command,
            timestamp=timestamp,
            status='pending'
        )
        
        # 儲存到 command history
        self.command_history[command_id] = command_info
        
        # 添加到 client 的 command queue
        if stable_id not in self.command_queues:
            self.command_queues[stable_id] = []
        self.command_queues[stable_id].append(command_id)
        
        # 不再使用舊的 command_queue 機制，所有命令都透過 CommandManager 管理
        
        return command_id
    
    def get_next_pending_command_id(self, stable_id: str) -> Optional[str]:
        """取得 client 的下一個 pending command ID（按時間順序）"""
        if stable_id not in self.command_queues:
            return None
        
        queue = self.command_queues[stable_id]
        
        # 找到第一個 pending 狀態的命令
        for command_id in queue:
            if command_id in self.command_history:
                command_info = self.command_history[command_id]
                if command_info.status == 'pending':
                    return command_id
        
        return None
    
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
        command_info.result_timestamp = time.time()
        
        # 不需要從 queue 中移除，因為 get_pending_commands_count 會自動清理
        
        return True
    
    def get_command(self, command_id: str) -> Optional[CommandInfo]:
        """取得 command 資訊"""
        return self.command_history.get(command_id)
    
    def update_command_status(self, command_id: str, status: str) -> bool:
        """更新 command 狀態"""
        if command_id not in self.command_history:
            return False
        self.command_history[command_id].status = status
        return True


# 單例實例
_command_manager_instance = None


def get_command_manager() -> CommandManager:
    """FastAPI 依賴注入函數"""
    global _command_manager_instance
    if _command_manager_instance is None:
        _command_manager_instance = CommandManager()
    return _command_manager_instance