from typing import Optional, List, Tuple
from dataclasses import dataclass
from constants import *


class TransitivePatternMatcher:
    """
    Handles complex transitive pattern matching for minesweeper AI
    Detects bombs and safe tiles by analyzing relationships between adjacent tiles
    """

    @dataclass(frozen=True)
    class TileContext:
        """Encapsulates all relevant context about a tile for pattern matching"""
        value: int
        flags_around: int
        unknown_around: int

        @property
        def remaining_mines(self) -> int:
            """Number of mines still needed to satisfy this tile's constraint"""
            return self.value - self.flags_around

    def __init__(self, board_analyzer):
        self.analyzer = board_analyzer

    def find_transitive_move(self, tile_coord: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        Advanced pattern detection using transitive properties between adjacent tiles
        Returns tile coordinates to reveal or flag (negative coordinates indicate flag)
        """
        if not self.analyzer.has_tile(tile_coord) \
            or not self._has_unknown_cardinal_neighbor(tile_coord):
            return None

        for neighbor in self.analyzer.get_cardinal_neighbors(tile_coord):
            if (result := self._check_neighbor_pattern(tile_coord, neighbor)) is not None:
                return result

        return None

    def _has_unknown_cardinal_neighbor(self, tile_coord: Tuple[int, int]) -> bool:
        """Check if there are any unknown cardinal neighbors"""
        for neighbor in self.analyzer.get_cardinal_neighbors(tile_coord):
            if not self.analyzer.has_tile(neighbor):
                continue

            if self.analyzer.get_tile_state(neighbor) < -1:
                return True

        return False

    def _get_tile_context(self, tile_coord: Tuple[int, int]) -> 'TransitivePatternMatcher.TileContext':
        """Gather all context for a tile"""
        return self.TileContext(
            value=self.analyzer.get_tile_state(tile_coord),
            flags_around=self.analyzer.count_neighbors_by_states(tile_coord, [AI_FLAGGED]),
            unknown_around=self.analyzer.count_neighbors_by_states(tile_coord, [AI_UNKNOWN])
        )

    def _check_neighbor_pattern(self, tile_coord: Tuple[int, int],
                                neighbor_coord: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        Check pattern between current tile and one neighbor
        Analyzes the relationship to find safe/bomb tiles using transitive properties
        """
        # Early validation - skip invalid or flagged/unknown neighbors
        if not self.analyzer.has_tile(neighbor_coord) \
            or self.analyzer.get_tile_state(neighbor_coord) in [AI_UNKNOWN, AI_FLAGGED]:
            return None

        # Gather tile contexts
        current_ctx = self._get_tile_context(tile_coord)
        neighbor_ctx = self._get_tile_context(neighbor_coord)
        possibilities = self.analyzer.get_neighbors_by_state(neighbor_coord, AI_UNKNOWN)

        if self._matches_safe_pattern(neighbor_ctx, current_ctx):
            return self._get_directional_tile(tile_coord, neighbor_coord, possibilities, safe=True)
        elif self._matches_bomb_pattern(neighbor_ctx, current_ctx):
            return self._get_directional_tile(tile_coord, neighbor_coord, possibilities, safe=False)
        else:
            return None

    def _matches_safe_pattern(self, neighbor: 'TransitivePatternMatcher.TileContext',
                              current: 'TransitivePatternMatcher.TileContext') -> bool:
        """
        Detect safe tile patterns based on transitive properties
        Returns True if the pattern indicates a safe tile
        """
        return (neighbor.unknown_around == 3 and
            current.unknown_around == 2 and
            neighbor.remaining_mines == current.remaining_mines and
            neighbor.remaining_mines in [1, 2])

    def _matches_bomb_pattern(self, neighbor: 'TransitivePatternMatcher.TileContext',
                              current: 'TransitivePatternMatcher.TileContext') -> bool:
        """
        Detect bomb tile patterns based on transitive properties
        Returns True if the pattern indicates a bomb tile
        """
        return (neighbor.unknown_around == 3 and 
                neighbor.remaining_mines == 2 and
                current.remaining_mines == 1 and 
                current.unknown_around in [2, 3])

    def _get_directional_tile(self, tile_coord: Tuple[int, int], neighbor_coord: Tuple[int, int],
                             possibilities: List[Tuple[int, int]], safe: bool = True) -> Optional[Tuple[int, int]]:
        """Get the appropriate tile based on direction and pattern type"""
        direction = (neighbor_coord[0] - tile_coord[0], 
                     neighbor_coord[1] - tile_coord[1])
        direction_map = {
                    (0, -1): (1, False),

        (-1, 0): (0, False),    (1, 0): (0, True),

                      (0, 1): (1, True)
        }

        if direction not in direction_map \
            or not possibilities:
            return None

        coord_index, compare_max = direction_map[direction]
        result = self._find_extreme_tile(possibilities, coord_index, compare_max)

        # Return negative coordinates to indicate flagging
        return result if result is None else \
            ((-result[0], -result[1]) if not safe else result)

    def _find_extreme_tile(self, possibilities: List[Tuple[int, int]], coord_index: int,
                          compare_max: bool) -> Optional[Tuple[int, int]]:
        """
        Find the extreme tile (min or max) along a specific axis
        coord_index: 0 for x-axis, 1 for y-axis
        compare_max: True to find max, False to find min
        """
        fixed_index = 1 - coord_index
        fixed_coord = possibilities[0][fixed_index]

        # Verify all possibilities have the same fixed coordinate
        for pos in possibilities:
            if pos[fixed_index] != fixed_coord:
                return None

        return max(possibilities, key=lambda p: p[coord_index]) if compare_max \
            else min(possibilities, key=lambda p: p[coord_index])
