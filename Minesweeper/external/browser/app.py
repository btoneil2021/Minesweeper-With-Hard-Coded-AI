from __future__ import annotations

import random
import time
from collections.abc import Callable, Sequence

from minesweeper.ai.analyzer import Analyzer
from minesweeper.ai.strategy import AIStrategy
from minesweeper.ai.strategies.constraint_subtractor import ConstraintSubtractor
from minesweeper.ai.strategies.pattern_detector import PatternDetector
from minesweeper.ai.strategies.probability_solver import ProbabilitySolver
from minesweeper.ai.strategies.random_explorer import RandomExplorer
from minesweeper.ai.strategies.transitive_matcher import TransitiveMatcher
from minesweeper.domain.move import Move
from minesweeper.domain.types import Coord, TileState
from minesweeper.external.browser.bridge.server import BrowserBridgeServer, BridgeError
from minesweeper.external.browser.dom_executor import DomMoveExecutor
from minesweeper.external.runtime import STOP_REASONS
from minesweeper.external.errors import ExecutionError


class BrowserApp:
    def __init__(
        self,
        session_id: str,
        bridge: BrowserBridgeServer,
        board_reader,
        executor: DomMoveExecutor,
        analyzer: Analyzer | None = None,
        strategies: Sequence[AIStrategy] | None = None,
        startup_wait_ms: int | None = None,
        refresh_poll_interval_ms: int = 250,
        post_move_refresh_retries: int = 8,
        sleep: Callable[[float], None] | None = None,
        output: Callable[[str], None] | None = None,
    ) -> None:
        self._session_id = session_id
        self._bridge = bridge
        self._board_reader = board_reader
        self._executor = executor
        self._analyzer = analyzer or Analyzer()
        self._startup_wait_seconds = None if startup_wait_ms is None else startup_wait_ms / 1000
        self._refresh_poll_interval_seconds = refresh_poll_interval_ms / 1000
        self._post_move_refresh_retries = post_move_refresh_retries
        self._sleep = sleep or time.sleep
        self._output = output or (lambda _message: None)
        self._rng = random.Random()
        self._snapshot_ready = False
        self._strategies = list(strategies) if strategies is not None else [
            RandomExplorer(self._rng),
            PatternDetector(),
            ConstraintSubtractor(),
            TransitiveMatcher(),
            ProbabilitySolver(),
        ]

    def run(self) -> str:
        while True:
            refresh_failure = self._refresh_from_bridge(allow_retry=not self._snapshot_ready)
            if refresh_failure is not None:
                return refresh_failure
            self._snapshot_ready = True
            if self._board_looks_terminal():
                self._output("Browser: board looks terminal; stopping")
                return STOP_REASONS.terminal_board_detected

            analysis = self._analyzer.analyze(self._board_reader)
            moves = self._next_moves(analysis)
            if not moves:
                self._output("Browser: no moves available; stopping")
                return STOP_REASONS.no_moves_available

            before = self._board_signature()
            try:
                self._output(
                    f"Browser: executing batch of {len(moves)} move"
                    f"{'' if len(moves) == 1 else 's'}"
                )
                self._executor.execute_batch(moves)
            except ExecutionError as exc:
                if str(exc) == STOP_REASONS.unsupported_move_type:
                    return STOP_REASONS.unsupported_move_type
                return STOP_REASONS.execution_failed

            refresh_failure = self._refresh_from_bridge(
                allow_retry=True,
                require_change_from=before,
                retry_count=self._post_move_refresh_retries + 1,
            )
            if refresh_failure is not None:
                return refresh_failure
            if self._board_looks_terminal():
                self._output("Browser: board looks terminal; stopping")
                return STOP_REASONS.terminal_board_detected

    def _refresh_from_bridge(
        self,
        allow_retry: bool = False,
        require_change_from: tuple[tuple[int, int, str, int, bool], ...] | None = None,
        retry_count: int | None = None,
    ) -> str | None:
        attempts: int | None = 1
        if allow_retry:
            if retry_count is not None:
                attempts = retry_count
            elif self._startup_wait_seconds is None:
                attempts = None
            else:
                attempts = max(
                    2,
                    int(self._startup_wait_seconds / self._refresh_poll_interval_seconds) + 1,
                )

        attempt = 0
        while attempts is None or attempt < attempts:
            try:
                snapshot = self._bridge.latest_snapshot(self._session_id)
                self._board_reader.update_snapshot(snapshot)
                if require_change_from is not None and self._board_signature() == require_change_from:
                    if attempts is not None and attempt == attempts - 1:
                        self._output("Browser: board unchanged after retry; stopping")
                        return STOP_REASONS.board_unchanged_after_retry
                    self._output("Browser: board unchanged after move; waiting for updated snapshot")
                    self._sleep(self._refresh_poll_interval_seconds)
                    attempt += 1
                    continue
                return None
            except (BridgeError, RuntimeError, ValueError):
                if attempts is not None and attempt == attempts - 1:
                    return STOP_REASONS.board_refresh_failed_after_retry
                if allow_retry:
                    self._sleep(self._refresh_poll_interval_seconds)
                attempt += 1
                continue
            attempt += 1
        return STOP_REASONS.board_refresh_failed_after_retry

    def _next_moves(self, analysis) -> Sequence[Move]:
        for strategy in self._strategies:
            if isinstance(strategy, RandomExplorer) and self._has_revealed_zero():
                continue

            moves = strategy.find_moves(analysis)
            if moves:
                self._output(
                    f"Browser: using {strategy.name} with {len(moves)} move"
                    f"{'' if len(moves) == 1 else 's'}"
                )
                return list(moves)

        return []

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
                    (x, y, tile.state.name, tile.adjacent_mines, tile.is_mine)
                )
        return tuple(signature)
