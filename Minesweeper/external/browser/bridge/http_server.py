from __future__ import annotations

import json
import threading
from collections.abc import Callable
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from minesweeper.external.browser.bridge.http_config import BridgeHttpConfig
from minesweeper.external.browser.bridge.server import BrowserBridgeServer, BridgeError
from minesweeper.external.browser.protocol import (
    BoardSnapshotPayload,
    MoveCommandPayload,
    ProtocolError,
    RestartCommandPayload,
)


class _BridgeThreadingHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class BrowserHttpServer:
    def __init__(
        self,
        bridge: BrowserBridgeServer,
        config: BridgeHttpConfig | None = None,
        port: int | None = None,
    ) -> None:
        self._bridge = bridge
        self._config = config or BridgeHttpConfig()
        self._requested_port = self._config.port if port is None else port
        self._server: _BridgeThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def host(self) -> str:
        return self._config.host

    @property
    def port(self) -> int:
        if self._server is None:
            return self._requested_port
        return int(self._server.server_address[1])

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def start(self) -> None:
        if self._server is not None:
            return

        handler_factory = self._make_handler_factory()
        self._server = _BridgeThreadingHTTPServer((self._config.host, self._requested_port), handler_factory)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server is None:
            return

        self._server.shutdown()
        self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        self._server = None
        self._thread = None

    def _make_handler_factory(self) -> Callable[..., _BridgeRequestHandler]:
        bridge = self._bridge

        class BridgeRequestHandler(_BridgeRequestHandler):
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                super().__init__(*args, bridge=bridge, **kwargs)

        return BridgeRequestHandler


class _BridgeRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args: Any, bridge: BrowserBridgeServer, **kwargs: Any) -> None:
        self._bridge = bridge
        super().__init__(*args, **kwargs)

    def do_OPTIONS(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._send_json(HTTPStatus.NO_CONTENT, {})
            return

        session_id, action = self._parse_session_path(parsed.path)
        if session_id is None or action not in {"snapshot", "commands"}:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return

        self._send_json(HTTPStatus.NO_CONTENT, {})

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._send_json(HTTPStatus.OK, {"ok": True})
            return

        session_id, action = self._parse_session_path(parsed.path)
        if session_id is None:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return

        try:
            if action == "commands":
                commands = self._bridge.drain_commands(session_id)
                self._send_json(
                    HTTPStatus.OK,
                    {"commands": [command.to_dict() for command in commands]},
                )
                return
            if action == "snapshot":
                self._bridge.latest_snapshot(session_id)
                self._send_json(HTTPStatus.METHOD_NOT_ALLOWED, {"error": "method not allowed"})
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
        except BridgeError as exc:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": str(exc)})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        session_id, action = self._parse_session_path(parsed.path)
        if session_id is None or action != "snapshot":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return

        try:
            payload = self._read_json_body()
            self._bridge.receive_snapshot_message(session_id, payload)
        except BridgeError as exc:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": str(exc)})
            return
        except (json.JSONDecodeError, UnicodeDecodeError, ProtocolError, ValueError) as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": f"malformed snapshot: {exc}"})
            return

        self._send_json(HTTPStatus.OK, {"ok": True})

    def log_message(self, *_args: Any, **_kwargs: Any) -> None:
        return

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ProtocolError("body must be a JSON object")
        return payload

    def _parse_session_path(self, path: str) -> tuple[str | None, str | None]:
        parts = [part for part in path.split("/") if part]
        if len(parts) != 3 or parts[0] != "session":
            return None, None
        return parts[1], parts[2]

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = b""
        if payload:
            body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)
