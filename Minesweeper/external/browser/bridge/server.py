from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from minesweeper.external.browser.protocol import (
    BoardSnapshotPayload,
    MoveCommandPayload,
    ProtocolError,
    RestartCommandPayload,
)


class BridgeError(RuntimeError):
    pass


@dataclass
class _SessionState:
    latest_snapshot: BoardSnapshotPayload | None = None
    outgoing_commands: list[MoveCommandPayload | RestartCommandPayload] = field(default_factory=list)


class BrowserBridgeServer:
    def __init__(self) -> None:
        self._sessions: dict[str, _SessionState] = {}

    def register_session(self, session_id: str) -> None:
        if session_id in self._sessions:
            raise BridgeError(f"session already registered: {session_id}")
        self._sessions[session_id] = _SessionState()

    def receive_snapshot_message(self, session_id: str, message: dict[str, Any]) -> None:
        session = self._require_session(session_id)
        snapshot = BoardSnapshotPayload.from_dict(self._require_dict(message))
        session.latest_snapshot = snapshot

    def latest_snapshot(self, session_id: str) -> BoardSnapshotPayload:
        session = self._require_session(session_id)
        if session.latest_snapshot is None:
            raise BridgeError(f"no snapshot available for session: {session_id}")
        return session.latest_snapshot

    def queue_command(self, session_id: str, command: MoveCommandPayload | RestartCommandPayload) -> None:
        session = self._require_session(session_id)
        if command.session_id != session_id:
            raise BridgeError(
                f"command session mismatch: expected {session_id!r}, got {command.session_id!r}"
            )
        session.outgoing_commands.append(command)

    def drain_commands(self, session_id: str) -> tuple[MoveCommandPayload | RestartCommandPayload, ...]:
        session = self._require_session(session_id)
        commands = tuple(session.outgoing_commands)
        session.outgoing_commands.clear()
        return commands

    def _require_session(self, session_id: str) -> _SessionState:
        session = self._sessions.get(session_id)
        if session is None:
            raise BridgeError(f"unknown session: {session_id}")
        return session

    def _require_dict(self, message: Any) -> dict[str, Any]:
        if not isinstance(message, dict):
            raise ProtocolError("bridge message must be an object")
        return message
