import os
from fastapi import FastAPI
from pt1_server.routers import root, clients, commands, client_registry, transcripts, auth
from pt1_server.auth import get_active_token_with_metadata, get_token_expiry, _default_rotation_seconds
from pt1_server.services.client_history import client_history_middleware_factory

app = FastAPI()

# 引入各個 router 模組
app.include_router(root.router)
app.include_router(clients.router)
app.include_router(commands.router)
app.include_router(client_registry.router)
app.include_router(transcripts.router)
app.include_router(auth.router)

app.middleware("http")(client_history_middleware_factory())

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
    rotation_seconds = _default_rotation_seconds()
    if rotation_seconds % 86400 == 0:
        rotation_hint = f"{rotation_seconds} seconds ({rotation_seconds // 86400} days)"
    else:
        rotation_hint = f"{rotation_seconds} seconds"
    print(f"  Rotation interval (default): {rotation_hint}")
    
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
        print("  Public URL  : Auto-detect from request")
        print("="*80)
        print("\n📝 Installation Note:")
        print("="*80)
        print("  PUBLIC_URL not set - will auto-detect from incoming requests.")
        print("  Installation scripts will use the request's host URL automatically.")
        print("\n  To set a fixed PUBLIC_URL (optional):")
        print("    export PUBLIC_URL=https://your-domain.example.com")
        print("    or")
        print("    PUBLIC_URL=https://your-domain.example.com uvicorn pt1_server.main:app --host 0.0.0.0 --port 5566")
    
    print("="*80)
    print("")

def run_server():
    """Entry point for pt1-server command"""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5566)
