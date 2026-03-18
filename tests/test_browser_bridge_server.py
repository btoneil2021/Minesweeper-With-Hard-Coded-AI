import pytest

from minesweeper.external.browser.bridge.server import BrowserBridgeServer, BridgeError
from minesweeper.external.browser.protocol import (
    BoardSnapshotPayload,
    MoveCommandPayload,
    MovePayload,
    ProtocolError,
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


def test_bridge_stores_latest_snapshot_for_registered_session() -> None:
    server = BrowserBridgeServer()
    server.register_session("tab-123")

    server.receive_snapshot_message("tab-123", make_snapshot())

    assert server.latest_snapshot("tab-123") == BoardSnapshotPayload.from_dict(make_snapshot())


def test_bridge_records_outgoing_commands_for_registered_session() -> None:
    server = BrowserBridgeServer()
    server.register_session("tab-123")

    move_command = MoveCommandPayload(
        session_id="tab-123",
        moves=(MovePayload(x=1, y=0, action="reveal"),),
    )
    restart_command = RestartCommandPayload(session_id="tab-123", target="#face")

    server.queue_command("tab-123", move_command)
    server.queue_command("tab-123", restart_command)

    assert server.drain_commands("tab-123") == (move_command, restart_command)
    assert server.drain_commands("tab-123") == ()


def test_bridge_rejects_unknown_session_ids() -> None:
    server = BrowserBridgeServer()

    with pytest.raises(BridgeError, match="unknown session"):
        server.receive_snapshot_message("missing", make_snapshot())

    with pytest.raises(BridgeError, match="unknown session"):
        server.queue_command(
            "missing",
            MoveCommandPayload(
                session_id="missing",
                moves=(MovePayload(x=0, y=0, action="flag"),),
            ),
        )


def test_bridge_rejects_malformed_snapshot_messages() -> None:
    server = BrowserBridgeServer()
    server.register_session("tab-123")

    with pytest.raises(ProtocolError):
        server.receive_snapshot_message(
            "tab-123",
            {
                "type": "board_snapshot",
                "width": 2,
                "height": 2,
                "face_state": "smile",
                "tiles": [
                    {"x": 0, "y": 0, "state": "hidden"},
                    {"x": 1, "y": 0, "state": "bogus"},
                ],
            },
        )
