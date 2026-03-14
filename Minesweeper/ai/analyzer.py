from dataclasses import dataclass, field
from typing import Mapping, Sequence

from minesweeper.domain.board import BoardView
from minesweeper.domain.types import Coord, TileState


@dataclass(frozen=True)
class AnalyzedBoard:
    UNKNOWN: int = -1
    FLAGGED: int = -2

    grid: Mapping[Coord, int] = field(default_factory=dict)
    frontier: Sequence[Coord] = field(default_factory=list)
    unknown_coords: frozenset[Coord] = field(default_factory=frozenset)
    flagged_coords: frozenset[Coord] = field(default_factory=frozenset)
    total_mines: int = 0


class Analyzer:
    def analyze(self, board: BoardView) -> AnalyzedBoard:
        grid: dict[Coord, int] = {}
        frontier: list[Coord] = []
        unknown_coords: set[Coord] = set()
        flagged_coords: set[Coord] = set()

        for x in range(board.width):
            for y in range(board.height):
                coord = Coord(x, y)
                tile = board.tile_at(coord)

                if tile.state == TileState.FLAGGED:
                    grid[coord] = AnalyzedBoard.FLAGGED
                    flagged_coords.add(coord)
                    continue

                if tile.state == TileState.HIDDEN:
                    grid[coord] = AnalyzedBoard.UNKNOWN
                    unknown_coords.add(coord)
                    continue

                grid[coord] = tile.adjacent_mines

        for x in range(board.width):
            for y in range(board.height):
                coord = Coord(x, y)
                value = grid[coord]
                if value <= 0:
                    continue

                if any(
                    neighbor in unknown_coords
                    for neighbor in coord.neighbors()
                ):
                    frontier.append(coord)

        return AnalyzedBoard(
            grid=grid,
            frontier=frontier,
            unknown_coords=frozenset(unknown_coords),
            flagged_coords=frozenset(flagged_coords),
            total_mines=board.num_mines,
        )
