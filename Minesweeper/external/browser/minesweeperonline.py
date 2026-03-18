from __future__ import annotations

import re

from minesweeper.external.browser.protocol import TilePayload
from minesweeper.domain.types import Coord


class MinesweeperOnlineParseError(ValueError):
    pass


_TILE_ID_RE = re.compile(r"^(?P<row>\d+)_(?P<col>\d+)$")
_FACE_CLASS_TO_STATE = {
    "facesmile": "in_progress",
    "facewin": "won",
    "facewon": "won",
    "facedead": "lost",
    "facelost": "lost",
}


def parse_tile_payload(tile_id: str, class_name: str) -> TilePayload:
    row, col = _parse_tile_id(tile_id)
    tokens = _class_tokens(class_name)
    if "square" not in tokens:
        raise MinesweeperOnlineParseError(f"unsupported tile class: {class_name!r}")

    tile_tokens = tokens - {"square"}
    if not tile_tokens or tile_tokens == {"blank"}:
        return TilePayload(x=col, y=row, state="hidden")

    if len(tile_tokens) != 1:
        raise MinesweeperOnlineParseError(f"unsupported tile class: {class_name!r}")

    token = next(iter(tile_tokens))
    if token.startswith("open"):
        return _parse_open_tile(row, col, token, class_name)
    if token == "bombflagged":
        return TilePayload(x=col, y=row, state="flagged")
    if token == "bombdeath":
        return TilePayload(x=col, y=row, state="exploded")
    if token == "bombrevealed":
        return TilePayload(x=col, y=row, state="mine_revealed")

    raise MinesweeperOnlineParseError(f"unsupported tile class: {class_name!r}")


def parse_face_state(class_name: str) -> str:
    tokens = _class_tokens(class_name)
    state_tokens = tokens - {"face"}
    if not state_tokens:
        return "in_progress"
    if len(state_tokens) != 1:
        raise MinesweeperOnlineParseError(f"unsupported face class: {class_name!r}")

    state_token = next(iter(state_tokens))
    state = _FACE_CLASS_TO_STATE.get(state_token)
    if state is None:
        raise MinesweeperOnlineParseError(f"unsupported face class: {class_name!r}")
    return state


def _parse_tile_id(tile_id: str) -> tuple[int, int]:
    match = _TILE_ID_RE.fullmatch(tile_id)
    if match is None:
        raise MinesweeperOnlineParseError(f"tile id must look like row_col: {tile_id!r}")
    return int(match.group("row")), int(match.group("col"))


def _parse_open_tile(row: int, col: int, token: str, class_name: str) -> TilePayload:
    match = re.fullmatch(r"open(?P<count>\d+)", token)
    if match is None:
        raise MinesweeperOnlineParseError(f"unsupported tile class: {class_name!r}")
    adjacent_mines = int(match.group("count"))
    if not 0 <= adjacent_mines <= 8:
        raise MinesweeperOnlineParseError(f"unsupported tile class: {class_name!r}")
    return TilePayload(x=col, y=row, state="revealed", adjacent_mines=adjacent_mines)


def _class_tokens(class_name: str) -> set[str]:
    tokens = {token for token in class_name.split() if token}
    if not tokens:
        raise MinesweeperOnlineParseError("class name must not be empty")
    return tokens
