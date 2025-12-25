import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pt1_server.routers import root, clients, commands, client_registry, transcripts, auth
from pt1_server.auth import get_active_token_with_metadata, get_token_expiry, _default_rotation_seconds
from pt1_server.services.client_history import client_history_middleware_factory


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("\n" + "="*80)
    print("                        PT-1 SERVER STARTED")
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
    print("="*80)
    print("")

    yield

    # Shutdown (if needed in the future)


app = FastAPI(lifespan=lifespan)

# 引入各個 router 模組
app.include_router(root.router)
app.include_router(clients.router)
app.include_router(commands.router)
app.include_router(client_registry.router)
app.include_router(transcripts.router)
app.include_router(auth.router)

app.middleware("http")(client_history_middleware_factory())

def run_server():
    """Entry point for pt1-server command"""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5566)
