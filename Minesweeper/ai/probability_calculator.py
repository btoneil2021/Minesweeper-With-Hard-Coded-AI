from constants import *
from itertools import product


class ProbabilityCalculator:
    """Calculates probabilities for making educated guesses using constraint satisfaction"""

    def __init__(self, board_analyzer):
        self.analyzer = board_analyzer

    def calculate_probabilities(self, target_tile=None):
        """
        Calculate mine probabilities using constraint satisfaction.

        If target_tile is provided, returns probability for that specific tile.
        Otherwise, returns a dictionary of {coordinate: probability} for all unknown tiles.

        Uses exhaustive enumeration of valid mine configurations to compute exact probabilities.
        """
        # Collect all constraints from numbered tiles
        constraints = self._collect_constraints()

        if not constraints:
            # No constraints available - use global probability
            return self._global_probability(target_tile)

        # Get all unknown tiles involved in constraints
        constrained_tiles = set()
        for unknown_tiles, _ in constraints:
            constrained_tiles.update(unknown_tiles)

        if target_tile and target_tile not in constrained_tiles:
            # Target tile not in any constraint - use global probability
            return self._global_probability(target_tile)

        # Count valid configurations where each tile is a mine
        mine_counts = {tile: 0 for tile in constrained_tiles}
        total_valid_configs = 0

        # Enumerate all possible mine configurations
        for config in self._generate_configurations(constrained_tiles):
            if self._is_valid_configuration(config, constraints):
                total_valid_configs += 1
                for tile in config:
                    mine_counts[tile] += 1

        if total_valid_configs == 0:
            # No valid configurations found - shouldn't happen with valid board
            return self._global_probability(target_tile)

        # Calculate probabilities
        probabilities = {
            tile: mine_counts[tile] / total_valid_configs
            for tile in constrained_tiles
        }

        if target_tile:
            return probabilities.get(target_tile, self._global_probability(target_tile))

        return probabilities

    def _collect_constraints(self):
        """
        Collect all constraints from numbered tiles.
        Returns list of (unknown_neighbors, required_mines) tuples.
        """
        constraints = []

        for coord in self.analyzer.get_all_coordinates():
            tile_value = self.analyzer.get_tile_state(coord)

            # Skip non-numbered tiles
            if tile_value in [AI_FLAGGED, AI_UNKNOWN] or tile_value == 0:
                continue

            unknown_neighbors = []
            mines_remaining = tile_value

            for neighbor in self.analyzer.get_neighbors(coord):
                if not self.analyzer.has_tile(neighbor):
                    continue

                neighbor_state = self.analyzer.get_tile_state(neighbor)

                if neighbor_state == AI_UNKNOWN:
                    unknown_neighbors.append(neighbor)
                elif neighbor_state == AI_FLAGGED:
                    mines_remaining -= 1

            # Only add constraint if there are unknown neighbors
            if unknown_neighbors:
                constraints.append((tuple(unknown_neighbors), mines_remaining))

        return constraints

    def _generate_configurations(self, tiles):
        """
        Generate all possible mine configurations for the given tiles.
        Each configuration is a set of tiles that are mines.
        """
        tiles_list = list(tiles)
        n = len(tiles_list)

        # Generate all 2^n binary combinations
        for bits in product([False, True], repeat=n):
            config = {tiles_list[i] for i, is_mine in enumerate(bits) if is_mine}
            yield config

    def _is_valid_configuration(self, config, constraints):
        """
        Check if a mine configuration satisfies all constraints.
        config: set of tiles that are mines
        constraints: list of (tiles, required_mine_count) tuples
        """
        for tiles, required_mines in constraints:
            actual_mines = sum(1 for tile in tiles if tile in config)
            if actual_mines != required_mines:
                return False
        return True

    def _global_probability(self, target_tile=None):
        """
        Calculate global mine probability based on total mines and unknown tiles.
        """
        total_unknown = sum(1 for state in self.analyzer.get_all_values()
                          if state == AI_UNKNOWN)
        total_flagged = sum(1 for state in self.analyzer.get_all_values()
                          if state == AI_FLAGGED)

        if total_unknown == 0:
            return 0.0

        # Remaining mines = total mines - flagged mines
        remaining_mines = NUM_BOMBS - total_flagged

        return remaining_mines / total_unknown