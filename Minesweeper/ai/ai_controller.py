import pygame as py
from constants import *


class AIController:
    """Executes AI moves on the game board"""

    def movement(self, key, board, game_logic, right_click=False):
        """
        Execute a move at the given key position

        Args:
            key: Tuple (x, y) coordinates of the tile
            board: Board object
            game_logic: GameLogic object
            right_click: If True, flag the tile; if False, reveal it
        """
        if AI_CLICK_FEEDBACK:
            py.mouse.set_pos(key[0] * TILE_SIZE + (TILE_SIZE // 2),
                            key[1] * TILE_SIZE + (TILE_SIZE // 2))

        tile = board.get_tile(key)
        if not right_click:
            game_logic.reveal_tile(key)
        elif tile.state != STATE_FLAGGED:
            tile.plantFlag()
