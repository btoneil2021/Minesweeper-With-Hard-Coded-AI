from collections.abc import Sequence

from minesweeper.domain.move import Move
from minesweeper.domain.tile import Tile
from minesweeper.domain.types import ActionType, Coord, TileState
from minesweeper.external.app import ExternalApp
from minesweeper.external.calibration import CalibrationResult
from minesweeper.external.capture import ScreenRegion, TileSize
from minesweeper.external.classifier import ColorProfiles
from minesweeper.external.errors import BoardReadError, ExecutionError
from minesweeper.external.grid import TileGrid
from minesweeper.external.runtime import STOP_REASONS


class FakeBoardReader:
    def __init__(
        self,
        snapshots: list[dict[Coord, Tile]],
        width: int = 1,
        height: int = 1,
        num_mines: int = 0,
    ) -> None:
        self._snapshots = snapshots
        self._index = -1
        self._current: dict[Coord, Tile] = {}
        self.width = width
        self.height = height
        self.num_mines = num_mines
        self.refresh_calls = 0
        self.remembered_batches: list[list[Move]] = []
        self.externally_resolved_coords: set[Coord] = set()

    def refresh(self) -> None:
        self.refresh_calls += 1
        if self._index < len(self._snapshots) - 1:
            self._index += 1
        self._current = self._snapshots[self._index]

    def tile_at(self, coord: Coord) -> Tile:
        return self._current[coord]

    def remember_moves(self, moves: Sequence[Move]) -> None:
        self.remembered_batches.append(list(moves))
        for move in moves:
            self.externally_resolved_coords.add(move.coord)

    def is_externally_resolved(self, coord: Coord) -> bool:
        return coord in self.externally_resolved_coords


class FailingBoardReader:
    def __init__(self, fail_times: int) -> None:
        self._remaining_failures = fail_times
        self.width = 1
        self.height = 1
        self.num_mines = 0
        self.refresh_calls = 0

    def refresh(self) -> None:
        self.refresh_calls += 1
        if self._remaining_failures > 0:
            self._remaining_failures -= 1
            raise BoardReadError("boom")

    def tile_at(self, coord: Coord) -> Tile:
        raise KeyError(coord)


class FakeAnalyzer:
    def __init__(self) -> None:
        self.calls = 0

    def analyze(self, board) -> str:
        self.calls += 1
        return f"analysis-{self.calls}"


class FakeStrategy:
    def __init__(self, name: str, moves: Sequence[Move]) -> None:
        self._name = name
        self._moves = list(moves)
        self.calls = 0

    @property
    def name(self) -> str:
        return self._name

    def find_moves(self, _analysis) -> Sequence[Move]:
        self.calls += 1
        return list(self._moves)


class RecordingExecutor:
    def __init__(self) -> None:
        self.batches: list[list[Move]] = []

    def execute_batch(self, moves: Sequence[Move]) -> None:
        self.batches.append(list(moves))


class FailingExecutor:
    def __init__(self, message: str) -> None:
        self._message = message

    def execute_batch(self, _moves: Sequence[Move]) -> None:
        raise ExecutionError(self._message)


def calibration() -> CalibrationResult:
    return CalibrationResult(
        board_region=ScreenRegion(0, 0, 10, 10),
        tile_size=TileSize(10, 10),
        width=1,
        height=1,
        num_mines=0,
        profiles=ColorProfiles(
            hidden_bg=(20, 20, 20),
            revealed_bg=(220, 220, 220),
            flagged_bg=None,
            number_colors={},
            mine_bg=None,
        ),
        grid=TileGrid(
            origin_left=0,
            origin_top=0,
            col_boundaries=(0, 10),
            row_boundaries=(0, 10),
        ),
    )


def test_external_app_refreshes_analyzes_and_executes_first_non_empty_strategy() -> None:
    hidden = {Coord(0, 0): Tile(Coord(0, 0), TileState.HIDDEN, False)}
    revealed = {Coord(0, 0): Tile(Coord(0, 0), TileState.REVEALED, False, 0)}
    board_reader = FakeBoardReader([hidden, revealed])
    analyzer = FakeAnalyzer()
    executor = RecordingExecutor()
    empty_strategy = FakeStrategy("Empty", [])
    reveal_move = Move(ActionType.REVEAL, Coord(0, 0))
    reveal_strategy = FakeStrategy("Reveal", [reveal_move])
    sleeps: list[float] = []

    app = ExternalApp(
        calibration(),
        board_reader=board_reader,
        analyzer=analyzer,
        executor=executor,
        strategies=[empty_strategy, reveal_strategy],
        sleep=lambda seconds: sleeps.append(seconds),
    )

    reason = app.run()

    assert analyzer.calls == 1
    assert empty_strategy.calls == 1
    assert reveal_strategy.calls == 1
    assert executor.batches == [[reveal_move]]
    assert sleeps == [0.4]
    assert reason == STOP_REASONS.terminal_board_detected


