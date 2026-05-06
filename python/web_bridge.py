"""Session-oriented wrapper for integrating the CLI into Python web backends."""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional

try:
    from .free_code_cli_client import FreeCodeCliClient, JsonDict, PermissionHandler
except ImportError:
    from free_code_cli_client import FreeCodeCliClient, JsonDict, PermissionHandler


EventCallback = Callable[[JsonDict], None]


@dataclass
class WebBridgeSession:
    session_id: str
    cli_session_id: str
    client: FreeCodeCliClient


class FreeCodeWebBridge:
    """Keeps one CLI subprocess per web session."""

    def __init__(
        self,
        *,
        cli_path: Optional[str] = None,
        cwd: Optional[str] = None,
        extra_args: Optional[Iterable[str]] = None,
        env: Optional[Dict[str, str]] = None,
        auto_permission_handler: Optional[PermissionHandler] = None,
    ) -> None:
        self.cli_path = cli_path
        self.cwd = cwd
        self.extra_args = list(extra_args or [])
        self.env = dict(env or {})
        self.auto_permission_handler = auto_permission_handler
        self._sessions: Dict[str, WebBridgeSession] = {}
        self._lock = threading.Lock()

    def create_session(
        self,
        session_id: Optional[str] = None,
        cli_session_id: Optional[str] = None,
        settings_path: Optional[str] = None,
        cwd: Optional[str] = None,
    ) -> WebBridgeSession:
        session_id = session_id or str(uuid.uuid4())
        cli_session_id = cli_session_id or str(uuid.uuid4())
        extra = list(self.extra_args)
        if settings_path:
            from pathlib import Path
            expanded = str(Path(settings_path).expanduser().resolve())
            extra.extend(["--settings", expanded])
        from pathlib import Path
        raw_cwd = cwd or self.cwd
        effective_cwd = str(Path(raw_cwd).expanduser().resolve()) if raw_cwd else None
        client = FreeCodeCliClient(
            cli_path=self.cli_path,
            cwd=effective_cwd,
            extra_args=extra,
            env=self.env,
            session_id=cli_session_id,
            auto_permission_handler=self.auto_permission_handler,
            auto_start=True,
        )
        session = WebBridgeSession(
            session_id=session_id,
            cli_session_id=cli_session_id,
            client=client,
        )
        with self._lock:
            self._sessions[session_id] = session
        return session

    def list_sessions(self) -> list[WebBridgeSession]:
        with self._lock:
            return list(self._sessions.values())

    def get_session(self, session_id: str) -> WebBridgeSession:
        with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"Unknown CLI session: {session_id}")
        return session

    def ensure_session(
        self,
        session_id: str,
        *,
        cli_session_id: Optional[str] = None,
        settings_path: Optional[str] = None,
        cwd: Optional[str] = None,
    ) -> WebBridgeSession:
        with self._lock:
            session = self._sessions.get(session_id)
        if session is not None:
            return session
        return self.create_session(
            session_id=session_id,
            cli_session_id=cli_session_id,
            settings_path=settings_path,
            cwd=cwd,
        )

    def ask(
        self,
        session_id: str,
        text: str,
        *,
        timeout: Optional[float] = None,
        on_event: Optional[EventCallback] = None,
    ) -> List[JsonDict]:
        session = self.ensure_session(session_id)
        return session.client.ask(text, timeout=timeout, on_event=on_event)

    def send_text(
        self,
        session_id: str,
        text: str,
        *,
        priority: Optional[str] = None,
    ) -> str:
        session = self.ensure_session(session_id)
        return session.client.send_text(text, priority=priority)

    def collect_until_result(
        self,
        session_id: str,
        *,
        timeout: Optional[float] = None,
        on_event: Optional[EventCallback] = None,
    ) -> List[JsonDict]:
        session = self.ensure_session(session_id)
        return session.client.collect_until_result(timeout=timeout, on_event=on_event)

    def close_session(self, session_id: str) -> None:
        with self._lock:
            session = self._sessions.pop(session_id, None)
        if session is not None:
            session.client.close()

    def close_all(self) -> None:
        with self._lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()
        for session in sessions:
            session.client.close()
