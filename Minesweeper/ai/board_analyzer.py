from constants import *
from game.neighbor_utils import NeighborUtils


class BoardAnalyzer(NeighborUtils):
    """Analyzes the board state and extracts visible information"""

    def __init__(self):
        self.ai_board_state = {}

    def grab_board(self, unknown_tiles):
        """
        Grabs the board in such a way that it cannot see anything but uncovered tiles
        -1 (AI_FLAGGED) is flagged, -2 (AI_UNKNOWN) is unknown
        """
        for coordinate in unknown_tiles.keys():
            tile = unknown_tiles[coordinate]
            if tile.state == STATE_REVEALED:
                self.ai_board_state[coordinate] = tile.val
            elif tile.state == STATE_FLAGGED:
                self.ai_board_state[coordinate] = AI_FLAGGED
            else:
                self.ai_board_state[coordinate] = AI_UNKNOWN

    def are_there_zeros(self):
        """Check if any revealed tiles have value 0"""
        for value in self.ai_board_state.values():
            if value == 0:
                return True
        return False
