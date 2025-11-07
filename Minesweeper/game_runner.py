import pygame as py
from constants import *
from game import Board, GameLogic, RenderManager, StatisticsTracker
from ai import AIStrategy, AIController

class GameRunner:
    """Manages the main game loop and orchestrates game components."""

    def __init__(self, game_mode=None):
        self.board = None
        self.game_logic = None
        self.ai_strategy = None
        self.ai_controller = None
        self.renderer = None
        self.statistics = None
        self.running = False
        self.game_mode = game_mode if game_mode is not None else GAME_MODE
        self.ai_enabled = True  # For hybrid mode - can be toggled

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
        key, is_flag = self.ai_strategy.decide_next_move(self.board)
        self.statistics.mark_if_can_be_evaluated(self.ai_strategy.performance_can_be_evaluated)

        if key is not None:
            self.ai_controller.movement(key, self.board, self.game_logic, right_click=is_flag)

    def _should_process_ai_turn(self):
        """Determine if AI should process a turn based on game mode."""
        if self.game_mode == MODE_AI_ONLY:
            return True
        elif self.game_mode == MODE_HYBRID:
            return self.ai_enabled
        return False

    def _should_allow_player_input(self):
        """Determine if player input should be accepted based on game mode."""
        return self.game_mode in [MODE_PLAYER_ONLY, MODE_HYBRID]

    def _handle_events(self):
        """Process pygame events."""
        for event in py.event.get():
            if event.type == py.MOUSEBUTTONDOWN and self._should_allow_player_input():
                if event.button == 1:  # Left Click
                    self.game_logic.click_action("left")
                elif event.button == 3:  # Right Click
                    self.game_logic.click_action("right")
            elif event.type == py.QUIT:
                self.running = False
            elif event.type == py.KEYDOWN and self.game_mode == MODE_HYBRID:
                self._handle_hybrid_keys(event.key)

    def _handle_hybrid_keys(self, key):
        """Handle keyboard controls for hybrid mode."""
        if key == py.K_SPACE:
            # Toggle AI on/off
            self.ai_enabled = not self.ai_enabled
        elif key == py.K_s:
            # Single AI step
            self._handle_ai_turn()

    def _render(self):
        """Draw the game board and statistics."""
        win_rate = self.statistics.get_win_rate()
        self.renderer.render(self.board, win_rate, self.game_mode, self.ai_enabled)

    def _update_statistics(self, won: bool):
        """Update game statistics after a game ends."""
        self.statistics.update(won)

    def _reset_game(self):
        """Reset the game to a fresh state."""
        self.board = Board()
        self.game_logic = GameLogic(self.board)

    def _check_and_handle_game_end(self):
        """Check for win/loss conditions and handle game restart."""
        if self.game_logic.is_lost() or self.game_logic.is_won():
            py.time.delay(GAME_RESTART_DELAY)
            self._update_statistics(won=self.game_logic.is_won())
            self._reset_game()

    def run(self):
        """Main game loop."""
        self._initialize_components()

        while self.running:
            if self._should_process_ai_turn():
                self._handle_ai_turn()
            self._handle_events()
            self._render()
            self._check_and_handle_game_end()

        py.quit()


def select_game_mode():
    """Prompt user to select game mode if not set in config."""
    print("\n=== MINESWEEPER GAME MODE SELECTION ===")
    print(f"0 - AI Only Mode (AI plays automatically)")
    print(f"1 - Player Only Mode (Manual play only)")
    print(f"2 - Hybrid Mode (Player + AI assistance)")
    print(f"\nCurrent default mode in config.py: {GAME_MODE}")
    print("\nPress Enter to use default, or type a mode number (0-2):")

    choice = input().strip()

    if choice == "":
        return GAME_MODE

    try:
        mode = int(choice)
        if mode in [MODE_AI_ONLY, MODE_PLAYER_ONLY, MODE_HYBRID]:
            return mode
        else:
            print(f"Invalid mode. Using default: {GAME_MODE}")
            return GAME_MODE
    except ValueError:
        print(f"Invalid input. Using default: {GAME_MODE}")
        return GAME_MODE


def main():
    mode = select_game_mode()
    game = GameRunner(game_mode=mode)

    # Print controls based on mode
    print(f"\n=== Starting Minesweeper in mode {mode} ===")
    if mode == MODE_PLAYER_ONLY:
        print("Controls: Left Click = Reveal, Right Click = Flag")
    elif mode == MODE_HYBRID:
        print("Controls: Left Click = Reveal, Right Click = Flag")
        print("          SPACE = Toggle AI On/Off, S = Single AI Step")

    game.run()


if __name__ == "__main__":
    main()
