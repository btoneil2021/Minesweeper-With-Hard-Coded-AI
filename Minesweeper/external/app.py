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
from minesweeper.external.board_reader import ScreenBoardReader
from minesweeper.external.calibration import CalibrationResult
from minesweeper.external.capture import ScreenCapture
from minesweeper.external.classifier import TileClassifier
from minesweeper.external.executor import ScreenMoveExecutor


class ExternalApp:
    def __init__(
        self,
        calibration: CalibrationResult,
        settle_delay_ms: int = 400,
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
        )
        self._executor = executor or ScreenMoveExecutor(
            board_region=calibration.board_region,
            tile_size=calibration.tile_size,
            grid=calibration.grid,
        )
        self._analyzer = analyzer or Analyzer()
        self._rng = random.Random()
        self._strategies = list(strategies) if strategies is not None else [
            RandomExplorer(self._rng),
            PatternDetector(),
            ConstraintSubtractor(),
            TransitiveMatcher(),
            ProbabilitySolver(),
        ]

    def run(self) -> None:
        unchanged_after_move = 0
        while True:
            self._output("External: refreshing board snapshot")
            self._board_reader.refresh()
            if self._board_looks_terminal():
                self._output("External: board looks terminal; stopping")
                return

            analysis = self._analyzer.analyze(self._board_reader)
            moves = self._next_moves(analysis)
            if not moves:
                self._output("External: no moves available; stopping")
                return

            before = self._board_signature()
            self._executor.execute_batch(moves)
            self._sleep(self._settle_delay_seconds)

            self._board_reader.refresh()
            if self._board_looks_terminal():
                self._output("External: board looks terminal; stopping")
                return

            after = self._board_signature()
            if after == before:
                unchanged_after_move += 1
                if unchanged_after_move >= 2:
                    self._output("External: board unchanged after retry; stopping")
                    return
                self._output("External: board unchanged after move; retrying once")
                self._sleep(self._settle_delay_seconds * 2)
                continue

            unchanged_after_move = 0

    def _next_moves(self, analysis) -> Sequence[Move]:
        for strategy in self._strategies:
            if isinstance(strategy, RandomExplorer) and self._has_revealed_zero():
                continue

            moves = strategy.find_moves(analysis)
            if moves:
                move_count = len(moves)
                noun = "move" if move_count == 1 else "moves"
                self._output(f"External: using {strategy.name} with {move_count} {noun}")
                return moves

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
                    (tile.coord.x, tile.coord.y, tile.state.name, tile.adjacent_mines, tile.is_mine)
                )
        return tuple(signature)
