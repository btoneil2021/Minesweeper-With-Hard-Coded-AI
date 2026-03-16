from collections.abc import Sequence

from minesweeper.domain.move import Move
from minesweeper.domain.tile import Tile
from minesweeper.domain.types import ActionType, Coord, TileState
from minesweeper.external.app import ExternalApp
from minesweeper.external.calibration import CalibrationResult
from minesweeper.external.capture import ScreenRegion, TileSize
from minesweeper.external.classifier import ColorProfiles
from minesweeper.external.grid import TileGrid


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

    def refresh(self) -> None:
        self.refresh_calls += 1
        if self._index < len(self._snapshots) - 1:
            self._index += 1
        self._current = self._snapshots[self._index]

    def tile_at(self, coord: Coord) -> Tile:
        return self._current[coord]


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

    app.run()

    assert analyzer.calls == 1
    assert empty_strategy.calls == 1
    assert reveal_strategy.calls == 1
    assert executor.batches == [[reveal_move]]
    assert sleeps == [0.4]


def test_external_app_retries_once_when_board_does_not_change() -> None:
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

    app.run()

    assert executor.batches == [[reveal_move], [reveal_move]]
    assert sleeps == [0.4, 0.8, 0.4]


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

    app.run()

    assert analyzer.calls == 0
    assert strategy.calls == 0
    assert executor.batches == []


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

    app.run()

    assert messages == [
        "External: refreshing board snapshot",
        "External: no moves available; stopping",
    ]


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

    app.run()

    assert messages == [
        "External: refreshing board snapshot",
        "External: using Reveal with 1 move",
        "External: board unchanged after move; retrying once",
        "External: refreshing board snapshot",
        "External: using Reveal with 1 move",
        "External: board unchanged after retry; stopping",
    ]


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

    app.run()

    assert messages == [
        "External: refreshing board snapshot",
        "External: board looks terminal; stopping",
    ]


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

    app.run()

    assert "External: using Reveal with 1 move" in messages


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
