from constants import *
from .constraint_collector import ConstraintCollector
from .configuration_validator import ConfigurationValidator

class ProbabilityCalculator:
    def __init__(self, board_analyzer):
        self.analyzer = board_analyzer
        self.constraint_collector = ConstraintCollector(board_analyzer)

    def calculate_probabilities(self, target_tile=None):
        """
        Calculate mine probabilities for tiles.

        Args:
            target_tile: Optional specific tile coordinate. If provided, returns float.
                        If None, returns dict of all probabilities.

        Returns:
            If target_tile provided: float probability (0.0 to 1.0)
            If target_tile is None: dict mapping {(x, y): probability} for ALL unknown tiles
        """
        constraints = self.constraint_collector.collect_all_constraints()

        # No constraints: use global probability for all tiles
        if not constraints:
            return self._calculate_global_probability(target_tile)

        # Calculate probabilities based on constraints
        constrained_probs = self._calculate_constrained_probabilities(constraints)

        # Fallback to global if calculation failed
        if not constrained_probs:
            return self._calculate_global_probability(target_tile)

        # If requesting specific tile
        if target_tile:
            # Check if tile is constrained
            if target_tile in constrained_probs:
                return constrained_probs[target_tile]
            else:
                # Unconstrained tile: use global probability
                return self._calculate_global_probability(target_tile)

        # Return all tiles: merge constrained + unconstrained
        all_probabilities = dict(constrained_probs)

        # Calculate weighted probability for unconstrained tiles
        # This uses the same global weighting approach as constrained tiles
        unconstrained_prob = self._calculate_unconstrained_probability(constraints, constrained_probs)

        # Add unconstrained tiles with weighted probability
        for coord in self.analyzer.get_all_coordinates():
            if (self.analyzer.get_tile_state(coord) == AI_UNKNOWN and
                coord not in all_probabilities):
                all_probabilities[coord] = unconstrained_prob

        return all_probabilities

    def _is_tile_constrained(self, tile, constraints):
        """Check if a tile is affected by any constraint"""
        for constraint in constraints:
            if tile in constraint.get_constrained_tiles():
                return True
        return False

    def _get_all_constrained_tiles(self, constraints):
        """Get set of all tiles affected by constraints"""
        constrained_tiles = set()
        for constraint in constraints:
            constrained_tiles.update(constraint.get_constrained_tiles())
        return constrained_tiles

    def _calculate_constrained_probabilities(self, constraints):
        """
        Calculate probabilities using constraint satisfaction with global probability weighting.

        This is the SOTA approach: weight each configuration by the number of ways
        remaining mines can be placed in unconstrained tiles.

        Returns:
            dict: {(x, y): probability} for all constrained tiles
        """
        # Get all valid configurations
        valid_configs = ConfigurationValidator.get_all_valid_configurations(constraints)

        if not valid_configs:
            return {}

        # Calculate global mine budget and unconstrained tile count
        total_unknown = sum(1 for state in self.analyzer.get_all_values()
                          if state == AI_UNKNOWN)
        total_flagged = sum(1 for state in self.analyzer.get_all_values()
                          if state == AI_FLAGGED)
        remaining_mines = NUM_BOMBS - total_flagged

        # Get constrained tiles (tiles affected by constraints)
        constrained_tiles = set()
        for constraint in constraints:
            constrained_tiles.update(constraint.get_constrained_tiles())

        # Unconstrained tiles = all unknown tiles - constrained tiles
        unconstrained_count = total_unknown - len(constrained_tiles)

        # Weight each configuration by C(unconstrained_count, remaining_mines - mines_in_config)
        # Use log-space arithmetic to avoid overflow with large numbers
        import math

        # Store log-weights for each configuration
        log_weights = []
        config_data = []

        for config_info in valid_configs:
            mines_in_config = config_info['mine_count']
            mines_for_unconstrained = remaining_mines - mines_in_config

            # Log-weight = log(C(unconstrained_count, mines_for_unconstrained))
            log_weight = ConfigurationValidator.log_combinations(unconstrained_count, mines_for_unconstrained)

            if log_weight != float('-inf'):
                log_weights.append(log_weight)
                config_data.append(config_info)

        if not log_weights:
            return {}

        # Calculate log(total_weight) using logsumexp trick
        max_log_weight = max(log_weights)
        total_weight_log = max_log_weight + math.log(sum(math.exp(lw - max_log_weight) for lw in log_weights))

        # Calculate weighted mine counts in log-space
        tile_log_weights = {tile: [] for tile in constrained_tiles}

        for i, config_info in enumerate(config_data):
            log_weight = log_weights[i]
            for tile in config_info['config']:
                if tile in tile_log_weights:
                    tile_log_weights[tile].append(log_weight)

        # Convert to probabilities
        probabilities = {}
        for tile in constrained_tiles:
            if tile_log_weights[tile]:
                # log(sum of weights where tile is mine)
                max_lw = max(tile_log_weights[tile])
                mine_weight_log = max_lw + math.log(sum(math.exp(lw - max_lw) for lw in tile_log_weights[tile]))

                # Probability = mine_weight / total_weight (in normal space)
                probabilities[tile] = math.exp(mine_weight_log - total_weight_log)
            else:
                probabilities[tile] = 0.0

        return probabilities

    def _calculate_unconstrained_probability(self, constraints, constrained_probs):
        """
        Calculate weighted probability for unconstrained tiles using global weighting.

        Args:
            constraints: List of constraints
            constrained_probs: Dict of probabilities for constrained tiles

        Returns:
            float: Weighted probability for an unconstrained tile
        """
        # Get all valid configurations
        valid_configs = ConfigurationValidator.get_all_valid_configurations(constraints)

        if not valid_configs:
            # No constraints - use simple global probability
            return self._calculate_global_probability_value()

        # Calculate global mine budget and tile counts
        total_unknown = sum(1 for state in self.analyzer.get_all_values()
                          if state == AI_UNKNOWN)
        total_flagged = sum(1 for state in self.analyzer.get_all_values()
                          if state == AI_FLAGGED)
        remaining_mines = NUM_BOMBS - total_flagged

        # Get constrained tiles
        constrained_tiles = set()
        for constraint in constraints:
            constrained_tiles.update(constraint.get_constrained_tiles())

        unconstrained_count = total_unknown - len(constrained_tiles)

        if unconstrained_count == 0:
            return 0.0

        # Calculate weighted average probability for unconstrained tiles
        # Use log-space arithmetic to avoid overflow
        import math

        log_weights = []
        probs = []

        for config_info in valid_configs:
            mines_in_config = config_info['mine_count']
            mines_for_unconstrained = remaining_mines - mines_in_config

            # Log-weight = log(C(unconstrained_count, mines_for_unconstrained))
            log_weight = ConfigurationValidator.log_combinations(unconstrained_count, mines_for_unconstrained)

            if log_weight != float('-inf'):
                # Probability for one unconstrained tile in this configuration
                prob = mines_for_unconstrained / unconstrained_count
                log_weights.append(log_weight)
                probs.append(prob)

        if not log_weights:
            return self._calculate_global_probability_value()

        # Calculate weighted average using log-space arithmetic
        # weighted_avg = sum(weight * prob) / sum(weight)
        max_log_weight = max(log_weights)

        # Numerator: sum(weight * prob)
        numerator = sum(math.exp(log_weights[i] - max_log_weight) * probs[i] for i in range(len(log_weights)))

        # Denominator: sum(weight)
        denominator = sum(math.exp(lw - max_log_weight) for lw in log_weights)

        return numerator / denominator

    def _calculate_global_probability_value(self):
        """Helper to calculate simple global probability as a float value."""
        total_unknown = sum(1 for state in self.analyzer.get_all_values()
                          if state == AI_UNKNOWN)
        total_flagged = sum(1 for state in self.analyzer.get_all_values()
                          if state == AI_FLAGGED)

        if total_unknown == 0:
            return 0.0

        remaining_mines = NUM_BOMBS - total_flagged
        return remaining_mines / total_unknown

    def _calculate_global_probability(self, target_tile=None):
        """
        Calculate probability based on remaining mines / unknown tiles.
        Used when no constraints exist or for unconstrained tiles.

        Returns:
            float if target_tile provided, dict otherwise
        """
        total_unknown = sum(1 for state in self.analyzer.get_all_values()
                          if state == AI_UNKNOWN)
        total_flagged = sum(1 for state in self.analyzer.get_all_values()
                          if state == AI_FLAGGED)

        if total_unknown == 0:
            return 0.0

        remaining_mines = NUM_BOMBS - total_flagged
        global_prob = remaining_mines / total_unknown

        if target_tile:
            return global_prob

        # Return probability for all unknown tiles
        return {coord: global_prob for coord in self.analyzer.get_all_coordinates()
                if self.analyzer.get_tile_state(coord) == AI_UNKNOWN}

    def _get_distance_to_frontier(self, tile):
        """
        Calculate minimum distance from tile to any revealed/numbered tile (the frontier).
        Lower distance = closer to known information.

        Args:
            tile: Coordinate tuple (x, y)

        Returns:
            int: Minimum Manhattan distance to frontier (0 = on frontier)
        """
        min_distance = float('inf')

        for coord in self.analyzer.get_all_coordinates():
            state = self.analyzer.get_tile_state(coord)
            # Check if tile is revealed (not unknown, not flagged)
            if state not in [AI_UNKNOWN, AI_FLAGGED]:
                # Calculate Manhattan distance
                distance = abs(tile[0] - coord[0]) + abs(tile[1] - coord[1])
                min_distance = min(min_distance, distance)

        return min_distance if min_distance != float('inf') else 1000

    def get_tile_constraints(self, tile):
        """
        Get all constraints affecting a specific tile (for debugging).

        Args:
            tile: Coordinate tuple (x, y)

        Returns:
            list of Constraint objects that include this tile
        """
        all_constraints = self.constraint_collector.collect_all_constraints()
        return [c for c in all_constraints if tile in c.get_constrained_tiles()]

    def format_probabilities(self, max_results=20):
        """
        Format probabilities in a human-readable way (for debugging).

        Args:
            max_results: Maximum number of tiles to show

        Returns:
            str: Formatted probability string
        """
        probabilities = self.calculate_probabilities()

        if not probabilities:
            return "No probabilities available (no unknown tiles or calculation failed)"

        # Sort by probability (lowest first - safest moves)
        sorted_probs = sorted(probabilities.items(), key=lambda x: x[1])

        lines = ["Mine Probabilities (lowest = safest):"]
        lines.append("-" * 40)

        for i, (tile, prob) in enumerate(sorted_probs[:max_results]):
            percentage = prob * 100
            bar_length = int(prob * 20)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            lines.append(f"{tile}: {percentage:5.1f}% {bar}")

        if len(sorted_probs) > max_results:
            lines.append(f"... and {len(sorted_probs) - max_results} more tiles")

        return "\n".join(lines)

    def find_lowest_probability_tile(self):
        """
        Find the tile with the lowest mine probability (safest tile to click).

        Uses smart tie-breaking:
        1. Primary: Lowest probability
        2. Secondary: Closest to frontier (more information gain)
        3. Tertiary: Random selection

        Returns:
            tuple: ((x, y), probability) or (None, 1.0) if no tiles available
        """
        import random

        probabilities = self.calculate_probabilities()

        if not probabilities or not isinstance(probabilities, dict):
            return (None, 1.0)

        # Find minimum probability
        min_prob = min(probabilities.values())

        # Get all tiles with minimum probability (handle ties)
        candidates = [(tile, prob) for tile, prob in probabilities.items()
                     if prob == min_prob]

        if len(candidates) == 1:
            return candidates[0]

        # Multiple tiles with same probability - prefer frontier tiles
        # Sort by distance to frontier (ascending = closer first)
        candidates_with_distance = [
            (tile, prob, self._get_distance_to_frontier(tile))
            for tile, prob in candidates
        ]
        candidates_with_distance.sort(key=lambda x: x[2])

        # Get all tiles with minimum distance
        min_distance = candidates_with_distance[0][2]
        best_candidates = [(tile, prob) for tile, prob, dist in candidates_with_distance
                          if dist == min_distance]

        # Random selection among remaining ties
        return random.choice(best_candidates)

    def find_highest_probability_tile(self, threshold=0.9):
        """
        Find the tile with the highest mine probability (best tile to flag).

        Args:
            threshold: Only return tiles with probability >= threshold

        Returns:
            tuple: ((x, y), probability) or (None, 0.0) if no good candidates
        """
        probabilities = self.calculate_probabilities()

        if not probabilities or not isinstance(probabilities, dict):
            return (None, 0.0)

        # Find tile with maximum probability
        best_tile, best_prob = max(probabilities.items(), key=lambda x: x[1])

        # Only return if above threshold
        if best_prob >= threshold:
            return (best_tile, best_prob)

        return (None, 0.0)