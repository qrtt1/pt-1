from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from collections import deque
import time

router = APIRouter()

# 簡單的 log 佇列 - 讀過就消失
log_queue: deque = deque()

class LogEntry(BaseModel):
    client_id: str
    session_id: str
    content: str
    timestamp: float = None

@router.post("/dev_log")
def upload_log(log_entry: LogEntry):
    """上傳客戶端 log"""
    if log_entry.timestamp is None:
        log_entry.timestamp = time.time()
    
    log_queue.append(log_entry.dict())
    print(f"[LOG] {log_entry.session_id} uploaded log: {len(log_entry.content)} chars")
    return {"status": "Log uploaded successfully"}

@router.get("/dev_log")
def get_logs():
    """讀取並清空 log 佇列"""
    logs = []
    while log_queue:
        logs.append(log_queue.popleft())
    return {"logs": logs, "count": len(logs)}

@router.get("/dev_log/peek")
def peek_logs():
    """查看 log 但不消費"""
    return {"logs": list(log_queue), "count": len(log_queue)}