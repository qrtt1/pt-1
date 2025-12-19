from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Optional
from auth import verify_token
import time
import hashlib

router = APIRouter()

# 客戶端註冊資料結構
class ClientInfo(BaseModel):
    client_id: str
    hostname: str
    username: str
    stable_id: str  # Client 提供的 ID（自訂名稱或自動生成的 hash）
    first_seen: float
    last_seen: float
    status: str  # 'online', 'offline'

# 客戶端註冊表
client_registry: Dict[str, ClientInfo] = {}
OFFLINE_TIMEOUT = 30  # 30 秒無回應視為離線

def generate_stable_id(hostname: str, username: str) -> str:
    """基於 hostname 和 username 產生穩定的客戶端 ID

    注意：此函數目前未被使用。Client 端已自行處理 ID 生成邏輯。
    保留此函數以供未來可能需要。
    """
    combined = f"{hostname.lower()}:{username.lower()}"
    return hashlib.md5(combined.encode()).hexdigest()[:12]

def update_client_status(client_id: str, hostname: str, username: str):
    """更新客戶端狀態

    使用 client 提供的 client_id 作為 stable_id。
    Client 端已處理 ID 邏輯：自訂 ID 或自動生成的 hash。
    """
    now = time.time()
    # 直接使用 client 提供的 client_id（可能是自訂名稱或自動生成的 hash）
    stable_id = client_id

    if stable_id in client_registry:
        # 更新現有客戶端
        client = client_registry[stable_id]
        client.hostname = hostname  # 更新可能變動的資訊
        client.username = username
        client.last_seen = now
        client.status = 'online'
    else:
        # 新客戶端註冊
        client_registry[stable_id] = ClientInfo(
            client_id=client_id,
            hostname=hostname,
            username=username,
            stable_id=stable_id,
            first_seen=now,
            last_seen=now,
            status='online'
        )

    return stable_id

def check_offline_clients():
    """檢查並更新離線客戶端狀態"""
    now = time.time()
    for stable_id, client in client_registry.items():
        if client.status == 'online' and (now - client.last_seen) > OFFLINE_TIMEOUT:
            client.status = 'offline'

@router.get("/client_registry")
def get_client_registry(token: str = Depends(verify_token)):
    """取得所有客戶端註冊資料"""
    check_offline_clients()
    return {
        "clients": list(client_registry.values()),
        "online_count": len([c for c in client_registry.values() if c.status == 'online']),
        "total_count": len(client_registry)
    }

@router.get("/client_registry/{stable_id}")
def get_client_info(stable_id: str, token: str = Depends(verify_token)):
    """取得特定客戶端詳細資料"""
    check_offline_clients()
    if stable_id not in client_registry:
        return {"error": "Client not found"}
    return client_registry[stable_id]

class ClientRegistration(BaseModel):
    client_id: str
    hostname: str
    username: str

@router.post("/register_client")
def register_client(registration: ClientRegistration, token: str = Depends(verify_token)):
    """註冊或更新客戶端"""
    stable_id = update_client_status(
        registration.client_id, 
        registration.hostname, 
        registration.username
    )
    return {
        "stable_id": stable_id,
        "status": "registered",
        "client_info": client_registry[stable_id]
    }