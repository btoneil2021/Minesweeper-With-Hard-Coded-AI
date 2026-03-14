from typing import NamedTuple

from minesweeper.domain.types import ActionType, Coord


class Move(NamedTuple):
    """A single game action: what to do and where."""

    action: ActionType
    coord: Coord
