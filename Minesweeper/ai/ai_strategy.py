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

    def decide_next_move(self, board):
        """
        Main AI logic - decides the next move to make
        Returns a tuple: (coord, is_flag, can_be_evaluated)
        """
        self.analyzer.grab_board(board.dictionary)

        if not self.analyzer.zeros_are_uncovered():
            return (self._random_move(), False, False)

        # Phase 1: Flag obvious bombs
        for coord in self.analyzer.get_all_coordinates():
            if self.analyzer.get_tile_state(coord) in [AI_FLAGGED, AI_UNKNOWN]:
                continue

            tiles_to_flag = self.pattern_detector.same_bombs_as_squares(coord)

            if tiles_to_flag is None:
                continue

            for flag_tile in tiles_to_flag:
                if not self.analyzer.has_tile(flag_tile):
                    continue

                if self.analyzer.get_tile_state(flag_tile) == AI_UNKNOWN:
                    return (flag_tile, True, True)

        # Phase 2: Reveal obviously safe tiles
        for coord in self.analyzer.get_all_coordinates():
            if self.analyzer.get_tile_state(coord) in [AI_FLAGGED, AI_UNKNOWN]:
                continue

            tiles_to_reveal = self.pattern_detector.all_bombs_found(coord)
            if tiles_to_reveal is None:
                continue

            for reveal_tile in tiles_to_reveal:
                if not self.analyzer.has_tile(reveal_tile):
                    continue
                    
                if self.analyzer.get_tile_state(reveal_tile) == AI_UNKNOWN:
                    return (reveal_tile, False, True)

        # Phase 3: Use advanced transitive property detection
        for coord in self.analyzer.get_all_coordinates():
            result = self._transitive_detection(coord)
            if result is not None:
                return result

        # If no logical move found, return None to indicate we're stuck
        return (None, False, True)
    
    def _random_move(self):
        while True:
            for tile_coord in self.analyzer.get_all_coordinates():
                if random.randint(0, AI_RANDOM_MOVE_RANGE) == AI_RANDOM_MOVE_PROBABILITY:
                    return tile_coord
    
    def _transitive_detection(self, coord):
        if self.analyzer.get_tile_state(coord) in [AI_FLAGGED, AI_UNKNOWN]:
            return None

        result = self.pattern_detector.transitive_bomb_property(key=coord)
        if result is None or not self.analyzer.has_tile(result):
            return None
        
        # Negative coordinates indicate a flag action
        if result[0] < 0 or result[1] < 0:
            flag_pos = (-1 * result[0], -1 * result[1])
            return (flag_pos, True, True)
        else:
            return (result, False, True)