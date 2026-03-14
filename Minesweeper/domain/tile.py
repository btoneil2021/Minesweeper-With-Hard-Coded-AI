from typing import NamedTuple

from minesweeper.domain.types import Coord, TileState


class Tile(NamedTuple):
    """
    Immutable snapshot of a single cell.

    `adjacent_mines` is the number displayed when revealed (0-8).
    For mines, this value is meaningless.
    """

    coord: Coord
    state: TileState
    is_mine: bool
    adjacent_mines: int = 0
