import pygame as py
from constants import *
from .ui_bar import UIBar

class RenderManager:
    """Manages pygame rendering and display."""

    def __init__(self, screen_size, font_size=30):
        self.screen = py.display.set_mode(screen_size)
        self.font = py.font.Font(None, font_size)
        self.ui_bar = UIBar(screen_size[0], self.font)

    def render(self, board, win_rate: float, game_mode=None, ai_enabled=None):
        """Draw the UI bar and game board."""
        self.screen.fill(COLOR_WHITE)

        # Populate UI bar rows
        self.ui_bar.set_row_content(0, f"Win Rate: {win_rate:.2%}", alignment='left')

        if game_mode is not None:
            mode_text = self._get_mode_text(game_mode, ai_enabled)
            self.ui_bar.set_row_content(1, mode_text, alignment='left')

        # Row 2 is reserved for future use (left empty)

        # Render UI bar at top
        ui_bar_surface = self.ui_bar.render()
        self.screen.blit(ui_bar_surface, (0, 0))

        # Render board below UI bar
        board.draw(self.screen, y_offset=UI_BAR_HEIGHT)

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