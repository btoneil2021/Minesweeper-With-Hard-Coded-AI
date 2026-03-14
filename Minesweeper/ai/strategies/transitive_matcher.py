from dataclasses import dataclass
from typing import Optional

from minesweeper.ai.analyzer import AnalyzedBoard
from minesweeper.domain.move import Move
from minesweeper.domain.types import ActionType, Coord


@dataclass(frozen=True)
class _TileContext:
    value: int
    flags_around: int
    unknown_around: int

    @property
    def remaining_mines(self) -> int:
        return self.value - self.flags_around


class TransitiveMatcher:
    @property
    def name(self) -> str:
        return "TransitiveMatcher"

    def find_move(self, analysis: AnalyzedBoard) -> Optional[Move]:
        frontier = set(analysis.frontier)
        for coord in analysis.frontier:
            for neighbor in self._cardinal_neighbors(coord):
                if neighbor not in frontier:
                    continue

                move = self._check_pair(coord, neighbor, analysis)
                if move is not None:
                    return move

        return None

    def _check_pair(
        self,
        current: Coord,
        neighbor: Coord,
        analysis: AnalyzedBoard,
    ) -> Optional[Move]:
        current_ctx = self._tile_context(current, analysis)
        neighbor_ctx = self._tile_context(neighbor, analysis)
        possibilities = [
            candidate
            for candidate in neighbor.neighbors()
            if candidate in analysis.unknown_coords
        ]

        if self._matches_safe_pattern(neighbor_ctx, current_ctx):
            coord = self._directional_tile(current, neighbor, possibilities)
            if coord is not None:
                return Move(ActionType.REVEAL, coord)

        if self._matches_bomb_pattern(neighbor_ctx, current_ctx):
            coord = self._directional_tile(current, neighbor, possibilities)
            if coord is not None:
                return Move(ActionType.FLAG, coord)

        return None

    def _tile_context(self, coord: Coord, analysis: AnalyzedBoard) -> _TileContext:
        return _TileContext(
            value=analysis.grid[coord],
            flags_around=sum(candidate in analysis.flagged_coords for candidate in coord.neighbors()),
            unknown_around=sum(candidate in analysis.unknown_coords for candidate in coord.neighbors()),
        )

    def _matches_safe_pattern(self, neighbor: _TileContext, current: _TileContext) -> bool:
        return (
            neighbor.unknown_around == 3
            and current.unknown_around == 2
            and neighbor.remaining_mines == current.remaining_mines
            and neighbor.remaining_mines in {1, 2}
        )

    def _matches_bomb_pattern(self, neighbor: _TileContext, current: _TileContext) -> bool:
        return (
            neighbor.unknown_around == 3
            and neighbor.remaining_mines == 2
            and current.remaining_mines == 1
            and current.unknown_around in {2, 3}
        )

    def _directional_tile(
        self,
        current: Coord,
        neighbor: Coord,
        possibilities: list[Coord],
    ) -> Coord | None:
        direction_map = {
            (0, -1): (1, False),
            (-1, 0): (0, False),
            (1, 0): (0, True),
            (0, 1): (1, True),
        }
        direction = (neighbor.x - current.x, neighbor.y - current.y)
        if direction not in direction_map or not possibilities:
            return None

        coord_index, compare_max = direction_map[direction]
        fixed_index = 1 - coord_index
        fixed_values = {coord[fixed_index] for coord in possibilities}
        if len(fixed_values) != 1:
            return None

        key = (lambda coord: coord[coord_index])
        return max(possibilities, key=key) if compare_max else min(possibilities, key=key)

    def _cardinal_neighbors(self, coord: Coord) -> tuple[Coord, Coord, Coord, Coord]:
        return (
            Coord(coord.x, coord.y - 1),
            Coord(coord.x - 1, coord.y),
            Coord(coord.x + 1, coord.y),
            Coord(coord.x, coord.y + 1),
        )
