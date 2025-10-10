from typing import Optional, Tuple
from constants import *

class ConstraintSubtractor:
    def __init__(self, board_analyzer):
        self.analyzer = board_analyzer

    def constraint_subtraction(self, tile_coord: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        Detects constraint subtraction patterns between numbered tiles (up to 2 hops apart).

        Pattern: If tile A's unknowns are a superset of tile B's unknowns,
        and we can deduce specific tiles must be mines or safe by subtraction.

        Example:
        - Tile A needs 2 mines in {X, Y, Z}
        - Tile B needs 1 mine in {Y, Z}
        - Therefore: X must be a mine (flag it)

        Now checks tiles up to 2 hops away to catch patterns like:
        1 blank 2  (where "1" and "2" aren't directly adjacent)

        Returns: Tile coordinate to flag (negative) or reveal, or None
        """
        if (tile_value := self.analyzer.get_tile_value_if_valid(tile_coord)) is None \
              or tile_value == 0:
            return None
        
        unknowns_a, mines_needed_a = self._get_tile_context(tile_coord, tile_value)

        if not unknowns_a or mines_needed_a <= 0:
            return None

        return self._check_and_return_two_hop_neighbors(tile_coord, unknowns_a, mines_needed_a)
    
    def _get_tile_context(self, tile_coord, tile_value):
        flags_around = self.analyzer.count_neighbors_by_states(tile_coord, [AI_FLAGGED])

        return (
            set(self.analyzer.get_neighbors_by_state(tile_coord, AI_UNKNOWN)),
            tile_value - flags_around
        )
    
    def _check_and_return_two_hop_neighbors(self, tile_coord, unknowns_a, mines_needed_a):
        for neighbor_coord in self.analyzer.get_two_hop_neighbors(tile_coord):
            if (neighbor_value := self.analyzer.get_tile_value_if_valid(neighbor_coord)) is None \
                  or neighbor_value == 0 \
                    or neighbor_value in [AI_FLAGGED, AI_UNKNOWN]:
                continue

            unknowns_b, mines_needed_b = self._get_tile_context(neighbor_coord, neighbor_value)

            if not unknowns_b or mines_needed_b <= 0:
                continue

            result_tile_coords = self._unknowns_subset_of_other_unknowns(unknowns_a, mines_needed_a,
                                                                       unknowns_b, mines_needed_b)
            if result_tile_coords is not None:
                return result_tile_coords

            result_tile_coords = self._unknowns_subset_of_other_unknowns(unknowns_b, mines_needed_b,
                                                                       unknowns_a, mines_needed_a)
            if result_tile_coords is not None:
                return result_tile_coords

            result_tile_coords = self._overlapping_constraints_case(unknowns_a, mines_needed_a,
                                                                    unknowns_b, mines_needed_b)
            if result_tile_coords is not None:
                return result_tile_coords
            
        return None
    
    def _unknowns_subset_of_other_unknowns(self, unknowns_a, mines_needed_a, unknowns_b, mines_needed_b):
        if not unknowns_b.issubset(unknowns_a):
            return None
        
        difference = unknowns_a - unknowns_b

        # Case 1: All difference tiles must be mines
        # A needs N mines in {B's tiles + difference}
        # B needs M mines in {B's tiles}
        # If N - M = len(difference), all difference tiles are mines
        if difference and mines_needed_a - mines_needed_b == len(difference):
            # Flag one of the difference tiles
            tile_to_flag = next(iter(difference))
            return (-tile_to_flag[0], -tile_to_flag[1])

        # Case 2: All difference tiles must be safe
        # If N = M, then B accounts for all of A's mines
        # So difference tiles are safe
        if difference and mines_needed_a == mines_needed_b:
            # Reveal one of the difference tiles
            return next(iter(difference))
    
    def _overlapping_constraints_case(self, unknowns_a, mines_needed_a, unknowns_b, mines_needed_b):
        # Case 3: Overlapping constraints (neither is subset of the other)
        # Example: A sees {X, Y, Z} needs 2, B sees {Y, Z, W} needs 1
        # Overlap {Y, Z} can have at most 1 mine, so X must be a mine
        intersection = unknowns_a & unknowns_b

        if not intersection or intersection == unknowns_a or intersection == unknowns_b:
            return None
        
        diff_a = unknowns_a - unknowns_b
        diff_b = unknowns_b - unknowns_a

        if len(diff_a) != 1 or len(diff_b) != 1:
            return None
        
        # Single tile in each difference - can deduce exact values
        tile_a = next(iter(diff_a))
        tile_b = next(iter(diff_b))

        max_intersection_mines = min(len(intersection), mines_needed_a, mines_needed_b)

        min_intersection_mines = max(0,
                                    mines_needed_a - len(diff_a),
                                    mines_needed_b - len(diff_b))

        if mines_needed_a > max_intersection_mines:
            return (-tile_a[0], -tile_a[1])

        if mines_needed_b > max_intersection_mines:
            return (-tile_b[0], -tile_b[1])

        if mines_needed_a == min_intersection_mines:
            return tile_a

        if mines_needed_b == min_intersection_mines:
            return tile_b
        
        return None