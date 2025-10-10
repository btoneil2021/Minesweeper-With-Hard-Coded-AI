import pygame as py
from constants import *


class GameLogic:
    """Handles game rules and player interactions"""

    def __init__(self, board):
        self.board = board

    def click_action(self, action):
        """Handle mouse click actions on the board"""
        pos = py.mouse.get_pos()
        coordinates = (pos[0] // TILE_SIZE, pos[1] // TILE_SIZE)
        tile = self.board.get_tile(coordinates)

        if action == "left":
            self.reveal_tile(coordinates)
        elif action == "right":
            tile.plantFlag()

    def reveal_tile(self, coordinates):
        """Reveal a tile and cascade if it's a zero-value tile"""
        tile = self.board.get_tile(coordinates)
        if not tile or tile.state != STATE_HIDDEN:
            return

        tile.set_revealed()

        if tile.val == 0:
            self._reveal_zeros(coordinates)

    def _reveal_zeros(self, coordinates):
        """Recursively reveal all connected zero-value tiles"""
        for neighbor in self.board.get_neighbors(coordinates):
            neighbor_tile = self.board.get_tile(neighbor)
            if not neighbor_tile or neighbor_tile.isBomb \
                   or neighbor_tile.state == STATE_REVEALED:
                continue

            neighbor_tile.set_revealed()
            if neighbor_tile.val == 0:
                self._reveal_zeros(neighbor)

    def is_lost(self):
        """Check if the game is lost (bomb revealed)"""
        for tile in self.board.dictionary.values():
            if tile.state == STATE_BOMB:
                return True
        return False

    def is_won(self):
        """Check if the game is won (all non-bombs revealed)"""
        for tile in self.board.dictionary.values():
            if not tile.isBomb and tile.state != STATE_REVEALED:
                return False
        return True
