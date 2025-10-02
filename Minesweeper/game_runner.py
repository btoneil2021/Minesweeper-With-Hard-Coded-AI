import pygame as py
from constants import *
from game import Board, GameLogic, RenderManager, StatisticsTracker
from ai import AIStrategy, AIController

class GameRunner:
    """Manages the main game loop and orchestrates game components."""

    def __init__(self):
        self.board = None
        self.game_logic = None
        self.ai_strategy = None
        self.ai_controller = None
        self.renderer = None
        self.statistics = None
        self.running = False

    def _initialize_components(self):
        """Initialize pygame and all game components."""
        py.init()
        self.renderer = RenderManager(SCREEN_SIZE)
        self.statistics = StatisticsTracker()
        self.board = Board()
        self.game_logic = GameLogic(self.board)
        self.ai_strategy = AIStrategy()
        self.ai_controller = AIController()
        self.running = True

    def _handle_ai_turn(self):
        """Process AI decision and execute move."""
        key, is_flag, can_be_evaluated = self.ai_strategy.decide_next_move(self.board)
        self.statistics.mark_if_can_be_evaluated(can_be_evaluated)

        if key is not None:
            self.ai_controller.movement(key, self.board, self.game_logic, right_click=is_flag)

    def _handle_events(self):
        """Process pygame events."""
        for event in py.event.get():
            if event.type == py.QUIT:
                self.running = False
            elif event.type == py.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left Click
                    self.game_logic.click_action("left")
                elif event.button == 3:  # Right Click
                    self.game_logic.click_action("right")

    def _render(self):
        """Draw the game board and statistics."""
        win_rate = self.statistics.get_win_rate()
        self.renderer.render(self.board, win_rate)

    def _update_statistics(self, won: bool):
        """Update game statistics after a game ends."""
        self.statistics.update(won)

    def _reset_game(self):
        """Reset the game to a fresh state."""
        self.board = Board()
        self.game_logic = GameLogic(self.board)

    def _check_and_handle_game_end(self):
        """Check for win/loss conditions and handle game restart."""
        if self.game_logic.is_lost():
            py.time.delay(GAME_RESTART_DELAY)
            self._update_statistics(won=False)
            self._reset_game()
        elif self.game_logic.is_won():
            py.time.delay(GAME_RESTART_DELAY)
            self._update_statistics(won=True)
            self._reset_game()

    def run(self):
        """Main game loop."""
        self._initialize_components()

        while self.running:
            self._handle_ai_turn()
            self._handle_events()
            self._render()
            self._check_and_handle_game_end()

        py.quit()


def main():
    game = GameRunner()
    game.run()


if __name__ == "__main__":
    main()
