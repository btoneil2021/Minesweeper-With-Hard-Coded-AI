from __future__ import annotations

import json
import urllib.error
import urllib.request

import pytest

from minesweeper.external.browser.bridge.http_config import BridgeHttpConfig
from minesweeper.external.browser.bridge.http_server import BrowserHttpServer
from minesweeper.external.browser.bridge.server import BrowserBridgeServer
from minesweeper.external.browser.protocol import (
    BoardSnapshotPayload,
    MoveCommandPayload,
    MovePayload,
    RestartCommandPayload,
    TilePayload,
)


def make_snapshot() -> dict[str, object]:
    return {
        "type": "board_snapshot",
        "width": 2,
        "height": 2,
        "face_state": "smile",
        "tiles": [
            {"x": 0, "y": 0, "state": "hidden"},
            {"x": 1, "y": 0, "state": "revealed", "adjacent_mines": 1},
            {"x": 0, "y": 1, "state": "flagged"},
            {"x": 1, "y": 1, "state": "revealed", "adjacent_mines": 0},
        ],
    }


def make_server(bridge: BrowserBridgeServer | None = None) -> BrowserHttpServer:
    return BrowserHttpServer(
        bridge=bridge or BrowserBridgeServer(),
        config=BridgeHttpConfig(),
        port=0,
    )


def test_http_server_reports_health() -> None:
    server = make_server()
    server.start()
    try:
        with urllib.request.urlopen(f"{server.base_url}/health") as response:
            body = json.loads(response.read().decode("utf-8"))

        assert body == {"ok": True}
    finally:
        server.stop()


def test_http_server_allows_cors_preflight_for_snapshot_endpoint() -> None:
    bridge = BrowserBridgeServer()
    bridge.register_session("tab-123")
    server = make_server(bridge)
    server.start()
    try:
        request = urllib.request.Request(
            f"{server.base_url}/session/tab-123/snapshot",
            method="OPTIONS",
            headers={
                "Origin": "chrome-extension://example",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        with urllib.request.urlopen(request) as response:
            headers = response.headers
            body = response.read().decode("utf-8")

        assert response.status == 204
        assert body == ""
        assert headers["Access-Control-Allow-Origin"] == "*"
        assert "POST" in headers["Access-Control-Allow-Methods"]
        assert "Content-Type" in headers["Access-Control-Allow-Headers"]
    finally:
        server.stop()


def test_http_server_stores_snapshot_for_registered_session() -> None:
    bridge = BrowserBridgeServer()
    bridge.register_session("tab-123")
    server = make_server(bridge)
    server.start()
    try:
        request = urllib.request.Request(
            f"{server.base_url}/session/tab-123/snapshot",
            data=json.dumps(make_snapshot()).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request) as response:
            body = json.loads(response.read().decode("utf-8"))

        assert body == {"ok": True}
        assert bridge.latest_snapshot("tab-123") == BoardSnapshotPayload.from_dict(make_snapshot())
    finally:
        server.stop()


def test_http_server_drains_queued_commands_for_registered_session() -> None:
    bridge = BrowserBridgeServer()
    bridge.register_session("tab-123")
    bridge.queue_command(
        "tab-123",
        MoveCommandPayload(
            session_id="tab-123",
            moves=(MovePayload(x=1, y=0, action="reveal"),),
        ),
    )
    bridge.queue_command("tab-123", RestartCommandPayload(session_id="tab-123", target="#face"))
    server = make_server(bridge)
    server.start()
    try:
        with urllib.request.urlopen(f"{server.base_url}/session/tab-123/commands") as response:
            body = json.loads(response.read().decode("utf-8"))

        assert body == {
            "commands": [
                {
                    "type": "execute_moves",
                    "session_id": "tab-123",
                    "moves": [{"x": 1, "y": 0, "action": "reveal"}],
                },
                {"type": "restart", "session_id": "tab-123", "target": "#face"},
            ]
        }
        assert bridge.drain_commands("tab-123") == ()
    finally:
        server.stop()


def test_http_server_rejects_malformed_snapshot_payloads() -> None:
    bridge = BrowserBridgeServer()
    bridge.register_session("tab-123")
    server = make_server(bridge)
    server.start()
    try:
        request = urllib.request.Request(
            f"{server.base_url}/session/tab-123/snapshot",
            data=b"{not-json",
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with pytest.raises(urllib.error.HTTPError) as excinfo:
            urllib.request.urlopen(request)

        assert excinfo.value.code == 400
        assert "malformed" in excinfo.value.read().decode("utf-8")
    finally:
        server.stop()


def test_http_server_rejects_unknown_sessions() -> None:
    server = make_server()
    server.start()
    try:
        with pytest.raises(urllib.error.HTTPError) as snapshot_excinfo:
            urllib.request.urlopen(f"{server.base_url}/session/missing/snapshot")

        with pytest.raises(urllib.error.HTTPError) as commands_excinfo:
            urllib.request.urlopen(f"{server.base_url}/session/missing/commands")

        assert snapshot_excinfo.value.code == 404
        assert commands_excinfo.value.code == 404
    finally:
        server.stop()
