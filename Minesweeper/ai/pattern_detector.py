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

    def _get_two_hop_neighbors(self, tile_coord: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Get all tiles within 2 hops (direct neighbors + neighbors-of-neighbors).
        This allows constraint subtraction to work on tiles that aren't directly adjacent.

        Example:
        1 blank 2  ← "1" and "2" are 2 hops apart
        """
        two_hop_neighbors = set()

        # Add direct neighbors (1-hop)
        for neighbor in self.analyzer.get_neighbors(tile_coord):
            if self.analyzer.has_tile(neighbor):
                two_hop_neighbors.add(neighbor)

                # Add neighbors-of-neighbors (2-hop)
                for second_hop in self.analyzer.get_neighbors(neighbor):
                    if self.analyzer.has_tile(second_hop) and second_hop != tile_coord:
                        two_hop_neighbors.add(second_hop)

        return list(two_hop_neighbors)

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
        tile_value = self._get_tile_value_if_valid(tile_coord)
        if tile_value is None or tile_value == 0:
            return None

        # Get tile A's context
        flags_a = self.analyzer.count_neighbors_by_states(tile_coord, [AI_FLAGGED])
        unknowns_a = set(self.analyzer.get_neighbors_by_state(tile_coord, AI_UNKNOWN))
        mines_needed_a = tile_value - flags_a

        if not unknowns_a or mines_needed_a <= 0:
            return None

        # Check numbered tiles within 2 hops (includes 1-hop neighbors + 2-hop neighbors)
        for neighbor_coord in self._get_two_hop_neighbors(tile_coord):
            neighbor_value = self._get_tile_value_if_valid(neighbor_coord)
            if neighbor_value is None or neighbor_value == 0:
                continue
            if neighbor_value in [AI_FLAGGED, AI_UNKNOWN]:
                continue

            # Get tile B's context
            flags_b = self.analyzer.count_neighbors_by_states(neighbor_coord, [AI_FLAGGED])
            unknowns_b = set(self.analyzer.get_neighbors_by_state(neighbor_coord, AI_UNKNOWN))
            mines_needed_b = neighbor_value - flags_b

            if not unknowns_b or mines_needed_b <= 0:
                continue

            # Check if B's unknowns are subset of A's unknowns
            if unknowns_b.issubset(unknowns_a):
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

            # Check if A's unknowns are subset of B's unknowns (reverse case)
            if unknowns_a.issubset(unknowns_b):
                difference = unknowns_b - unknowns_a

                # Case 1: All difference tiles must be mines
                if difference and mines_needed_b - mines_needed_a == len(difference):
                    tile_to_flag = next(iter(difference))
                    return (-tile_to_flag[0], -tile_to_flag[1])

                # Case 2: All difference tiles must be safe
                if difference and mines_needed_b == mines_needed_a:
                    return next(iter(difference))

            # Case 3: Overlapping constraints (neither is subset of the other)
            # Example: A sees {X, Y, Z} needs 2, B sees {Y, Z, W} needs 1
            # Overlap {Y, Z} can have at most 1 mine, so X must be a mine
            intersection = unknowns_a & unknowns_b
            if intersection and intersection != unknowns_a and intersection != unknowns_b:
                diff_a = unknowns_a - unknowns_b  # Tiles only A sees
                diff_b = unknowns_b - unknowns_a  # Tiles only B sees

                if len(diff_a) == 1 and len(diff_b) == 1:
                    # Single tile in each difference - can deduce exact values
                    tile_a = next(iter(diff_a))
                    tile_b = next(iter(diff_b))

                    # Logic: If intersection has X mines:
                    # - tile_a has (mines_needed_a - X) mines
                    # - tile_b has (mines_needed_b - X) mines
                    # Since both are single tiles, they can only be 0 or 1

                    # Maximum mines in intersection
                    max_intersection_mines = min(len(intersection), mines_needed_a, mines_needed_b)

                    # Minimum mines in intersection
                    min_intersection_mines = max(0,
                                                mines_needed_a - len(diff_a),
                                                mines_needed_b - len(diff_b))

                    # If mines_needed_a > max possible in intersection, tile_a must be mine
                    if mines_needed_a > max_intersection_mines:
                        return (-tile_a[0], -tile_a[1])

                    # If mines_needed_b > max possible in intersection, tile_b must be mine
                    if mines_needed_b > max_intersection_mines:
                        return (-tile_b[0], -tile_b[1])

                    # If min mines in intersection accounts for all of A's needs, tile_a is safe
                    if mines_needed_a == min_intersection_mines:
                        return tile_a

                    # If min mines in intersection accounts for all of B's needs, tile_b is safe
                    if mines_needed_b == min_intersection_mines:
                        return tile_b

        return None