def test_external_app_retries_refresh_once_when_board_does_not_change() -> None:
    hidden = {Coord(0, 0): Tile(Coord(0, 0), TileState.HIDDEN, False)}
    board_reader = FakeBoardReader([hidden, hidden, hidden])
    executor = RecordingExecutor()
    reveal_move = Move(ActionType.REVEAL, Coord(0, 0))
    sleeps: list[float] = []

    app = ExternalApp(
        calibration(),
        board_reader=board_reader,
        analyzer=FakeAnalyzer(),
        executor=executor,
        strategies=[FakeStrategy("Reveal", [reveal_move])],
        sleep=lambda seconds: sleeps.append(seconds),
    )

    reason = app.run()

    assert executor.batches == [[reveal_move]]
    assert sleeps == [0.4, 0.8]
    assert reason == STOP_REASONS.board_unchanged_after_retry


def test_external_app_remembers_successfully_executed_flag_batches_for_future_refreshes() -> None:
    hidden = {Coord(0, 0): Tile(Coord(0, 0), TileState.HIDDEN, False)}
    board_reader = FakeBoardReader([hidden, hidden, hidden])
    executor = RecordingExecutor()
    flag_move = Move(ActionType.FLAG, Coord(0, 0))

    app = ExternalApp(
        calibration(),
        board_reader=board_reader,
        analyzer=FakeAnalyzer(),
        executor=executor,
        strategies=[FakeStrategy("Flag", [flag_move])],
        sleep=lambda _seconds: None,
    )

    reason = app.run()

    assert executor.batches == [[flag_move]]
    assert board_reader.remembered_batches == [[flag_move]]
    assert reason == STOP_REASONS.board_unchanged_after_retry


def test_external_app_stops_when_board_looks_complete() -> None:
    complete = {Coord(0, 0): Tile(Coord(0, 0), TileState.REVEALED, False, 0)}
    board_reader = FakeBoardReader([complete])
    analyzer = FakeAnalyzer()
    executor = RecordingExecutor()
    strategy = FakeStrategy("ShouldNotRun", [Move(ActionType.REVEAL, Coord(0, 0))])

    app = ExternalApp(
        calibration(),
        board_reader=board_reader,
        analyzer=analyzer,
        executor=executor,
        strategies=[strategy],
    )

    reason = app.run()

    assert analyzer.calls == 0
    assert strategy.calls == 0
    assert executor.batches == []
    assert reason == STOP_REASONS.terminal_board_detected


def test_external_app_logs_no_moves_stop_when_output_is_enabled() -> None:
    hidden = {Coord(0, 0): Tile(Coord(0, 0), TileState.HIDDEN, False)}
    board_reader = FakeBoardReader([hidden])
    messages: list[str] = []

    app = ExternalApp(
        calibration(),
        board_reader=board_reader,
        analyzer=FakeAnalyzer(),
        executor=RecordingExecutor(),
        strategies=[FakeStrategy("Empty", [])],
        output=lambda message: messages.append(message),
    )

    reason = app.run()

    assert messages == [
        "External: refreshing board snapshot",
        "External: no moves available; stopping",
    ]
    assert reason == STOP_REASONS.no_moves_available


def test_external_app_logs_unchanged_board_retry_and_stop() -> None:
    hidden = {Coord(0, 0): Tile(Coord(0, 0), TileState.HIDDEN, False)}
    board_reader = FakeBoardReader([hidden, hidden, hidden])
    reveal_move = Move(ActionType.REVEAL, Coord(0, 0))
    messages: list[str] = []

    app = ExternalApp(
        calibration(),
        board_reader=board_reader,
        analyzer=FakeAnalyzer(),
        executor=RecordingExecutor(),
        strategies=[FakeStrategy("Reveal", [reveal_move])],
        sleep=lambda _seconds: None,
        output=lambda message: messages.append(message),
    )

    reason = app.run()

    assert messages == [
        "External: refreshing board snapshot",
        "External: using Reveal with 1 move",
        "External: executing batch 0 with 1 move before next refresh",
        "External: refreshing board snapshot",
        "External: board unchanged after move; retrying once",
        "External: refreshing board snapshot",
        "External: board unchanged after retry; stopping",
    ]
    assert reason == STOP_REASONS.board_unchanged_after_retry


