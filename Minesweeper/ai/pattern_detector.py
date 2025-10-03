from typing import Optional, List, Tuple
from constants import *
from .transitive_pattern_matcher import TransitivePatternMatcher


class PatternDetector:
    """Detects common minesweeper patterns for making logical deductions"""

    def __init__(self, board_analyzer):
        self.analyzer = board_analyzer
        self.transitive_matcher = TransitivePatternMatcher(board_analyzer)

    def _get_tile_value_if_valid(self, tile_coord: Tuple[int, int]) -> Optional[int]:
        """Returns tile value if tile exists, None otherwise"""
        if not self.analyzer.has_tile(tile_coord):
            return None
        return self.analyzer.get_tile_state(tile_coord)

    def same_bombs_as_squares(self, tile_coord: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
        """
        Detects when the number of unknown squares equals the tile value
        This means all unknown squares must be bombs
        """
        unknown_or_flagged_count = self.analyzer.count_neighbors_by_states(tile_coord, [AI_FLAGGED, AI_UNKNOWN])
        if (tile_value := self._get_tile_value_if_valid(tile_coord)) is None \
            or unknown_or_flagged_count != tile_value:
            return None

        return self.analyzer.get_neighbors_by_state(tile_coord, AI_UNKNOWN)

    def all_bombs_found(self, tile_coord: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
        """
        Detects when all bombs around a tile are flagged
        This means all remaining unknown squares are safe
        """

        flags_around = self.analyzer.count_neighbors_by_states(tile_coord, [AI_FLAGGED])
        if (tile_value := self._get_tile_value_if_valid(tile_coord)) is None \
            or flags_around != tile_value:
            return None

        unknown_neighbors = self.analyzer.get_neighbors_by_state(tile_coord, AI_UNKNOWN)
        if unknown_neighbors:
            return unknown_neighbors

    def transitive_bomb_property(self, tile_coord: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        Advanced pattern detection using transitive properties between adjacent tiles
        Returns tile coordinates to reveal or flag (negative coordinates indicate flag)
        """
        return self.transitive_matcher.find_transitive_move(tile_coord)
