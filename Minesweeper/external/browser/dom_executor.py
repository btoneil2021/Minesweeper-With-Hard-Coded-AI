from __future__ import annotations

from collections.abc import Callable, Sequence

from minesweeper.external.browser.protocol import (
    MoveCommandPayload,
    MovePayload,
    RestartCommandPayload,
)
from minesweeper.domain.move import Move
from minesweeper.domain.types import ActionType
from minesweeper.external.errors import ExecutionError


BrowserCommand = MoveCommandPayload | RestartCommandPayload


class DomMoveExecutor:
    def __init__(self, session_id: str, send: Callable[[BrowserCommand], None]) -> None:
        self._session_id = session_id
        self._send = send

    def execute(self, move: Move) -> None:
        self.execute_batch((move,))

    def execute_batch(self, moves: Sequence[Move]) -> None:
        payloads = tuple(self._move_payload(move) for move in moves)
        if not payloads:
            return
        self._send(MoveCommandPayload(session_id=self._session_id, moves=payloads))

    def restart(self) -> None:
        self._send(RestartCommandPayload(session_id=self._session_id, target="#face"))

    def _move_payload(self, move: Move) -> MovePayload:
        if move.action == ActionType.REVEAL:
            action = "reveal"
        elif move.action == ActionType.FLAG:
            action = "flag"
        else:
            raise ExecutionError("unsupported move type")

        return MovePayload(x=move.coord.x, y=move.coord.y, action=action)
