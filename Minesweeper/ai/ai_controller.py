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
        # Move mouse to position for visual feedback
        py.mouse.set_pos(key[0] * TILE_SIZE + (TILE_SIZE // 2),
                        key[1] * TILE_SIZE + (TILE_SIZE // 2))

        if not right_click:
            # Left click - reveal tile
            board.dictionary[str(key)].reveal()
            if board.dictionary[str(key)].val == 0:
                game_logic.reveal_zeros(key)
        elif board.dictionary[str(key)].state != STATE_FLAGGED:
            # Right click - flag tile
            board.dictionary[str(key)].plantFlag()
