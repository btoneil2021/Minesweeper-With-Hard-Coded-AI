import pygame as py
import math
from constants import *


class GameLogic:
    """Handles game rules and player interactions"""

    def __init__(self, board):
        self.board = board

    def click_action(self, action):
        """Handle mouse click actions on the board"""
        pos = py.mouse.get_pos()
        row = math.floor(pos[0] / TILE_SIZE)
        col = math.floor(pos[1] / TILE_SIZE)

        if action == "left":
            self.board.dictionary[str((row, col))].reveal()
            if self.board.dictionary[str((row, col))].val == 0:
                self.reveal_zeros((row, col))
        elif action == "right":
            self.board.dictionary[str((row, col))].plantFlag()

    def reveal_zeros(self, key):
        """Recursively reveal all connected zero-value tiles"""
        neighbors = self._get_neighbors(key)

        if str(key) not in self.board.dictionary or self.board.dictionary[str(key)].isBomb:
            return

        if self.board.dictionary[str(key)].val == 0:
            for neighbor in neighbors:
                if str(neighbor) in self.board.dictionary:
                    tile = self.board.dictionary[str(neighbor)]
                    if not tile.isBomb and tile.state != STATE_REVEALED:
                        tile.state = STATE_REVEALED
                        # Recursively reveal if the neighbor is also a zero
                        if tile.val == 0:
                            self.reveal_zeros(neighbor)

    def _get_neighbors(self, key):
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

    def is_lost(self):
        """Check if the game is lost (bomb revealed)"""
        for tile in self.board.dictionary.values():
            if tile.state == STATE_BOMB:
                return True
        return False

    def is_won(self):
        """Check if the game is won (all non-bombs revealed/flagged)"""
        for tile in self.board.dictionary.values():
            if tile.state not in [STATE_REVEALED, STATE_FLAGGED]:
                return False
        return True
