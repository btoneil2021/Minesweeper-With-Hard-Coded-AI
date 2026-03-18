from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ProtocolError(ValueError):
    pass


_BOARD_SNAPSHOT_TYPE = "board_snapshot"
_EXECUTE_MOVES_TYPE = "execute_moves"
_RESTART_TYPE = "restart"
_ALLOWED_TILE_STATES = {"hidden", "revealed", "flagged", "exploded", "mine_revealed"}
_ALLOWED_MOVE_ACTIONS = {"reveal", "flag"}


@dataclass(frozen=True)
class TilePayload:
    x: int
    y: int
    state: str
    adjacent_mines: int | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"x": self.x, "y": self.y, "state": self.state}
        if self.adjacent_mines is not None:
            payload["adjacent_mines"] = self.adjacent_mines
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TilePayload":
        x = _require_int(payload, "x")
        y = _require_int(payload, "y")
        state = _require_str(payload, "state")
        if state not in _ALLOWED_TILE_STATES:
            raise ProtocolError(f"unsupported tile state: {state}")
        adjacent_mines = payload.get("adjacent_mines")
        if adjacent_mines is not None:
            adjacent_mines = _require_int(payload, "adjacent_mines")
        elif state == "revealed":
            adjacent_mines = 0
        return cls(x=x, y=y, state=state, adjacent_mines=adjacent_mines)


@dataclass(frozen=True)
class BoardSnapshotPayload:
    width: int
    height: int
    face_state: str
    tiles: tuple[TilePayload, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": _BOARD_SNAPSHOT_TYPE,
            "width": self.width,
            "height": self.height,
            "face_state": self.face_state,
            "tiles": [tile.to_dict() for tile in self.tiles],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BoardSnapshotPayload":
        _require_type(payload, _BOARD_SNAPSHOT_TYPE)
        width = _require_int(payload, "width")
        height = _require_int(payload, "height")
        face_state = _require_str(payload, "face_state")
        tiles_value = payload.get("tiles")
        if not isinstance(tiles_value, list):
            raise ProtocolError("tiles must be a list")
        tiles: list[TilePayload] = []
        seen_coords: set[tuple[int, int]] = set()
        for tile_value in tiles_value:
            tile = _require_tile_payload(tile_value)
            if not (0 <= tile.x < width and 0 <= tile.y < height):
                raise ProtocolError(f"tile coord out of bounds: ({tile.x}, {tile.y})")
            coord = (tile.x, tile.y)
            if coord in seen_coords:
                raise ProtocolError(f"duplicate tile coord: ({tile.x}, {tile.y})")
            seen_coords.add(coord)
            tiles.append(tile)
        return cls(width=width, height=height, face_state=face_state, tiles=tuple(tiles))


@dataclass(frozen=True)
class MovePayload:
    x: int
    y: int
    action: str

    def to_dict(self) -> dict[str, Any]:
        return {"x": self.x, "y": self.y, "action": self.action}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MovePayload":
        x = _require_int(payload, "x")
        y = _require_int(payload, "y")
        action = _require_str(payload, "action")
        if action not in _ALLOWED_MOVE_ACTIONS:
            raise ProtocolError(f"unsupported move action: {action}")
        return cls(x=x, y=y, action=action)


@dataclass(frozen=True)
class MoveCommandPayload:
    session_id: str
    moves: tuple[MovePayload, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": _EXECUTE_MOVES_TYPE,
            "session_id": self.session_id,
            "moves": [move.to_dict() for move in self.moves],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MoveCommandPayload":
        _require_type(payload, _EXECUTE_MOVES_TYPE)
        session_id = _require_str(payload, "session_id")
        moves_value = payload.get("moves")
        if not isinstance(moves_value, list):
            raise ProtocolError("moves must be a list")
        moves = tuple(_require_move_payload(move) for move in moves_value)
        return cls(session_id=session_id, moves=moves)


@dataclass(frozen=True)
class RestartCommandPayload:
    session_id: str
    target: str = "#face"

    def to_dict(self) -> dict[str, Any]:
        return {"type": _RESTART_TYPE, "session_id": self.session_id, "target": self.target}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RestartCommandPayload":
        _require_type(payload, _RESTART_TYPE)
        session_id = _require_str(payload, "session_id")
        target = _require_str(payload, "target")
        if target != "#face":
            raise ProtocolError(f"unsupported restart target: {target}")
        return cls(session_id=session_id, target=target)


def _require_type(payload: dict[str, Any], expected: str) -> None:
    actual = payload.get("type")
    if actual != expected:
        raise ProtocolError(f"expected type {expected!r}, got {actual!r}")


def _require_int(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ProtocolError(f"{key} must be an int")
    return value


def _require_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ProtocolError(f"{key} must be a string")
    return value


def _require_tile_payload(payload: Any) -> TilePayload:
    if not isinstance(payload, dict):
        raise ProtocolError("tile payload must be an object")
    return TilePayload.from_dict(payload)


def _require_move_payload(payload: Any) -> MovePayload:
    if not isinstance(payload, dict):
        raise ProtocolError("move payload must be an object")
    return MovePayload.from_dict(payload)
