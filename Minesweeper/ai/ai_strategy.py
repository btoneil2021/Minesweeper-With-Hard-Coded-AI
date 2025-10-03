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

        if self._should_do_random_move():
            return self._random_move()
        else:
            self.performance_can_be_evaluated = True

        for coord in self.analyzer.get_all_coordinates():
            if self.analyzer.get_tile_state(coord) in [AI_FLAGGED, AI_UNKNOWN]:
                continue

            if (tile_and_action := self._safe_ai_moves(coord)) is not None:
                return tile_and_action

        return (None, False)
    
    def _should_do_random_move(self):
        if self.analyzer.zeros_are_uncovered():
            return False
        return True

    def _random_move(self):
        self.performance_can_be_evaluated = False
        
        coords = list(self.analyzer.get_all_coordinates())
        return (random.choice(coords), False)
                
    def _find_actionable_tile(self, potential_action_tiles, to_be_flagged=False):
        for tile in potential_action_tiles:
            if self.analyzer.has_tile(tile) \
                and self.analyzer.get_tile_state(tile) == AI_UNKNOWN:
                return (tile, to_be_flagged)
                
    def _obvious_bomb_tile_detection(self, tile_coord):
        if (tiles_to_flag := self.pattern_detector.same_bombs_as_squares(tile_coord)) is None:
            return None

        return self._find_actionable_tile(tiles_to_flag, to_be_flagged=True)
                
    def _safe_tile_detection(self, tile_coord):
        if (tiles_to_reveal := self.pattern_detector.all_bombs_found(tile_coord)) is None:
            return None

        return self._find_actionable_tile(tiles_to_reveal, to_be_flagged=False)
    
    def _transitive_detection(self, tile_coord):
        if (target_tile := self.pattern_detector.transitive_bomb_property(tile_coord)) is None \
            or not self.analyzer.has_tile(target_tile):
            return None

        # Negative coordinates indicate a flagging action
        if target_tile[0] < 0 or target_tile[1] < 0:
            flag_pos = (-1 * target_tile[0], -1 * target_tile[1])
            return (flag_pos, True)
        else:
            return (target_tile, False)
        
    def _safe_ai_moves(self, tile_coord):
        if (tile_and_action := self._obvious_bomb_tile_detection(tile_coord)) is not None:
            return tile_and_action

        if (tile_and_action := self._safe_tile_detection(tile_coord)) is not None:
            return tile_and_action

        if (tile_and_action := self._transitive_detection(tile_coord)) is not None:
            return tile_and_action