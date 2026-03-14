from dataclasses import dataclass
import random

from minesweeper.domain.tile import Tile
from minesweeper.domain.types import Coord, GameConfig, TileState


@dataclass
class _Cell:
    coord: Coord
    state: TileState
    is_mine: bool
    adjacent_mines: int = 0


class Board:
    """Concrete board implementation."""

    def __init__(self, config: GameConfig, rng: random.Random | None = None) -> None:
        self._width = config.width
        self._height = config.height
        self._num_mines = config.num_mines
        self._cells: dict[Coord, _Cell] = {}
        generator = rng or random.Random()

        mine_coords = set(
            generator.sample(
                [Coord(x, y) for x in range(self._width) for y in range(self._height)],
                self._num_mines,
            )
        )

        for x in range(self._width):
            for y in range(self._height):
                coord = Coord(x, y)
                self._cells[coord] = _Cell(
                    coord=coord,
                    state=TileState.HIDDEN,
                    is_mine=coord in mine_coords,
                    adjacent_mines=self._adjacent_mine_count(coord, mine_coords),
                )

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def num_mines(self) -> int:
        return self._num_mines

    def tile_at(self, coord: Coord) -> Tile:
        cell = self._cells[coord]
        return Tile(
            coord=cell.coord,
            state=cell.state,
            is_mine=cell.is_mine,
            adjacent_mines=cell.adjacent_mines,
        )

    def set_state(self, coord: Coord, state: TileState) -> None:
        self._cells[coord].state = state

    def relocate_mine(self, coord: Coord) -> None:
        source = self._cells[coord]
        if not source.is_mine:
            return

        for target_coord, target in self._cells.items():
            if target_coord != coord and not target.is_mine:
                source.is_mine = False
                target.is_mine = True
                self._recompute_adjacent_counts()
                return

    def _recompute_adjacent_counts(self) -> None:
        mine_coords = {
            coord
            for coord, cell in self._cells.items()
            if cell.is_mine
        }
        for coord, cell in self._cells.items():
            cell.adjacent_mines = self._adjacent_mine_count(coord, mine_coords)

    def _adjacent_mine_count(self, coord: Coord, mine_coords: set[Coord]) -> int:
        if coord in mine_coords:
            return 0

        return sum(neighbor in mine_coords for neighbor in coord.neighbors())
