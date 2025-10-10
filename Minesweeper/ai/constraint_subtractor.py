from typing import Optional, Tuple, Set, NamedTuple
from constants import *

class TileConstraint(NamedTuple):
    unknowns: Set[Tuple[int, int]]
    mines_needed: int

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
        
        constraint_a = self._get_tile_context(tile_coord, tile_value)

        if not constraint_a.unknowns or constraint_a.mines_needed <= 0:
            return None

        return self._check_and_return_two_hop_neighbors(tile_coord, constraint_a)
    
    def _get_tile_context(self, tile_coord, tile_value) -> TileConstraint:
        flags_around = self.analyzer.count_neighbors_by_states(tile_coord, [AI_FLAGGED])
        unknowns = set(self.analyzer.get_neighbors_by_state(tile_coord, AI_UNKNOWN))
        mines_needed = tile_value - flags_around
        
        return TileConstraint(unknowns, mines_needed)
    
    def _check_and_return_two_hop_neighbors(self, tile_coord, constraint_a: TileConstraint):
        for neighbor_coord in self.analyzer.get_two_hop_neighbors(tile_coord):
            if (constraint_b := self._get_valid_neighbor_constraint(neighbor_coord)) is None:
                continue

            if result := self._try_constraint_strategies(constraint_a, constraint_b):
                return result

        return None

    def _get_valid_neighbor_constraint(self, neighbor_coord) -> Optional[TileConstraint]:
        """Returns constraint for neighbor if valid, otherwise None."""
        if (neighbor_value := self.analyzer.get_tile_value_if_valid(neighbor_coord)) is None \
              or neighbor_value == 0 \
              or neighbor_value in [AI_FLAGGED, AI_UNKNOWN]:
            return None

        constraint = self._get_tile_context(neighbor_coord, neighbor_value)

        if not constraint.unknowns or constraint.mines_needed <= 0:
            return None

        return constraint

    def _try_constraint_strategies(self, constraint_a: TileConstraint, constraint_b: TileConstraint):
        """Try all constraint solving strategies in sequence."""
        for check_order in [(constraint_a, constraint_b), (constraint_b, constraint_a)]:
            if result := self._unknowns_subset_of_other_unknowns(*check_order):
                return result

        return self._overlapping_constraints_case(constraint_a, constraint_b)
    
    def _unknowns_subset_of_other_unknowns(self, constraint_a: TileConstraint, constraint_b: TileConstraint):
        if not constraint_b.unknowns.issubset(constraint_a.unknowns):
            return None

        difference = constraint_a.unknowns - constraint_b.unknowns

        if tile := self._all_difference_tiles_are_mines(difference, constraint_a, constraint_b):
            return tile

        if tile := self._all_difference_tiles_are_safe(difference, constraint_a, constraint_b):
            return tile

    def _all_difference_tiles_are_mines(self, difference, constraint_a: TileConstraint, constraint_b: TileConstraint):
        """A needs N mines in {B's tiles + difference}, B needs M in {B's tiles}.
        If N - M = len(difference), all difference tiles are mines."""
        if difference and constraint_a.mines_needed - constraint_b.mines_needed == len(difference):
            tile_to_flag = next(iter(difference))
            return (-tile_to_flag[0], -tile_to_flag[1])

    def _all_difference_tiles_are_safe(self, difference, constraint_a: TileConstraint, constraint_b: TileConstraint):
        """If N = M, then B accounts for all of A's mines, so difference tiles are safe."""
        if difference and constraint_a.mines_needed == constraint_b.mines_needed:
            return next(iter(difference))

    def _overlapping_constraints_case(self, constraint_a: TileConstraint, constraint_b: TileConstraint):
        # Case 3: Overlapping constraints (neither is subset of the other)
        # Example: A sees {X, Y, Z} needs 2, B sees {Y, Z, W} needs 1
        # Overlap {Y, Z} can have at most 1 mine, so X must be a mine
        if not self._is_single_tile_in_difference(constraint_a.unknowns, constraint_b.unknowns):
            return None

        intersection = constraint_a.unknowns & constraint_b.unknowns
        diff_a = constraint_a.unknowns - constraint_b.unknowns
        diff_b = constraint_b.unknowns - constraint_a.unknowns
        tile_a, tile_b = next(iter(diff_a)), next(iter(diff_b))

        max_intersection_mines = min(len(intersection), constraint_a.mines_needed, constraint_b.mines_needed)
        min_intersection_mines = max(0, constraint_a.mines_needed - 1, constraint_b.mines_needed - 1)

        if constraint_a.mines_needed > max_intersection_mines: return (-tile_a[0], -tile_a[1])
        if constraint_b.mines_needed > max_intersection_mines: return (-tile_b[0], -tile_b[1])
        if constraint_a.mines_needed == min_intersection_mines: return tile_a
        if constraint_b.mines_needed == min_intersection_mines: return tile_b

        return None
    
    def _is_single_tile_in_difference(self, unknowns_a, unknowns_b):
        if not self._is_intersection(unknowns_a, unknowns_b):
            return False
        
        diff_a = unknowns_a - unknowns_b
        diff_b = unknowns_b - unknowns_a
        
        return (len(diff_a) == 1 and len(diff_b) == 1)
        
    def _is_intersection(self, unknowns_a, unknowns_b):
        intersection = unknowns_a & unknowns_b

        return (intersection and intersection != unknowns_a and intersection != unknowns_b)
    