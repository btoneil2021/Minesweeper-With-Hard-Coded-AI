from constants import *


class PatternDetector:
    """Detects common minesweeper patterns for making logical deductions"""

    def __init__(self, board_analyzer):
        self.analyzer = board_analyzer

    def same_bombs_as_squares(self, key):
        """
        Detects when the number of unknown squares equals the tile value
        This means all unknown squares must be bombs
        """
        if not self.analyzer.has_tile(key):
            return None

        tile_value = self.analyzer.get_tile_state(key)
        open_square_number = 0

        for neighbor in self.analyzer.get_neighbors(key):
            if not self.analyzer.has_tile(neighbor):
                continue
            if self.analyzer.get_tile_state(neighbor) in [AI_FLAGGED, AI_UNKNOWN]:
                open_square_number += 1

        if open_square_number == tile_value:
            tiles_to_update = []
            for neighbor in self.analyzer.get_neighbors(key):
                if not self.analyzer.has_tile(neighbor):
                    continue
                if self.analyzer.get_tile_state(neighbor) == AI_UNKNOWN:
                    tiles_to_update.append(neighbor)
            return tiles_to_update
        return None

    def all_bombs_found(self, key):
        """
        Detects when all bombs around a tile are flagged
        This means all remaining unknown squares are safe
        """
        if not self.analyzer.has_tile(key):
            return None

        tile_value = self.analyzer.get_tile_state(key)
        flags_around = 0

        for neighbor in self.analyzer.get_neighbors(key):
            if not self.analyzer.has_tile(neighbor):
                continue
            if self.analyzer.get_tile_state(neighbor) == AI_FLAGGED:
                flags_around += 1

        if flags_around == tile_value:
            tiles_to_update = []
            for neighbor in self.analyzer.get_neighbors(key):
                if not self.analyzer.has_tile(neighbor):
                    continue
                if self.analyzer.get_tile_state(neighbor) == AI_UNKNOWN:
                    tiles_to_update.append(neighbor)
            if len(tiles_to_update) != 0:
                return tiles_to_update
        return None

    def transitive_bomb_property(self, key):
        """
        Advanced pattern detection using transitive properties between adjacent tiles
        Returns tile coordinates to reveal or flag (negative coordinates indicate flag)
        """
        if not self.analyzer.has_tile(key):
            return None

        tile_value = self.analyzer.get_tile_state(key)
        flags_around = 0
        open_square_number = 0
        possibilities = []
        check_availability = 4

        # Check if there are any unknown cardinal neighbors
        for neighbor in self.analyzer.get_cardinal_neighbors(key):
            if not self.analyzer.has_tile(neighbor):
                check_availability -= 1
            elif self.analyzer.get_tile_state(neighbor) >= -1:
                check_availability -= 1

        if check_availability == 0:
            return None

        # Count flags and unknown squares around the key tile
        for neighbor in self.analyzer.get_neighbors(key):
            if not self.analyzer.has_tile(neighbor):
                continue
            elif self.analyzer.get_tile_state(neighbor) == AI_UNKNOWN:
                open_square_number += 1
            elif self.analyzer.get_tile_state(neighbor) == AI_FLAGGED:
                flags_around += 1

        # Check each cardinal direction for pattern matches
        for neighbor in self.analyzer.get_cardinal_neighbors(key):
            if not self.analyzer.has_tile(neighbor):
                continue
            if self.analyzer.get_tile_state(neighbor) in [AI_UNKNOWN, AI_FLAGGED]:
                continue

            adjacent_tile_value = self.analyzer.get_tile_state(neighbor)
            flags_around_adjacent = 0
            open_square_number_around_adjacent = 0

            # Analyze the adjacent tile
            for neighbor2 in self.analyzer.get_neighbors(neighbor):
                if not self.analyzer.has_tile(neighbor2):
                    continue
                elif self.analyzer.get_tile_state(neighbor2) == AI_UNKNOWN:
                    open_square_number_around_adjacent += 1
                    possibilities.append(neighbor2)
                elif self.analyzer.get_tile_state(neighbor2) == AI_FLAGGED:
                    flags_around_adjacent += 1

            # Pattern matching conditions
            result = self._check_pattern_conditions(
                key, neighbor, possibilities,
                open_square_number_around_adjacent, adjacent_tile_value,
                flags_around_adjacent, tile_value, flags_around, open_square_number
            )
            if result is not None:
                return result

        return None

    def _check_pattern_conditions(self, key, neighbor, possibilities,
                                  open_sq_adj, adj_val, flags_adj,
                                  tile_val, flags, open_sq):
        """Helper method to check various pattern conditions"""
        # Pattern 1: Safe tile detection
        if (all([open_sq_adj == 3, adj_val == flags_adj + 1, tile_val == flags + 1, open_sq == 2]) or
            all([open_sq_adj == 3, adj_val == flags_adj + 2, tile_val == flags + 2, open_sq == 2])):
            return self._get_directional_tile(key, neighbor, possibilities, safe=True)

        # Pattern 2: Bomb detection
        if (all([open_sq_adj == 3, adj_val == flags_adj + 2, tile_val == flags + 1, open_sq in [2, 3]]) or
            all([open_sq_adj == 3, adj_val == flags_adj + 2, tile_val == 1, open_sq == 3])):
            return self._get_directional_tile(key, neighbor, possibilities, safe=False)

        return None

    def _get_directional_tile(self, key, neighbor, possibilities, safe=True):
        """Get the appropriate tile based on direction and pattern type"""
        if not possibilities:
            return None

        the_val = (-1, -1) if safe else (0, 0)

        if neighbor == (key[0] + 1, key[1]):  # Right
            y = possibilities[0][1]
            for x, placeholder_y in possibilities:
                if (safe and x >= the_val[0]) or (not safe and x > the_val[0]):
                    the_val = (x, y)
                if placeholder_y != y:
                    return None
        elif neighbor == (key[0] - 1, key[1]):  # Left
            from constants import NUM_TILES_X, NUM_TILES_Y
            the_val = (NUM_TILES_X, NUM_TILES_Y)
            y = possibilities[0][1]
            for x, placeholder_y in possibilities:
                if x < the_val[0]:
                    the_val = (x, y)
                if placeholder_y != y:
                    return None
        elif neighbor == (key[0], key[1] + 1):  # Down
            x = possibilities[0][0]
            for placeholder_x, y in possibilities:
                if (safe and y > the_val[1]) or (not safe and y > the_val[1]):
                    the_val = (x, y)
                if placeholder_x != x:
                    return None
        elif neighbor == (key[0], key[1] - 1):  # Up
            from constants import NUM_TILES_X, NUM_TILES_Y
            the_val = (NUM_TILES_X, NUM_TILES_Y)
            x = possibilities[0][0]
            for placeholder_x, y in possibilities:
                if y < the_val[1]:
                    the_val = (x, y)
                if placeholder_x != x:
                    return None

        # Return negative coordinates to indicate flagging
        if not safe:
            return (-1 * the_val[0], -1 * the_val[1])
        return the_val
