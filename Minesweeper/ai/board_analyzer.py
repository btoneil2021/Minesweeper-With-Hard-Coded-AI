from constants import *


class BoardAnalyzer:
    """Analyzes the board state and extracts visible information"""

    def __init__(self):
        self.copyDict = {}

    def grab_board(self, board_dict):
        """
        Grabs the board in such a way that it cannot see anything but uncovered tiles
        -1 (AI_FLAGGED) is flagged, -2 (AI_UNKNOWN) is unknown
        """
        for key in board_dict.keys():
            tile = board_dict[key]
            if tile.state == STATE_REVEALED:
                self.copyDict[key] = tile.val
            elif tile.state == STATE_FLAGGED:
                self.copyDict[key] = AI_FLAGGED
            else:
                self.copyDict[key] = AI_UNKNOWN

    def are_there_zeros(self):
        """Check if any revealed tiles have value 0"""
        for value in self.copyDict.values():
            if value == 0:
                return True
        return False

    def get_neighbors(self, key):
        """Get all 8 neighboring coordinates for a given tile"""
        return [
            (key[0] + 1, key[1]),
            (key[0], key[1] + 1),
            (key[0] + 1, key[1] + 1),
            (key[0] - 1, key[1]),
            (key[0], key[1] - 1),
            (key[0] - 1, key[1] - 1),
            (key[0] - 1, key[1] + 1),
            (key[0] + 1, key[1] - 1)
        ]

    def get_cardinal_neighbors(self, key):
        """Get only the 4 cardinal direction neighbors"""
        return [
            (key[0] + 1, key[1]),
            (key[0] - 1, key[1]),
            (key[0], key[1] + 1),
            (key[0], key[1] - 1)
        ]
