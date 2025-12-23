import json
from typing import Optional, Callable, Awaitable

from fastapi import Request, HTTPException

from services.providers import get_command_manager


def _extract_command_id(path_parts: list[str]) -> str:
    if len(path_parts) < 2:
        return ""
    if path_parts[1] in {"upload_files", "get_result", "list_files"} and len(path_parts) >= 3:
        return path_parts[2]
    if path_parts[1] == "download_file" and len(path_parts) >= 3:
        return path_parts[2]
    return ""


def _extract_stable_id_from_path(path_parts: list[str]) -> str:
    if len(path_parts) < 2:
        return ""
    if path_parts[1] == "client_registry" and len(path_parts) >= 3:
        return path_parts[2]
    if path_parts[1] == "agent_transcript" and len(path_parts) >= 3:
        return path_parts[2]
    return ""


def _truncate_value(value: str, limit: int = 80) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + "..."


def _collect_query_args(request: Request) -> list[str]:
    args = []
    for key, value in request.query_params.multi_items():
        if value:
            args.append(f"{key}={_truncate_value(str(value))}")
    return args


def _safe_json_args(path: str, data: dict) -> list[str]:
    args = []
    if path == "/register_client":
        for key in ("client_id", "hostname", "username"):
            value = data.get(key)
            if value:
                args.append(f"{key}={_truncate_value(str(value))}")
        return args

    if path == "/submit_result":
        for key in ("command_id", "status", "result_type"):
            value = data.get(key)
            if value:
                args.append(f"{key}={_truncate_value(str(value))}")
        return args

    for key in ("client_id", "stable_id", "command_id", "limit"):
        value = data.get(key)
        if value:
            args.append(f"{key}={_truncate_value(str(value))}")

    return args


def client_history_middleware_factory() -> Callable[[Request, Callable[..., Awaitable]], Awaitable]:
    async def log_client_calls(request: Request, call_next: Callable[..., Awaitable]):
        path = request.url.path
        cmd_manager = get_command_manager()
        method = request.method
        stable_id = None
        detail_args: list[str] = []
        event_label = f"client_api {method} {path}"

        detail_args.extend(_collect_query_args(request))
        if "client_id" in request.query_params:
            stable_id = request.query_params.get("client_id")
        elif "stable_id" in request.query_params:
            stable_id = request.query_params.get("stable_id")

        path_parts = path.strip("/").split("/")
        path_stable_id = _extract_stable_id_from_path(path_parts)
        if path_stable_id:
            stable_id = path_stable_id
            detail_args.append(f"client_id={_truncate_value(path_stable_id)}")

        command_id = _extract_command_id(path_parts)
        if command_id:
            detail_args.append(f"command_id={_truncate_value(command_id)}")
            command_info = cmd_manager.get_command(command_id)
            if command_info:
                stable_id = command_info.stable_id

        data = {}
        body = b""
        content_type = request.headers.get("content-type", "")
        if method in {"POST", "PUT", "PATCH"} and "application/json" in content_type:
            body = await request.body()
            if body:
                # 先解碼 bytes 為 str，處理非 UTF-8 編碼（如 Windows-1252）
                try:
                    body_str = body.decode('utf-8')
                except UnicodeDecodeError as e:
                    # latin-1 可處理所有單 byte (0x00-0xFF)，不會失敗
                    body_str = body.decode('latin-1')
                    print(f"[DEBUG] UnicodeDecodeError on {path}: {e}")
                    print(f"[DEBUG] Raw body (first 500 bytes): {body[:500]!r}")
                # 無論 JSON 是否有效，都確保 body 是 UTF-8 編碼
                body = body_str.encode('utf-8')
                try:
                    data = json.loads(body_str)
                except json.JSONDecodeError as e:
                    print(f"[DEBUG] JSONDecodeError on {path}: {e}")
                    print(f"[DEBUG] body_str (first 500 chars): {body_str[:500]!r}")
                    data = {}

            json_stable_id = data.get("client_id") or data.get("stable_id")
            if json_stable_id:
                stable_id = json_stable_id

            json_command_id = data.get("command_id")
            if json_command_id:
                command_info = cmd_manager.get_command(json_command_id)
                if command_info:
                    stable_id = command_info.stable_id
                else:
                    stable_id = stable_id or data.get("client_id") or data.get("stable_id")

            detail_args.extend(_safe_json_args(path, data))

            async def receive():
                return {"type": "http.request", "body": body}

            request = Request(request.scope, receive)

        detail = "&".join(detail_args)

        try:
            response = await call_next(request)
        except HTTPException as exc:
            cmd_manager.log_client_event(stable_id, event_label, exc.status_code, detail)
            raise
        except Exception:
            cmd_manager.log_client_event(stable_id, event_label, 500, detail)
            raise

        if not (path == "/next_command" and response.status_code == 200):
            cmd_manager.log_client_event(stable_id, event_label, response.status_code, detail)
        return response

    return log_client_calls
