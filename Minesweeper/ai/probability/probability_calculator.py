from constants import *
from .constraint_collector import ConstraintCollector
from .constraint_grouper import ConstraintGrouper
from .configuration_generator import ConfigurationGenerator
from .math_utilities import log_combinations, logsumexp, weighted_average_in_log_space
import math
import random


class ProbabilityCalculator:
    """
    Orchestrates probability calculation using three-layer architecture.

    Layer 1: Constraint extraction and grouping
    Layer 2: Configuration generation
    Layer 3: Probability calculation with log-space weighting
    """

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
        # Layer 1: Extract and group constraints
        constraints = self.constraint_collector.collect_all_constraints()

        # No constraints: use global probability
        if not constraints:
            return self._calculate_global_probability(target_tile)

        # Layer 2 & 3: Generate configurations and calculate probabilities
        constrained_probs = self._calculate_constrained_probabilities(constraints)

        # Fallback to global if calculation failed
        if not constrained_probs:
            return self._calculate_global_probability(target_tile)

        # If requesting specific tile
        if target_tile:
            if target_tile in constrained_probs:
                return constrained_probs[target_tile]
            else:
                # Unconstrained tile: use global probability
                return self._calculate_global_probability(target_tile)

        # Return all tiles: merge constrained + unconstrained
        all_probabilities = dict(constrained_probs)

        # Calculate weighted probability for unconstrained tiles
        unconstrained_prob = self._calculate_unconstrained_probability(constraints, constrained_probs)

        # Add unconstrained tiles
        for coord in self.analyzer.get_all_coordinates():
            if (self.analyzer.get_tile_state(coord) == AI_UNKNOWN and
                coord not in all_probabilities):
                all_probabilities[coord] = unconstrained_prob

        return all_probabilities

    def _calculate_constrained_probabilities(self, constraints):
        """
        Calculate probabilities using constraint satisfaction with global weighting.

        Uses the three-layer architecture:
        1. Group constraints (Layer 1)
        2. Generate valid configurations (Layer 2)
        3. Weight and calculate probabilities (Layer 3)

        Returns:
            dict: {(x, y): probability} for all constrained tiles
        """
        # Layer 1: Group constraints
        groups = ConstraintGrouper.group_constraints(constraints)

        if not groups:
            return {}

        # Merge all groups to get complete set of constrained tiles.
        # Note: Even though groups are mathematically independent for constraint
        # satisfaction, we MUST process all constrained tiles together for correct
        # global weighting. The weight C(unconstrained_count, mines_for_unconstrained)
        # requires knowing the TRUE number of unconstrained tiles, which is:
        #   total_unknown - len(ALL constrained tiles)
        # Processing groups separately would incorrectly inflate unconstrained_count.
        all_constrained_tiles = set()
        for _, tiles in groups:
            all_constrained_tiles.update(tiles)

        # Layer 2: Generate valid configurations
        valid_configs = ConfigurationGenerator.generate_valid_configurations(
            constraints, all_constrained_tiles
        )

        if not valid_configs:
            return {}

        # Layer 3: Calculate probabilities with global weighting
        return self._weight_and_calculate_probabilities(
            valid_configs, all_constrained_tiles
        )

    def _weight_and_calculate_probabilities(self, valid_configs, constrained_tiles):
        """
        Weight configurations by unconstrained possibilities and calculate probabilities.

        Uses log-space arithmetic from math_utilities to avoid overflow.
        """
        # Get global mine budget
        total_unknown = sum(1 for state in self.analyzer.get_all_values()
                          if state == AI_UNKNOWN)
        total_flagged = sum(1 for state in self.analyzer.get_all_values()
                          if state == AI_FLAGGED)
        remaining_mines = NUM_BOMBS - total_flagged
        unconstrained_count = total_unknown - len(constrained_tiles)

        # Calculate log-weights for each configuration
        log_weights = []
        config_data = []

        for config_info in valid_configs:
            mines_in_config = config_info['mine_count']
            mines_for_unconstrained = remaining_mines - mines_in_config

            # Weight = C(unconstrained_count, mines_for_unconstrained)
            log_weight = log_combinations(unconstrained_count, mines_for_unconstrained)

            if log_weight != float('-inf'):
                log_weights.append(log_weight)
                config_data.append(config_info)

        if not log_weights:
            return {}

        # Calculate total weight using logsumexp
        total_weight_log = logsumexp(log_weights)

        # Calculate weighted mine counts for each tile
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
                # Sum of weights where tile is mine
                mine_weight_log = logsumexp(tile_log_weights[tile])
                # Probability = mine_weight / total_weight
                probabilities[tile] = math.exp(mine_weight_log - total_weight_log)
            else:
                probabilities[tile] = 0.0

        return probabilities

    def _calculate_unconstrained_probability(self, constraints, constrained_probs):
        """
        Calculate weighted probability for unconstrained tiles.

        Args:
            constraints: List of constraints
            constrained_probs: Dict of probabilities for constrained tiles

        Returns:
            float: Weighted probability for an unconstrained tile
        """
        # Get all constrained tiles
        constrained_tiles = set()
        for constraint in constraints:
            constrained_tiles.update(constraint.get_constrained_tiles())

        # Generate configurations
        valid_configs = ConfigurationGenerator.generate_valid_configurations(
            constraints, constrained_tiles
        )

        if not valid_configs:
            return self._calculate_global_probability_value()

        # Get global counts
        total_unknown = sum(1 for state in self.analyzer.get_all_values()
                          if state == AI_UNKNOWN)
        total_flagged = sum(1 for state in self.analyzer.get_all_values()
                          if state == AI_FLAGGED)
        remaining_mines = NUM_BOMBS - total_flagged
        unconstrained_count = total_unknown - len(constrained_tiles)

        if unconstrained_count == 0:
            return 0.0

        # Calculate weighted average probability
        log_weights = []
        probs = []

        for config_info in valid_configs:
            mines_in_config = config_info['mine_count']
            mines_for_unconstrained = remaining_mines - mines_in_config

            log_weight = log_combinations(unconstrained_count, mines_for_unconstrained)

            if log_weight != float('-inf'):
                prob = mines_for_unconstrained / unconstrained_count
                log_weights.append(log_weight)
                probs.append(prob)

        if not log_weights:
            return self._calculate_global_probability_value()

        return weighted_average_in_log_space(log_weights, probs)

    def _calculate_global_probability_value(self):
        """Calculate simple global probability as a float value."""
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
        Calculate minimum distance from tile to any revealed tile.

        Args:
            tile: Coordinate tuple (x, y)

        Returns:
            int: Minimum Manhattan distance to frontier
        """
        min_distance = float('inf')

        for coord in self.analyzer.get_all_coordinates():
            state = self.analyzer.get_tile_state(coord)
            if state not in [AI_UNKNOWN, AI_FLAGGED]:
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
        probabilities = self.calculate_probabilities()

        if not probabilities or not isinstance(probabilities, dict):
            return (None, 1.0)

        # Find minimum probability
        min_prob = min(probabilities.values())

        # Get all tiles with minimum probability
        candidates = [(tile, prob) for tile, prob in probabilities.items()
                     if prob == min_prob]

        if len(candidates) == 1:
            return candidates[0]

        # Tie-breaking: prefer frontier tiles
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