def test_external_app_logs_terminal_stop() -> None:
    complete = {Coord(0, 0): Tile(Coord(0, 0), TileState.REVEALED, False, 0)}
    board_reader = FakeBoardReader([complete])
    messages: list[str] = []

    app = ExternalApp(
        calibration(),
        board_reader=board_reader,
        analyzer=FakeAnalyzer(),
        executor=RecordingExecutor(),
        strategies=[FakeStrategy("Unused", [])],
        output=lambda message: messages.append(message),
    )

    reason = app.run()

    assert messages == [
        "External: refreshing board snapshot",
        "External: board looks terminal; stopping",
    ]
    assert reason == STOP_REASONS.terminal_board_detected


def test_external_app_logs_strategy_name_and_move_count() -> None:
    hidden = {Coord(0, 0): Tile(Coord(0, 0), TileState.HIDDEN, False)}
    revealed = {Coord(0, 0): Tile(Coord(0, 0), TileState.REVEALED, False, 0)}
    board_reader = FakeBoardReader([hidden, revealed])
    messages: list[str] = []
    reveal_move = Move(ActionType.REVEAL, Coord(0, 0))

    app = ExternalApp(
        calibration(),
        board_reader=board_reader,
        analyzer=FakeAnalyzer(),
        executor=RecordingExecutor(),
        strategies=[FakeStrategy("Reveal", [reveal_move])],
        sleep=lambda _seconds: None,
        output=lambda message: messages.append(message),
    )

    reason = app.run()

    assert "External: using Reveal with 1 move" in messages
    assert "External: executing batch 0 with 1 move before next refresh" in messages
    assert reason == STOP_REASONS.terminal_board_detected


def test_external_app_logs_batch_size_before_refresh() -> None:
    hidden = {
        Coord(0, 0): Tile(Coord(0, 0), TileState.HIDDEN, False),
        Coord(0, 1): Tile(Coord(0, 1), TileState.HIDDEN, False),
    }
    revealed = {
        Coord(0, 0): Tile(Coord(0, 0), TileState.REVEALED, False, 0),
        Coord(0, 1): Tile(Coord(0, 1), TileState.FLAGGED, False),
    }
    board_reader = FakeBoardReader([hidden, revealed], width=1, height=2)
    messages: list[str] = []
    moves = [
        Move(ActionType.REVEAL, Coord(0, 0)),
        Move(ActionType.FLAG, Coord(0, 1)),
    ]

    app = ExternalApp(
        calibration(),
        board_reader=board_reader,
        analyzer=FakeAnalyzer(),
        executor=RecordingExecutor(),
        strategies=[FakeStrategy("Reveal", moves)],
        sleep=lambda _seconds: None,
        output=lambda message: messages.append(message),
    )

    app.run()

    assert "External: executing batch 0 with 1 move before next refresh" in messages


def test_external_app_limits_flag_batches_to_one_live_move_before_refresh() -> None:
    hidden = {
        Coord(0, 0): Tile(Coord(0, 0), TileState.HIDDEN, False),
        Coord(0, 1): Tile(Coord(0, 1), TileState.HIDDEN, False),
        Coord(0, 2): Tile(Coord(0, 2), TileState.HIDDEN, False),
    }
    progressed = {
        Coord(0, 0): Tile(Coord(0, 0), TileState.FLAGGED, False),
        Coord(0, 1): Tile(Coord(0, 1), TileState.HIDDEN, False),
        Coord(0, 2): Tile(Coord(0, 2), TileState.HIDDEN, False),
    }
    board_reader = FakeBoardReader([hidden, progressed], width=1, height=3)
    executor = RecordingExecutor()
    moves = [
        Move(ActionType.FLAG, Coord(0, 0)),
        Move(ActionType.FLAG, Coord(0, 1)),
        Move(ActionType.FLAG, Coord(0, 2)),
    ]

    app = ExternalApp(
        calibration(),
        board_reader=board_reader,
        analyzer=FakeAnalyzer(),
        executor=executor,
        strategies=[FakeStrategy("Flags", moves)],
        sleep=lambda _seconds: None,
    )

    reason = app.run()

    assert executor.batches == [[Move(ActionType.FLAG, Coord(0, 0))]]
    assert board_reader.remembered_batches == [[Move(ActionType.FLAG, Coord(0, 0))]]
    assert reason == STOP_REASONS.no_moves_available


