from typing import Optional, List, Tuple
from constants import *


class TransitivePatternMatcher:
    """
    Handles complex transitive pattern matching for minesweeper AI
    Detects bombs and safe tiles by analyzing relationships between adjacent tiles
    """

    def __init__(self, board_analyzer):
        self.analyzer = board_analyzer

    def find_transitive_move(self, key: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        Advanced pattern detection using transitive properties between adjacent tiles
        Returns tile coordinates to reveal or flag (negative coordinates indicate flag)
        """
        if not self.analyzer.has_tile(key):
            return None

        if not self._has_unknown_cardinal_neighbor(key):
            return None

        tile_value = self.analyzer.get_tile_state(key)
        flags_around = self._count_neighbors_by_states(key, [AI_FLAGGED])
        unknown_count = self._count_neighbors_by_states(key, [AI_UNKNOWN])

        # Check each cardinal direction for pattern matches
        for neighbor in self.analyzer.get_cardinal_neighbors(key):
            if not self.analyzer.has_tile(neighbor):
                continue
            if self.analyzer.get_tile_state(neighbor) in [AI_UNKNOWN, AI_FLAGGED]:
                continue

            adjacent_tile_value = self.analyzer.get_tile_state(neighbor)
            flags_around_adjacent = self._count_neighbors_by_states(neighbor, [AI_FLAGGED])
            unknown_around_adjacent = self._count_neighbors_by_states(neighbor, [AI_UNKNOWN])
            possibilities = self._get_neighbors_by_state(neighbor, AI_UNKNOWN)

            # Pattern matching conditions
            result = self._check_pattern_conditions(
                key, neighbor, possibilities,
                unknown_around_adjacent, adjacent_tile_value,
                flags_around_adjacent, tile_value, flags_around, unknown_count
            )
            if result is not None:
                return result

        return None

    def _has_unknown_cardinal_neighbor(self, key: Tuple[int, int]) -> bool:
        """Check if there are any unknown cardinal neighbors"""
        for neighbor in self.analyzer.get_cardinal_neighbors(key):
            if self.analyzer.has_tile(neighbor):
                if self.analyzer.get_tile_state(neighbor) < -1:
                    return True
        return False

    def _count_neighbors_by_states(self, key: Tuple[int, int],
                                   target_states: List[int]) -> int:
        """Count neighbors matching any of the target states"""
        count = 0
        for neighbor in self.analyzer.get_neighbors(key):
            if self.analyzer.has_tile(neighbor):
                if self.analyzer.get_tile_state(neighbor) in target_states:
                    count += 1
        return count

    def _get_neighbors_by_state(self, key: Tuple[int, int],
                                target_state: int) -> List[Tuple[int, int]]:
        """Get all neighbors matching the target state"""
        matching_neighbors = []
        for neighbor in self.analyzer.get_neighbors(key):
            if self.analyzer.has_tile(neighbor):
                if self.analyzer.get_tile_state(neighbor) == target_state:
                    matching_neighbors.append(neighbor)
        return matching_neighbors

    def _check_pattern_conditions(self, tile_coord: Tuple[int, int], neighbor: Tuple[int, int],
                                  possibilities: List[Tuple[int, int]],
                                  unknown_adjacent: int, adjacent_value: int, flags_adjacent: int,
                                  tile_value: int, flags_current: int, unknown_current: int) -> Optional[Tuple[int, int]]:
        """
        Check various pattern conditions for transitive bomb detection
        Analyzes the relationship between current tile and adjacent tile to find safe/bomb tiles
        """
        if self._matches_safe_pattern(unknown_adjacent, adjacent_value, flags_adjacent,
                                      tile_value, flags_current, unknown_current):
            return self._get_directional_tile(tile_coord, neighbor, possibilities, safe=True)

        if self._matches_bomb_pattern(unknown_adjacent, adjacent_value, flags_adjacent,
                                      tile_value, flags_current, unknown_current):
            return self._get_directional_tile(tile_coord, neighbor, possibilities, safe=False)

        return None

    def _matches_safe_pattern(self, unknown_adj: int, adj_val: int, flags_adj: int,
                             tile_val: int, flags_curr: int, unknown_curr: int) -> bool:
        """
        Detect safe tile patterns based on transitive properties
        Returns True if the pattern indicates a safe tile
        """
        # Pattern: Adjacent needs 1 more bomb, current needs 1 more bomb, current has 2 unknowns
        # This means the shared unknown is a bomb, so the opposite unknown is safe
        if unknown_adj == 3 and adj_val == flags_adj + 1 and \
           tile_val == flags_curr + 1 and unknown_curr == 2:
            return True

        # Pattern: Adjacent needs 2 more bombs, current needs 2 more bombs, current has 2 unknowns
        # This means both unknowns of current are bombs, so other adjacents are safe
        if unknown_adj == 3 and adj_val == flags_adj + 2 and \
           tile_val == flags_curr + 2 and unknown_curr == 2:
            return True

        return False

    def _matches_bomb_pattern(self, unknown_adj: int, adj_val: int, flags_adj: int,
                             tile_val: int, flags_curr: int, unknown_curr: int) -> bool:
        """
        Detect bomb tile patterns based on transitive properties
        Returns True if the pattern indicates a bomb tile
        """
        # Pattern: Adjacent needs 2 more bombs, current needs 1 more bomb
        # This indicates a specific directional bomb
        if unknown_adj == 3 and adj_val == flags_adj + 2 and \
           tile_val == flags_curr + 1 and unknown_curr in [2, 3]:
            return True

        # Pattern: Adjacent needs 2 more bombs, current value is 1 (needs 1 bomb total)
        if unknown_adj == 3 and adj_val == flags_adj + 2 and \
           tile_val == 1 and unknown_curr == 3:
            return True

        return False

    def _get_directional_tile(self, key: Tuple[int, int], neighbor: Tuple[int, int],
                             possibilities: List[Tuple[int, int]], safe: bool = True) -> Optional[Tuple[int, int]]:
        """Get the appropriate tile based on direction and pattern type"""
        if not possibilities:
            return None

        direction = (neighbor[0] - key[0], neighbor[1] - key[1])

        # Right: (1, 0) - find max x with same y
        if direction == (1, 0):
            result = self._find_extreme_tile(possibilities, coord_index=0, compare_max=True)
        # Left: (-1, 0) - find min x with same y
        elif direction == (-1, 0):
            result = self._find_extreme_tile(possibilities, coord_index=0, compare_max=False)
        # Down: (0, 1) - find max y with same x
        elif direction == (0, 1):
            result = self._find_extreme_tile(possibilities, coord_index=1, compare_max=True)
        # Up: (0, -1) - find min y with same x
        elif direction == (0, -1):
            result = self._find_extreme_tile(possibilities, coord_index=1, compare_max=False)
        else:
            return None

        if result is None:
            return None

        # Return negative coordinates to indicate flagging
        if not safe:
            return (-1 * result[0], -1 * result[1])
        return result

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

        # Find the extreme value along the variable axis
        if compare_max:
            extreme_pos = max(possibilities, key=lambda p: p[coord_index])
        else:
            extreme_pos = min(possibilities, key=lambda p: p[coord_index])

        return extreme_pos
