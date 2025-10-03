import pygame as py
from constants import *

class RenderManager:
    """Manages pygame rendering and display."""

    def __init__(self, screen_size, font_size=30):
        self.screen = py.display.set_mode(screen_size)
        self.font = py.font.Font(None, font_size)

    def render(self, board, win_rate: float, game_mode=None, ai_enabled=None):
        """Draw the board and statistics."""
        self.screen.fill(COLOR_WHITE)
        board.draw(self.screen)

        # Display win rate
        text = self.font.render(f"Win Rate: {win_rate:.2%}", True, COLOR_BLACK)
        self.screen.blit(text, (5, 5))

        # Display game mode info
        if game_mode is not None:
            mode_text = self._get_mode_text(game_mode, ai_enabled)
            mode_surface = self.font.render(mode_text, True, COLOR_BLACK)
            self.screen.blit(mode_surface, (5, 40))

        py.display.update()

    def _get_mode_text(self, game_mode, ai_enabled):
        """Get display text for current game mode."""
        if game_mode == MODE_AI_ONLY:
            return "Mode: AI Only"
        elif game_mode == MODE_PLAYER_ONLY:
            return "Mode: Player Only"
        elif game_mode == MODE_HYBRID:
            ai_status = "ON" if ai_enabled else "OFF"
            return f"Mode: Hybrid | AI: {ai_status}"
        return "Mode: Unknown"