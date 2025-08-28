import os
from fastapi import FastAPI
from routers import root, clients, commands, dev_logs, client_registry

app = FastAPI()

# 引入各個 router 模組
app.include_router(root.router)
app.include_router(clients.router)
app.include_router(commands.router)
app.include_router(dev_logs.router)
app.include_router(client_registry.router)

@app.on_event("startup")
async def startup_event():
    # 從環境變數獲取 Public URL，如果沒有則提示使用者設定
    public_url = os.getenv("PUBLIC_URL")
    
    print("\n" + "="*80)
    print("                        DIAGNOSTIC SERVER STARTED")
    print("="*80)
    print("  Server URL  : http://localhost:5566")
    
    if public_url:
        print(f"  Public URL  : {public_url}")
        print("="*80)
        print("\n📋 Installation Commands:")
        print("="*80)
        print("  Standard Mode (Continuous):")
        print(f"    iwr {public_url}/client_install.ps1 -UseBasicParsing | iex")
        print("\n  Single Run Mode (Development):")
        print(f"    iwr '{public_url}/client_install.ps1?single_run=true' -UseBasicParsing | iex")
        print("\n  Development Auto-Updater:")
        print(f"    iwr {public_url}/dev_client_install.ps1 -UseBasicParsing | iex")
        print("="*80)
        print("  📝 Note: Single run mode waits max 10 seconds for one command, then exits.")
        print("="*80)
        print("\n🔍 Development Log Endpoints:")
        print("="*80)
        print(f"  View logs (consume): GET {public_url}/dev_log")
        print(f"  Peek logs (no consume): GET {public_url}/dev_log/peek")
        print("  📝 Note: dev_client_install.ps1 automatically uploads transcripts to /dev_log")
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