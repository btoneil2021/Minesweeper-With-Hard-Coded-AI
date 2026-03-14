from typing import Protocol

from minesweeper.domain.tile import Tile
from minesweeper.domain.types import Coord


class BoardView(Protocol):
    """Read-only view of the board."""

    @property
    def width(self) -> int: ...

    @property
    def height(self) -> int: ...

    @property
    def num_mines(self) -> int: ...

    def tile_at(self, coord: Coord) -> Tile: ...
