from constants import *
from game.neighbor_utils import NeighborUtils


class BoardAnalyzer(NeighborUtils):
    """Analyzes the board state and extracts visible information"""

    def __init__(self):
        self._ai_board_state = {}

    def grab_board(self, unknown_tiles):
        """
        Grabs the board in such a way that it cannot see anything but uncovered tiles
        -1 (AI_FLAGGED) is flagged, -2 (AI_UNKNOWN) is unknown
        """
        for coordinate in unknown_tiles.keys():
            tile = unknown_tiles[coordinate]
            if tile.state == STATE_REVEALED:
                self._ai_board_state[coordinate] = tile.val
            elif tile.state == STATE_FLAGGED:
                self._ai_board_state[coordinate] = AI_FLAGGED
            else:
                self._ai_board_state[coordinate] = AI_UNKNOWN

    def zeros_are_uncovered(self):
        """Check if any revealed tiles have value 0"""
        for value in self._ai_board_state.values():
            if value == 0:
                return True
        return False

    def get_tile_state(self, coordinate):
        """Get the state of a specific tile coordinate"""
        return self._ai_board_state.get(coordinate)

    def has_tile(self, coordinate):
        """Check if a coordinate exists in the board state"""
        return coordinate in self._ai_board_state

    def get_all_coordinates(self):
        """Get all tile coordinates"""
        return self._ai_board_state.keys()

    def get_all_values(self):
        """Get all tile values"""
        return self._ai_board_state.values()
