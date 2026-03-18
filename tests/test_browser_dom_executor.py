import pytest

from minesweeper.external.browser.dom_executor import DomMoveExecutor
from minesweeper.external.browser.protocol import (
    MoveCommandPayload,
    MovePayload,
    RestartCommandPayload,
)
from minesweeper.domain.move import Move
from minesweeper.domain.types import ActionType, Coord
from minesweeper.external.errors import ExecutionError


def test_execute_batch_maps_reveal_to_left_click_command_payload() -> None:
    sent: list[object] = []
    executor = DomMoveExecutor(session_id="tab-123", send=sent.append)

    executor.execute_batch([Move(ActionType.REVEAL, Coord(2, 3))])

    assert sent == [
        MoveCommandPayload(
            session_id="tab-123",
            moves=(MovePayload(x=2, y=3, action="reveal"),),
        )
    ]


def test_execute_batch_maps_flag_to_right_click_command_payload() -> None:
    sent: list[object] = []
    executor = DomMoveExecutor(session_id="tab-123", send=sent.append)

    executor.execute_batch([Move(ActionType.FLAG, Coord(4, 5))])

    assert sent == [
        MoveCommandPayload(
            session_id="tab-123",
            moves=(MovePayload(x=4, y=5, action="flag"),),
        )
    ]


def test_restart_emits_restart_command_payload() -> None:
    sent: list[object] = []
    executor = DomMoveExecutor(session_id="tab-123", send=sent.append)

    executor.restart()

    assert sent == [RestartCommandPayload(session_id="tab-123", target="#face")]


def test_execute_batch_rejects_unsupported_action_types() -> None:
    executor = DomMoveExecutor(session_id="tab-123", send=lambda _command: None)

    with pytest.raises(ExecutionError, match="unsupported move type"):
        executor.execute_batch([Move(ActionType.UNFLAG, Coord(0, 0))])
