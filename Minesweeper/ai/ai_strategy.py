import random
from constants import *
from .board_analyzer import BoardAnalyzer
from .pattern_detector import PatternDetector
from .probability_calculator import ProbabilityCalculator


class AIStrategy:
    """High-level AI decision-making engine"""

    def __init__(self):
        self.analyzer = BoardAnalyzer()
        self.pattern_detector = PatternDetector(self.analyzer)
        self.probability_calculator = ProbabilityCalculator(self.analyzer)

    def first_moves(self):
        """Make random moves at the beginning of the game"""
        while True:
            for key in self.analyzer.copyDict.keys():
                if random.randint(0, AI_RANDOM_MOVE_RANGE) == AI_RANDOM_MOVE_PROBABILITY:
                    return key

    def decide_next_move(self, board):
        """
        Main AI logic - decides the next move to make
        Returns a tuple: (key, is_flag, can_be_evaluated)
        """
        can_be_evaluated = False
        self.analyzer.grab_board(board.dictionary)

        # At the beginning, make random moves
        if not self.analyzer.are_there_zeros():
            return (self.first_moves(), False, can_be_evaluated)

        can_be_evaluated = True

        # Phase 1: Flag obvious bombs
        for key in self.analyzer.copyDict.keys():
            if self.analyzer.copyDict[key] in [AI_FLAGGED, AI_UNKNOWN]:
                continue

            tiles_to_flag = self.pattern_detector.same_bombs_as_squares(key)
            if tiles_to_flag is not None:
                for flag_tile in tiles_to_flag:
                    if flag_tile in self.analyzer.copyDict:
                        if self.analyzer.copyDict[flag_tile] == AI_UNKNOWN:
                            return (flag_tile, True, can_be_evaluated)

        # Phase 2: Reveal obviously safe tiles
        for key in self.analyzer.copyDict.keys():
            if self.analyzer.copyDict[key] in [AI_FLAGGED, AI_UNKNOWN]:
                continue

            tiles_to_reveal = self.pattern_detector.all_bombs_found(key)
            if tiles_to_reveal is not None:
                for reveal_tile in tiles_to_reveal:
                    if reveal_tile in self.analyzer.copyDict:
                        if self.analyzer.copyDict[reveal_tile] == AI_UNKNOWN:
                            return (reveal_tile, False, can_be_evaluated)

        # Phase 3: Use advanced transitive property detection
        for key in self.analyzer.copyDict.keys():
            if self.analyzer.copyDict[key] in [AI_FLAGGED, AI_UNKNOWN]:
                continue

            result = self.pattern_detector.transitive_bomb_property(key=key)
            if result is not None and result in self.analyzer.copyDict:
                # Negative coordinates indicate a flag action
                if result[0] < 0 or result[1] < 0:
                    flag_pos = (-1 * result[0], -1 * result[1])
                    return (flag_pos, True, can_be_evaluated)
                else:
                    return (result, False, can_be_evaluated)

        # If no logical move found, return None to indicate we're stuck
        return (None, False, can_be_evaluated)
