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
        self.performance_can_be_evaluated = False

    def decide_next_move(self, board):
        """
        Main AI logic - decides the next move to make
        Returns a tuple: (coord, is_flag)
        """
        self.analyzer.grab_board(board.dictionary)

        if not self.analyzer.zeros_are_uncovered():
            self.performance_can_be_evaluated = False
            return (self._random_move(), False)

        self.performance_can_be_evaluated = True

        # Check all tiles for logical moves
        for coord in self.analyzer.get_all_coordinates():
            if self.analyzer.get_tile_state(coord) in [AI_FLAGGED, AI_UNKNOWN]:
                continue

            # Phase 1: Flag obvious bombs
            tiles_to_flag = self.pattern_detector.same_bombs_as_squares(coord)
            if tiles_to_flag is not None:
                for flag_tile in tiles_to_flag:
                    if self.analyzer.has_tile(flag_tile) and self.analyzer.get_tile_state(flag_tile) == AI_UNKNOWN:
                        return (flag_tile, True)

            # Phase 2: Reveal obviously safe tiles
            tiles_to_reveal = self.pattern_detector.all_bombs_found(coord)
            if tiles_to_reveal is not None:
                for reveal_tile in tiles_to_reveal:
                    if self.analyzer.has_tile(reveal_tile) and self.analyzer.get_tile_state(reveal_tile) == AI_UNKNOWN:
                        return (reveal_tile, False)

            # Phase 3: Use advanced transitive property detection
            if (result := self._transitive_detection(coord)) is not None:
                return result

        # If no logical move found, return None to indicate we're stuck
        return (None, False)
    
    def _random_move(self):
        while True:
            for tile_coord in self.analyzer.get_all_coordinates():
                if random.randint(0, AI_RANDOM_MOVE_RANGE) == AI_RANDOM_MOVE_PROBABILITY:
                    return tile_coord
    
    def _transitive_detection(self, coord):
        if (target_tile := self.pattern_detector.transitive_bomb_property(key=coord)) is None \
            or not self.analyzer.has_tile(target_tile):
            return None

        # Negative coordinates indicate a flagging action
        if target_tile[0] < 0 or target_tile[1] < 0:
            flag_pos = (-1 * target_tile[0], -1 * target_tile[1])
            return (flag_pos, True)
        else:
            return (target_tile, False)