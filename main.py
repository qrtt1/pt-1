import os
from fastapi import FastAPI
from routers import root, clients, commands, client_registry, transcripts, auth
from auth import get_active_token_with_metadata, get_token_expiry, _default_rotation_seconds

app = FastAPI()

# 引入各個 router 模組
app.include_router(root.router)
app.include_router(clients.router)
app.include_router(commands.router)
app.include_router(client_registry.router)
app.include_router(transcripts.router)
app.include_router(auth.router)

@app.on_event("startup")
async def startup_event():
    # 從環境變數獲取 Public URL，如果沒有則提示使用者設定
    public_url = os.getenv("PUBLIC_URL")
    
    print("\n" + "="*80)
    print("                        DIAGNOSTIC SERVER STARTED")
    print("="*80)
    print("  Server URL  : http://localhost:5566")
    active_token, expiry, metadata = get_active_token_with_metadata()
    expiry_str = expiry.isoformat() + "Z" if expiry else "unknown"
    print(f"  Active API token: {active_token}")
    print(f"  Token expires (UTC): {expiry_str}")
    print(f"  Rotation interval (default): {_default_rotation_seconds()} seconds")
    
    if public_url:
        print(f"  Public URL  : {public_url}")
        print("="*80)
        print("\n📋 Installation Commands:")
        print("="*80)
        print("  Standard Mode (Continuous):")
        print(f"    iwr {public_url}/client_install.ps1 -UseBasicParsing | iex")
        print("\n  Single Run Mode (Development):")
        print(f"    iwr '{public_url}/client_install.ps1?single_run=true' -UseBasicParsing | iex")
        print("\n  Production Agent (Recommended):")
        print(f"    iwr {public_url}/win_agent.ps1 -UseBasicParsing | iex")
        print("="*80)
        print("  📝 Note: Production agent features auto-restart and self-healing.")
        print("  📝 Note: Single run mode waits max 10 seconds for one command, then exits.")
    else:
        print("  Public URL  : ⚠️  NOT SET")
        print("="*80)
        print("\n⚠️  PUBLIC URL NOT CONFIGURED")
        print("="*80)
        print("  Please set the PUBLIC_URL environment variable:")
        print("  export PUBLIC_URL=https://your-ngrok-url.ngrok-free.app")
        print("  or")
        print("  PUBLIC_URL=https://your-ngrok-url.ngrok-free.app uvicorn main:app --host 0.0.0.0 --port 5566")
        print("\n  Then restart the server to see installation commands.")
    
    print("="*80)
    print("")
