import pygame as py
from constants import *


class AIController:
    """Executes AI moves on the game board"""

    def movement(self, tile_coords, board, game_logic, right_click=False):
        if AI_CLICK_FEEDBACK:
            py.mouse.set_pos(tile_coords[0] * TILE_SIZE + (TILE_SIZE // 2),
                            tile_coords[1] * TILE_SIZE + (TILE_SIZE // 2))

        tile = board.get_tile(tile_coords)
        if not right_click:
            game_logic.reveal_tile(tile_coords)
        elif tile.state != STATE_FLAGGED:
            tile.plantFlag()
