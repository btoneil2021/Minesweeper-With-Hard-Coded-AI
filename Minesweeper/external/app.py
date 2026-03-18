from __future__ import annotations

import random
import time
from collections.abc import Callable, Sequence
from pathlib import Path

from minesweeper.ai.analyzer import Analyzer
from minesweeper.ai.strategy import AIStrategy
from minesweeper.ai.strategies.constraint_subtractor import ConstraintSubtractor
from minesweeper.ai.strategies.pattern_detector import PatternDetector
from minesweeper.ai.strategies.probability_solver import ProbabilitySolver
from minesweeper.ai.strategies.random_explorer import RandomExplorer
from minesweeper.ai.strategies.transitive_matcher import TransitiveMatcher
from minesweeper.domain.move import Move
from minesweeper.domain.types import ActionType, Coord, TileState
from minesweeper.external.board_reader import ScreenBoardReader
from minesweeper.external.calibration import CalibrationResult
from minesweeper.external.capture import ScreenCapture
from minesweeper.external.classifier import TileClassifier
from minesweeper.external.errors import BoardReadError, ExecutionError
from minesweeper.external.executor import ScreenMoveExecutor
from minesweeper.external.runtime import STOP_REASONS


class ExternalApp:
    def __init__(
        self,
        calibration: CalibrationResult,
        settle_delay_ms: int = 400,
        click_delay_ms: int = 40,
        board_read_retries: int = 1,
        unchanged_board_retries: int = 1,
        debug_capture_dir: Path | None = None,
        capture: ScreenCapture | None = None,
        classifier: TileClassifier | None = None,
        board_reader: ScreenBoardReader | None = None,
        executor: ScreenMoveExecutor | None = None,
        analyzer: Analyzer | None = None,
        strategies: Sequence[AIStrategy] | None = None,
        sleep: Callable[[float], None] | None = None,
        output: Callable[[str], None] | None = None,
    ) -> None:
        self._calibration = calibration
        self._settle_delay_seconds = settle_delay_ms / 1000
        self._board_read_retries = board_read_retries
        self._unchanged_board_retries = unchanged_board_retries
        self._sleep = sleep or time.sleep
        self._output = output or (lambda _message: None)

        runtime_capture = capture or ScreenCapture()
        runtime_classifier = classifier or TileClassifier(calibration.profiles)
        self._board_reader = board_reader or ScreenBoardReader(
            capture=runtime_capture,
            classifier=runtime_classifier,
            board_region=calibration.board_region,
            tile_size=calibration.tile_size,
            width=calibration.width,
            height=calibration.height,
            num_mines=calibration.num_mines,
            grid=calibration.grid,
            debug_capture_dir=debug_capture_dir,
            output=self._output,
        )
        self._executor = executor or ScreenMoveExecutor(
            board_region=calibration.board_region,
            tile_size=calibration.tile_size,
            grid=calibration.grid,
            click_delay_ms=click_delay_ms,
            before_click=self._record_move_overlay,
        )
        self._analyzer = analyzer or Analyzer()
        self._batch_index = 0
        self._move_index = 0
        self._rng = random.Random()
        self._strategies = list(strategies) if strategies is not None else [
            RandomExplorer(self._rng),
            PatternDetector(),
            ConstraintSubtractor(),
            TransitiveMatcher(),
            ProbabilitySolver(),
        ]

    def run(self) -> str:
        while True:
            refresh_failure = self._refresh_with_retry()
            if refresh_failure is not None:
                return refresh_failure
            if self._board_looks_terminal():
                self._output("External: board looks terminal; stopping")
                return STOP_REASONS.terminal_board_detected

            analysis = self._analyzer.analyze(self._board_reader)
            moves = self._next_moves(analysis)
            if not moves:
                self._output("External: no moves available; stopping")
                return STOP_REASONS.no_moves_available

            before = self._board_signature()
            try:
                move_count = len(moves)
                noun = "move" if move_count == 1 else "moves"
                self._output(
                    f"External: executing batch {self._batch_index} with {move_count} {noun} before next refresh"
                )
                self._executor.execute_batch(moves)
                remember_moves = getattr(self._board_reader, "remember_moves", None)
                if callable(remember_moves):
                    remember_moves(moves)
                self._batch_index += 1
            except ExecutionError as exc:
                if str(exc) == STOP_REASONS.unsupported_move_type:
                    return STOP_REASONS.unsupported_move_type
                return STOP_REASONS.execution_failed
            self._sleep(self._settle_delay_seconds)

            refresh_failure = self._refresh_with_retry()
            if refresh_failure is not None:
                return refresh_failure
            if self._board_looks_terminal():
                self._output("External: board looks terminal; stopping")
                return STOP_REASONS.terminal_board_detected

            after = self._board_signature()
            if after == before:
                if self._unchanged_board_retries <= 0:
                    self._output("External: board unchanged after retry; stopping")
                    return STOP_REASONS.board_unchanged_after_retry

                for attempt in range(self._unchanged_board_retries):
                    self._output("External: board unchanged after move; retrying once")
                    self._sleep(self._settle_delay_seconds * 2)
                    refresh_failure = self._refresh_with_retry()
                    if refresh_failure is not None:
                        return refresh_failure
                    if self._board_looks_terminal():
                        self._output("External: board looks terminal; stopping")
                        return STOP_REASONS.terminal_board_detected
                    if self._board_signature() != before:
                        break
                    if attempt == self._unchanged_board_retries - 1:
                        self._output("External: board unchanged after retry; stopping")
                        return STOP_REASONS.board_unchanged_after_retry

    def _refresh_with_retry(self) -> str | None:
        self._output("External: refreshing board snapshot")
        try:
            self._board_reader.refresh()
            return None
        except BoardReadError:
            for attempt in range(self._board_read_retries):
                self._sleep(self._settle_delay_seconds)
                self._output("External: refreshing board snapshot")
                try:
                    self._board_reader.refresh()
                    return None
                except BoardReadError:
                    if attempt == self._board_read_retries - 1:
                        return STOP_REASONS.board_refresh_failed_after_retry
            return STOP_REASONS.board_refresh_failed_after_retry

    def _next_moves(self, analysis) -> Sequence[Move]:
        for strategy in self._strategies:
            if isinstance(strategy, RandomExplorer) and self._has_revealed_zero():
                continue

            moves = strategy.find_moves(analysis)
            moves = self._validated_moves(moves)
            moves = self._conservative_live_batch(moves)
            if moves:
                move_count = len(moves)
                noun = "move" if move_count == 1 else "moves"
                self._output(f"External: using {strategy.name} with {move_count} {noun}")
                return moves

        return []

    def _validated_moves(self, moves: Sequence[Move]) -> list[Move]:
        if not moves:
            return []

        actions_by_coord: dict[Coord, ActionType] = {}
        is_externally_resolved = getattr(self._board_reader, "is_externally_resolved", None)
        for move in moves:
            tile = self._board_reader.tile_at(move.coord)
            if tile.state != TileState.HIDDEN:
                return []
            if callable(is_externally_resolved) and is_externally_resolved(move.coord):
                return []
            previous_action = actions_by_coord.get(move.coord)
            if previous_action is not None and previous_action != move.action:
                return []
            actions_by_coord[move.coord] = move.action

        return list(moves)

    def _conservative_live_batch(self, moves: Sequence[Move]) -> list[Move]:
        if not moves:
            return []
        if any(move.action == ActionType.FLAG for move in moves):
            return [moves[0]]
        return list(moves)

    def _has_revealed_zero(self) -> bool:
        for x in range(self._board_reader.width):
            for y in range(self._board_reader.height):
                tile = self._board_reader.tile_at(Coord(x, y))
                if tile.state == TileState.REVEALED and tile.adjacent_mines == 0:
                    return True
        return False

    def _board_looks_terminal(self) -> bool:
        if self._has_exploded_tile():
            return True
        return self._all_tiles_resolved()

    def _has_exploded_tile(self) -> bool:
        for x in range(self._board_reader.width):
            for y in range(self._board_reader.height):
                if self._board_reader.tile_at(Coord(x, y)).state == TileState.EXPLODED:
                    return True
        return False

    def _all_tiles_resolved(self) -> bool:
        for x in range(self._board_reader.width):
            for y in range(self._board_reader.height):
                if self._board_reader.tile_at(Coord(x, y)).state == TileState.HIDDEN:
                    return False
        return True

    def _board_signature(self) -> tuple[tuple[int, int, str, int, bool], ...]:
        signature: list[tuple[int, int, str, int, bool]] = []
        for x in range(self._board_reader.width):
            for y in range(self._board_reader.height):
                tile = self._board_reader.tile_at(Coord(x, y))
                signature.append(
                    (tile.coord.x, tile.coord.y, tile.state.name, tile.adjacent_mines, tile.is_mine)
                )
        return tuple(signature)

    def _record_move_overlay(
        self,
        move: Move,
        x: int,
        y: int,
        move_index_in_batch: int,
        batch_size: int,
    ) -> None:
        self._output(
            f"External: batch {self._batch_index} move {move_index_in_batch + 1}/{batch_size} "
            f"{move.action.name.lower()} {move.coord} at screen ({x}, {y})"
        )
        self._board_reader.save_move_overlay(
            coord=move.coord,
            click_point=(x, y),
            label=f"{move.action.name} ({move.coord.x},{move.coord.y})",
            batch_index=self._batch_index,
            move_index=self._move_index,
            move_index_in_batch=move_index_in_batch,
            batch_size=batch_size,
        )
        self._move_index += 1
