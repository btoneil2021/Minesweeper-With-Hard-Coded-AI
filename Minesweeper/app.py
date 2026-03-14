from __future__ import annotations

import random

import pygame

from minesweeper.ai.analyzer import Analyzer
from minesweeper.ai.strategy import AIStrategy
from minesweeper.ai.strategies.constraint_subtractor import ConstraintSubtractor
from minesweeper.ai.strategies.pattern_detector import PatternDetector
from minesweeper.ai.strategies.probability_solver import ProbabilitySolver
from minesweeper.ai.strategies.random_explorer import RandomExplorer
from minesweeper.ai.strategies.transitive_matcher import TransitiveMatcher
from minesweeper.domain.move import Move
from minesweeper.domain.types import (
    ActionType,
    AI_ONLY,
    Coord,
    GameConfig,
    GameMode,
    GamePhase,
    PLAYER_ONLY,
    TileState,
)
from minesweeper.engine.game import Game
from minesweeper.engine.stats import GameResult, StatsTracker
from minesweeper.ui.input import QuitEvent, StepAIEvent, TileClickEvent, ToggleAIEvent, poll_events
from minesweeper.ui.renderer import PygameRenderer


class App:
    def __init__(
        self,
        config: GameConfig | None = None,
        mode: GameMode = PLAYER_ONLY,
    ) -> None:
        self._config = config or GameConfig()
        self._mode = mode
        self._renderer = PygameRenderer(self._config)
        self._rng = random.Random()
        self._game = Game(self._config, self._rng)
        self._stats = StatsTracker()
        self._analyzer = Analyzer()
        self._strategies: list[AIStrategy] = [
            RandomExplorer(self._rng),
            PatternDetector(),
            ConstraintSubtractor(),
            TransitiveMatcher(),
            ProbabilitySolver(),
        ]
        self._ai_active = mode == AI_ONLY
        self._is_evaluable = False
        self._running = True

    def run(self) -> None:
        while self._running:
            step_ai = False
            for event in poll_events(self._mode, self._renderer):
                if isinstance(event, QuitEvent):
                    self._running = False
                elif isinstance(event, ToggleAIEvent):
                    self._ai_active = not self._ai_active
                elif isinstance(event, StepAIEvent):
                    step_ai = True
                elif isinstance(event, TileClickEvent):
                    self._handle_tile_click(event)

            if self._mode.ai_enabled and (self._ai_active or step_ai):
                self._run_ai_turn()

            self._renderer.render(
                self._game.board,
                self._stats.win_rate,
                self._mode,
                self._ai_active,
            )

            if self._game.phase in {GamePhase.WON, GamePhase.LOST}:
                self._record_and_reset()

        pygame.quit()

    def _handle_tile_click(self, event: TileClickEvent) -> None:
        move = Move(event.action, event.coord)
        if event.action == ActionType.FLAG:
            tile = self._game.board.tile_at(event.coord)
            if tile.state == TileState.FLAGGED:
                move = Move(ActionType.UNFLAG, event.coord)

        try:
            self._game.apply_move(move)
        except ValueError:
            return

    def _run_ai_turn(self) -> None:
        analysis = self._analyzer.analyze(self._game.board)
        for strategy in self._strategies:
            if isinstance(strategy, RandomExplorer) and self._has_revealed_zero():
                continue

            moves = strategy.find_moves(analysis)
            if not moves:
                continue

            if not isinstance(strategy, RandomExplorer):
                self._is_evaluable = True

            for move in moves:
                try:
                    self._game.apply_move(move)
                except ValueError:
                    return

                if self._config.ai_click_feedback:
                    pygame.time.delay(60)
            return

    def _has_revealed_zero(self) -> bool:
        for x in range(self._game.board.width):
            for y in range(self._game.board.height):
                tile = self._game.board.tile_at(Coord(x, y))
                if tile.state == TileState.REVEALED and tile.adjacent_mines == 0:
                    return True

        return False

    def _record_and_reset(self) -> None:
        self._stats.record(
            GameResult(
                won=self._game.phase == GamePhase.WON,
                is_evaluable=self._is_evaluable,
            )
        )
        pygame.time.delay(self._config.restart_delay_ms)
        self._game.reset(self._config)
        self._is_evaluable = False
        if self._mode == AI_ONLY:
            self._ai_active = True


__all__ = ["App", "GameConfig", "GameMode", "PLAYER_ONLY", "AI_ONLY"]