def test_external_app_skips_strategy_with_conflicting_actions_for_same_coord() -> None:
    hidden = {
        Coord(0, 0): Tile(Coord(0, 0), TileState.HIDDEN, False),
        Coord(0, 1): Tile(Coord(0, 1), TileState.HIDDEN, False),
    }
    progressed = {
        Coord(0, 0): Tile(Coord(0, 0), TileState.REVEALED, False, 0),
        Coord(0, 1): Tile(Coord(0, 1), TileState.REVEALED, False, 0),
    }
    board_reader = FakeBoardReader([hidden, progressed], width=1, height=2)
    executor = RecordingExecutor()
    bad_strategy = FakeStrategy(
        "Bad",
        [
            Move(ActionType.FLAG, Coord(0, 0)),
            Move(ActionType.REVEAL, Coord(0, 0)),
        ],
    )
    good_strategy = FakeStrategy(
        "Good",
        [Move(ActionType.REVEAL, Coord(0, 1))],
    )

    app = ExternalApp(
        calibration(),
        board_reader=board_reader,
        analyzer=FakeAnalyzer(),
        executor=executor,
        strategies=[bad_strategy, good_strategy],
        sleep=lambda _seconds: None,
    )

    reason = app.run()

    assert bad_strategy.calls == 1
    assert good_strategy.calls == 1
    assert executor.batches == [[Move(ActionType.REVEAL, Coord(0, 1))]]
    assert reason == STOP_REASONS.terminal_board_detected


def test_external_app_skips_strategy_moves_that_target_non_hidden_tiles() -> None:
    hidden = {
        Coord(0, 0): Tile(Coord(0, 0), TileState.REVEALED, False, 1),
        Coord(0, 1): Tile(Coord(0, 1), TileState.HIDDEN, False),
    }
    progressed = {
        Coord(0, 0): Tile(Coord(0, 0), TileState.REVEALED, False, 1),
        Coord(0, 1): Tile(Coord(0, 1), TileState.REVEALED, False, 0),
    }
    board_reader = FakeBoardReader([hidden, progressed], width=1, height=2)
    executor = RecordingExecutor()
    stale_strategy = FakeStrategy(
        "Stale",
        [Move(ActionType.FLAG, Coord(0, 0))],
    )
    good_strategy = FakeStrategy(
        "Good",
        [Move(ActionType.REVEAL, Coord(0, 1))],
    )

    app = ExternalApp(
        calibration(),
        board_reader=board_reader,
        analyzer=FakeAnalyzer(),
        executor=executor,
        strategies=[stale_strategy, good_strategy],
        sleep=lambda _seconds: None,
    )

    reason = app.run()

    assert stale_strategy.calls == 1
    assert good_strategy.calls == 1
    assert executor.batches == [[Move(ActionType.REVEAL, Coord(0, 1))]]
    assert reason == STOP_REASONS.terminal_board_detected


def test_external_app_skips_repeated_reveals_for_coords_already_clicked_live() -> None:
    hidden = {
        Coord(0, 0): Tile(Coord(0, 0), TileState.HIDDEN, False),
        Coord(0, 1): Tile(Coord(0, 1), TileState.HIDDEN, False),
    }
    changed_elsewhere = {
        Coord(0, 0): Tile(Coord(0, 0), TileState.HIDDEN, False),
        Coord(0, 1): Tile(Coord(0, 1), TileState.REVEALED, False, 0),
    }
    board_reader = FakeBoardReader([hidden, changed_elsewhere], width=1, height=2)
    executor = RecordingExecutor()
    first_strategy = FakeStrategy(
        "First",
        [Move(ActionType.REVEAL, Coord(0, 0))],
    )
    repeated_strategy = FakeStrategy(
        "Repeated",
        [Move(ActionType.REVEAL, Coord(0, 0))],
    )

    app = ExternalApp(
        calibration(),
        board_reader=board_reader,
        analyzer=FakeAnalyzer(),
        executor=executor,
        strategies=[first_strategy, repeated_strategy],
        sleep=lambda _seconds: None,
    )

    reason = app.run()

    assert executor.batches == [[Move(ActionType.REVEAL, Coord(0, 0))]]
    assert board_reader.remembered_batches == [[Move(ActionType.REVEAL, Coord(0, 0))]]
    assert reason == STOP_REASONS.no_moves_available


