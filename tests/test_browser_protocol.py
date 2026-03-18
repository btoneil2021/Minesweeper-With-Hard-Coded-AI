import pytest

from minesweeper.external.browser.protocol import (
    BoardSnapshotPayload,
    MoveCommandPayload,
    MovePayload,
    ProtocolError,
    RestartCommandPayload,
    TilePayload,
)


def test_board_snapshot_payload_round_trips_through_dict() -> None:
    payload = BoardSnapshotPayload(
        width=30,
        height=16,
        face_state="smile",
        tiles=(
            TilePayload(x=0, y=0, state="hidden"),
            TilePayload(x=1, y=0, state="revealed", adjacent_mines=1),
            TilePayload(x=2, y=0, state="flagged"),
        ),
    )

    data = payload.to_dict()

    assert data == {
        "type": "board_snapshot",
        "width": 30,
        "height": 16,
        "face_state": "smile",
        "tiles": [
            {"x": 0, "y": 0, "state": "hidden"},
            {"x": 1, "y": 0, "state": "revealed", "adjacent_mines": 1},
            {"x": 2, "y": 0, "state": "flagged"},
        ],
    }
    assert BoardSnapshotPayload.from_dict(data) == payload


def test_move_command_payload_round_trips_through_dict() -> None:
    payload = MoveCommandPayload(
        session_id="tab-123",
        moves=(
            MovePayload(x=3, y=4, action="reveal"),
            MovePayload(x=8, y=7, action="flag"),
        ),
    )

    data = payload.to_dict()

    assert data == {
        "type": "execute_moves",
        "session_id": "tab-123",
        "moves": [
            {"x": 3, "y": 4, "action": "reveal"},
            {"x": 8, "y": 7, "action": "flag"},
        ],
    }
    assert MoveCommandPayload.from_dict(data) == payload


def test_restart_command_payload_round_trips_through_dict() -> None:
    payload = RestartCommandPayload(session_id="tab-123", target="#face")

    data = payload.to_dict()

    assert data == {"type": "restart", "session_id": "tab-123", "target": "#face"}
    assert RestartCommandPayload.from_dict(data) == payload


def test_invalid_payloads_are_rejected() -> None:
    with pytest.raises(ProtocolError):
        BoardSnapshotPayload.from_dict(
            {
                "type": "board_snapshot",
                "width": 30,
                "height": 16,
                "face_state": "smile",
                "tiles": [{"x": 0, "y": 0, "state": "bogus"}],
            }
        )

    with pytest.raises(ProtocolError):
        MoveCommandPayload.from_dict(
            {
                "type": "execute_moves",
                "session_id": "tab-123",
                "moves": [{"x": 3, "y": 4, "action": "bogus"}],
            }
        )

    with pytest.raises(ProtocolError):
        RestartCommandPayload.from_dict({"type": "restart"})

    with pytest.raises(ProtocolError):
        RestartCommandPayload.from_dict(
            {"type": "restart", "session_id": "tab-123", "target": "#menu"}
        )


def test_board_snapshot_payload_rejects_duplicate_tile_coords() -> None:
    with pytest.raises(ProtocolError, match="duplicate tile coord"):
        BoardSnapshotPayload.from_dict(
            {
                "type": "board_snapshot",
                "width": 3,
                "height": 2,
                "face_state": "smile",
                "tiles": [
                    {"x": 0, "y": 0, "state": "hidden"},
                    {"x": 0, "y": 0, "state": "revealed", "adjacent_mines": 1},
                ],
            }
        )


def test_board_snapshot_payload_rejects_out_of_bounds_tile_coords() -> None:
    with pytest.raises(ProtocolError, match="out of bounds"):
        BoardSnapshotPayload.from_dict(
            {
                "type": "board_snapshot",
                "width": 3,
                "height": 2,
                "face_state": "smile",
                "tiles": [
                    {"x": 0, "y": 0, "state": "hidden"},
                    {"x": 3, "y": 1, "state": "revealed", "adjacent_mines": 1},
                ],
            }
        )
