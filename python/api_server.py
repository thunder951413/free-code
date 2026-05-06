"""Optional FastAPI server wrapper around the free-code Python bridge."""

from __future__ import annotations

import json
import time
from typing import Any, Dict, Iterable, Optional

try:
    from .free_code_cli_client import extract_assistant_text
    from .web_bridge import FreeCodeWebBridge
except ImportError:
    from free_code_cli_client import extract_assistant_text
    from web_bridge import FreeCodeWebBridge


def _require_fastapi():
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.responses import StreamingResponse
    except ImportError as exc:
        raise RuntimeError(
            "This module requires FastAPI. Install it with: "
            "pip install fastapi uvicorn"
        ) from exc
    return FastAPI, HTTPException, StreamingResponse


def _assistant_text_from_events(events: Iterable[Dict[str, Any]]) -> str:
    chunks = []
    for event in events:
        text = extract_assistant_text(event)
        if text:
            chunks.append(text)
    return "".join(chunks)


def create_app(
    *,
    cli_path: Optional[str] = None,
    cwd: Optional[str] = None,
    extra_args: Optional[Iterable[str]] = None,
    env: Optional[Dict[str, str]] = None,
    auto_permission_handler=None,
) -> Any:
    FastAPI, HTTPException, StreamingResponse = _require_fastapi()

    bridge = FreeCodeWebBridge(
        cli_path=cli_path,
        cwd=cwd,
        extra_args=extra_args,
        env=env,
        auto_permission_handler=auto_permission_handler,
    )
    app = FastAPI(title="free-code Python bridge")

    @app.get("/health")
    def health() -> Dict[str, Any]:
        return {"ok": True}

    @app.get("/sessions")
    def list_sessions() -> Dict[str, Any]:
        sessions = bridge.list_sessions()
        return {
            "sessions": [
                {"session_id": s.session_id, "cli_session_id": s.cli_session_id}
                for s in sessions
            ]
        }

    @app.post("/sessions")
    def ensure_session(payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = payload or {}
        session = bridge.ensure_session(
            session_id=payload.get("session_id", ""),
            cli_session_id=payload.get("cli_session_id"),
            settings_path=payload.get("settings_path"),
            cwd=payload.get("cwd"),
        )
        return {
            "session_id": session.session_id,
            "cli_session_id": session.cli_session_id,
        }

    @app.get("/sessions/{session_id}")
    def get_session(session_id: str) -> Dict[str, Any]:
        try:
            session = bridge.get_session(session_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {
            "session_id": session.session_id,
            "cli_session_id": session.cli_session_id,
        }

    @app.delete("/sessions/{session_id}")
    def close_session(session_id: str) -> Dict[str, Any]:
        bridge.close_session(session_id)
        return {"ok": True, "session_id": session_id}

    @app.post("/chat/{session_id}")
    def chat(session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        message = payload.get("message")
        if not isinstance(message, str) or not message.strip():
            raise HTTPException(status_code=400, detail="message must be a non-empty string")

        timeout_value = payload.get("timeout", 180)
        try:
            timeout = float(timeout_value)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="timeout must be a number")

        try:
            events = bridge.ask(session_id, message, timeout=timeout)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        result_event = next((event for event in reversed(events) if event.get("type") == "result"), None)
        return {
            "session_id": session_id,
            "assistant_text": _assistant_text_from_events(events),
            "result": result_event,
            "events": events,
        }

    @app.post("/chat/{session_id}/stream")
    def chat_stream(session_id: str, payload: Dict[str, Any]) -> Any:
        message = payload.get("message")
        if not isinstance(message, str) or not message.strip():
            raise HTTPException(status_code=400, detail="message must be a non-empty string")

        try:
            session = bridge.ensure_session(session_id)
            session.client.send_text(message)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        def event_stream():
            try:
                while True:
                    event = session.client.read_event(timeout=600)
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                    if event.get("type") == "result":
                        break
            except Exception as exc:
                error_event = {"type": "error", "error": str(exc), "session_id": session_id}
                yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    @app.get("/settings")
    def read_settings(path: Optional[str] = None) -> Dict[str, Any]:
        if not path:
            raise HTTPException(status_code=400, detail="path is required")
        from pathlib import Path
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return {"ok": True, "path": str(p), "data": {}}
        if not p.is_file():
            raise HTTPException(status_code=400, detail="path is not a file")
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Failed to read settings: {exc}") from exc
        return {"ok": True, "path": str(p), "data": data}

    @app.post("/settings")
    def write_settings(payload: Dict[str, Any]) -> Dict[str, Any]:
        path = payload.get("path")
        data = payload.get("data")
        if not path:
            raise HTTPException(status_code=400, detail="path is required")
        if data is None:
            raise HTTPException(status_code=400, detail="data is required")
        from pathlib import Path
        p = Path(path).expanduser().resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        try:
            p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to write settings: {exc}") from exc
        return {"ok": True, "path": str(p)}

    return app
