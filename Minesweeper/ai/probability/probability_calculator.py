from constants import *
from .constraint_collector import ConstraintCollector
from .configuration_emulator import ConfigurationEnumerator

class ProbabilityCalculator:
    def __init__(self, board_analyzer):
        self.analyzer = board_analyzer
        self.constraint_collector = ConstraintCollector(board_analyzer)

    def calculate_probabilities(self, target_tile=None):
        constraints = self.constraint_collector.collect_all_constraints()

        if not constraints:
            return self._calculate_global_probability(target_tile)

        constrained_tiles = self._get_all_constrained_tiles(constraints)

        if target_tile and target_tile not in constrained_tiles:
            return self._calculate_global_probability(target_tile)

        probabilities = self._calculate_constrained_probabilities(constraints)

        if not probabilities:
            return self._calculate_global_probability(target_tile)

        return probabilities.get(target_tile) if target_tile else probabilities

    def _get_all_constrained_tiles(self, constraints):
        constrained_tiles = set()
        for constraint in constraints:
            constrained_tiles.update(constraint.get_constrained_tiles())
        return constrained_tiles

    def _calculate_constrained_probabilities(self, constraints):
        mine_counts, total_valid = ConfigurationEnumerator.count_mine_occurrences(constraints)

        if total_valid == 0:
            return {}

        return {tile: count / total_valid for tile, count in mine_counts.items()}

    def _calculate_global_probability(self, target_tile=None):
        total_unknown = sum(1 for state in self.analyzer.get_all_values()
                          if state == AI_UNKNOWN)
        total_flagged = sum(1 for state in self.analyzer.get_all_values()
                          if state == AI_FLAGGED)

        if total_unknown == 0:
            return 0.0

        remaining_mines = NUM_BOMBS - total_flagged
        return remaining_mines / total_unknown