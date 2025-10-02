from constants import *


class ProbabilityCalculator:
    """Calculates probabilities for making educated guesses"""

    def __init__(self, board_analyzer):
        self.analyzer = board_analyzer

    def calculate_probabilities(self, key):
        """
        Calculate the probability that a given tile is a bomb
        based on surrounding revealed tiles
        """
        full_prob = 0
        num_valued_tiles = 0

        for neighbor in self.analyzer.get_neighbors(key):
            if neighbor not in self.analyzer.copyDict:
                continue
            if self.analyzer.copyDict[neighbor] in [AI_FLAGGED, AI_UNKNOWN]:
                continue

            num_valued_tiles += 1

            # Analyze the value tile
            the_value = self.analyzer.copyDict[neighbor]
            bombs_left = the_value
            open_squares = 0

            for neighbor2 in self.analyzer.get_neighbors(neighbor):
                if neighbor2 not in self.analyzer.copyDict:
                    continue
                elif self.analyzer.copyDict[neighbor2] == AI_UNKNOWN:
                    open_squares += 1
                elif self.analyzer.copyDict[neighbor2] == AI_FLAGGED:
                    bombs_left -= 1

            if open_squares > 0:
                full_prob += bombs_left / open_squares

        if num_valued_tiles <= 2:
            return 1

        return full_prob / num_valued_tiles
