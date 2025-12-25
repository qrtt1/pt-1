"""
Services providers for dependency injection
提供服務的單例實例管理
"""

import threading
from typing import TypeVar, Type, Optional, Dict, Any
from .command_manager import CommandManager


T = TypeVar('T')


class SingletonProvider:
    """通用單例 Provider"""
    
    def __init__(self):
        self._instances: Dict[Type, Any] = {}
        self._locks: Dict[Type, threading.Lock] = {}
        self._main_lock = threading.Lock()
    
    def get_instance(self, cls: Type[T]) -> T:
        """取得單例實例"""
        if cls not in self._instances:
            with self._main_lock:
                if cls not in self._locks:
                    self._locks[cls] = threading.Lock()
            
            with self._locks[cls]:
                if cls not in self._instances:
                    self._instances[cls] = cls()
        
        return self._instances[cls]


# 全域 provider 實例
_provider = SingletonProvider()


def get_command_manager() -> CommandManager:
    """FastAPI 依賴注入函數 - 取得 CommandManager 單例"""
    return _provider.get_instance(CommandManager)


def reset_providers():
    """重置所有 provider（主要用於測試）"""
    global _provider
    _provider = SingletonProvider()