def test_external_app_returns_refresh_failure_stop_after_one_retry() -> None:
    board_reader = FailingBoardReader(fail_times=2)
    sleeps: list[float] = []

    app = ExternalApp(
        calibration(),
        board_reader=board_reader,
        analyzer=FakeAnalyzer(),
        executor=RecordingExecutor(),
        strategies=[FakeStrategy("Unused", [])],
        sleep=lambda seconds: sleeps.append(seconds),
    )

    reason = app.run()

    assert reason == STOP_REASONS.board_refresh_failed_after_retry
    assert board_reader.refresh_calls == 2
    assert sleeps == [0.4]


def test_external_app_respects_zero_board_read_retries() -> None:
    board_reader = FailingBoardReader(fail_times=1)
    sleeps: list[float] = []

    app = ExternalApp(
        calibration(),
        board_reader=board_reader,
        analyzer=FakeAnalyzer(),
        executor=RecordingExecutor(),
        strategies=[FakeStrategy("Unused", [])],
        sleep=lambda seconds: sleeps.append(seconds),
        board_read_retries=0,
    )

    reason = app.run()

    assert reason == STOP_REASONS.board_refresh_failed_after_retry
    assert board_reader.refresh_calls == 1
    assert sleeps == []


def test_external_app_returns_unsupported_move_type_stop_reason() -> None:
    hidden = {Coord(0, 0): Tile(Coord(0, 0), TileState.HIDDEN, False)}
    app = ExternalApp(
        calibration(),
        board_reader=FakeBoardReader([hidden]),
        analyzer=FakeAnalyzer(),
        executor=FailingExecutor("unsupported move type"),
        strategies=[FakeStrategy("Reveal", [Move(ActionType.REVEAL, Coord(0, 0))])],
        sleep=lambda _seconds: None,
    )

    reason = app.run()

    assert reason == STOP_REASONS.unsupported_move_type


def test_external_app_returns_execution_failed_stop_reason() -> None:
    hidden = {Coord(0, 0): Tile(Coord(0, 0), TileState.HIDDEN, False)}
    app = ExternalApp(
        calibration(),
        board_reader=FakeBoardReader([hidden]),
        analyzer=FakeAnalyzer(),
        executor=FailingExecutor("mouse click failed"),
        strategies=[FakeStrategy("Reveal", [Move(ActionType.REVEAL, Coord(0, 0))])],
        sleep=lambda _seconds: None,
    )

    reason = app.run()

    assert reason == STOP_REASONS.execution_failed


def test_external_app_passes_calibration_grid_to_default_runtime_components(monkeypatch) -> None:
    board_reader_kwargs: dict[str, object] = {}
    executor_kwargs: dict[str, object] = {}
    calibration_result = calibration()

    class RecordingBoardReader:
        def __init__(self, **kwargs: object) -> None:
            board_reader_kwargs.update(kwargs)

        width = 1
        height = 1
        num_mines = 0

        def refresh(self) -> None:
            return None

        def tile_at(self, coord: Coord) -> Tile:
            return Tile(coord=coord, state=TileState.REVEALED, is_mine=False, adjacent_mines=0)

    class RecordingMoveExecutor:
        def __init__(self, **kwargs: object) -> None:
            executor_kwargs.update(kwargs)

        def execute_batch(self, moves: Sequence[Move]) -> None:
            return None

    monkeypatch.setattr("minesweeper.external.app.ScreenBoardReader", RecordingBoardReader)
    monkeypatch.setattr("minesweeper.external.app.ScreenMoveExecutor", RecordingMoveExecutor)

    ExternalApp(
        calibration_result,
        capture=object(),
        classifier=object(),
        analyzer=FakeAnalyzer(),
        strategies=[],
    )

    assert board_reader_kwargs["grid"] == calibration_result.grid
    assert executor_kwargs["grid"] == calibration_result.grid
