import pygame as py
from constants import *

class RenderManager:
    """Manages pygame rendering and display."""

    def __init__(self, screen_size, font_size=30):
        self.screen = py.display.set_mode(screen_size)
        self.font = py.font.Font(None, font_size)

    def render(self, board, win_rate: float):
        """Draw the board and statistics."""
        self.screen.fill(COLOR_WHITE)
        board.draw(self.screen)

        # Display win rate
        text = self.font.render(str(win_rate), True, COLOR_BLACK)
        self.screen.blit(text, (0, 0))

        py.display.update()