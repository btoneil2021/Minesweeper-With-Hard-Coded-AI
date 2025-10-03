from typing import Optional, List, Tuple
from constants import *
from .transitive_pattern_matcher import TransitivePatternMatcher


class PatternDetector:
    """Detects common minesweeper patterns for making logical deductions"""

    def __init__(self, board_analyzer):
        self.analyzer = board_analyzer
        self.transitive_matcher = TransitivePatternMatcher(board_analyzer)

    def _count_neighbors_by_states(self, tile_coord: Tuple[int, int],
                                   target_states: List[int]) -> int:
        """Count neighbors matching any of the target states"""
        count = 0

        for neighbor in self.analyzer.get_neighbors(tile_coord):
            if not self.analyzer.has_tile(neighbor):
                continue

            if self.analyzer.get_tile_state(neighbor) in target_states:
                count += 1

        return count

    def _get_neighbors_by_state(self, tile_coord: Tuple[int, int],
                                target_state: int) -> List[Tuple[int, int]]:
        """Get all neighbors matching the target state"""
        matching_neighbors = []

        for neighbor in self.analyzer.get_neighbors(tile_coord):
            if not self.analyzer.has_tile(neighbor):
                continue

            if self.analyzer.get_tile_state(neighbor) == target_state:
                matching_neighbors.append(neighbor)

        return matching_neighbors

    def same_bombs_as_squares(self, tile_coord: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
        """
        Detects when the number of unknown squares equals the tile value
        This means all unknown squares must be bombs
        """
        if not self.analyzer.has_tile(tile_coord):
            return None

        tile_value = self.analyzer.get_tile_state(tile_coord)
        unknown_or_flagged_count = self._count_neighbors_by_states(tile_coord, [AI_FLAGGED, AI_UNKNOWN])

        if unknown_or_flagged_count == tile_value:
            return self._get_neighbors_by_state(tile_coord, AI_UNKNOWN)

        return None

    def all_bombs_found(self, tile_coord: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
        """
        Detects when all bombs around a tile are flagged
        This means all remaining unknown squares are safe
        """
        if not self.analyzer.has_tile(tile_coord):
            return None

        tile_value = self.analyzer.get_tile_state(tile_coord)
        flags_around = self._count_neighbors_by_states(tile_coord, [AI_FLAGGED])

        if flags_around == tile_value:
            unknown_neighbors = self._get_neighbors_by_state(tile_coord, AI_UNKNOWN)
            if unknown_neighbors:
                return unknown_neighbors

        return None

    def transitive_bomb_property(self, tile_coord: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        Advanced pattern detection using transitive properties between adjacent tiles
        Returns tile coordinates to reveal or flag (negative coordinates indicate flag)
        """
        return self.transitive_matcher.find_transitive_move(tile_coord)
