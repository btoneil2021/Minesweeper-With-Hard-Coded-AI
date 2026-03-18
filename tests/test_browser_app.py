from __future__ import annotations

from collections.abc import Sequence

from minesweeper.ai.analyzer import Analyzer
from minesweeper.ai.strategy import AIStrategy
from minesweeper.external.browser.app import BrowserApp
from minesweeper.external.browser.bridge.server import BrowserBridgeServer
from minesweeper.external.browser.dom_executor import DomMoveExecutor
from minesweeper.external.browser.dom_reader import DomBoardReader
from minesweeper.external.browser.protocol import (
    BoardSnapshotPayload,
    MoveCommandPayload,
    MovePayload,
    TilePayload,
)
from minesweeper.domain.move import Move
from minesweeper.domain.tile import Tile
from minesweeper.domain.types import ActionType, Coord, TileState
from minesweeper.external.runtime import STOP_REASONS


class FakeDomReader:
    def __init__(self, num_mines: int = 1) -> None:
        self._snapshot: BoardSnapshotPayload | None = None
        self._tiles: dict[Coord, Tile] = {}
        self.width = 0
        self.height = 0
        self.num_mines = num_mines
        self.update_calls = 0

    def update_snapshot(self, snapshot: BoardSnapshotPayload) -> None:
        self.update_calls += 1
        self._snapshot = snapshot
        self.width = snapshot.width
        self.height = snapshot.height
        self._tiles = {
            Coord(tile.x, tile.y): self._tile_from_payload(tile)
            for tile in snapshot.tiles
        }
        if len(self._tiles) != snapshot.width * snapshot.height:
            raise ValueError("snapshot does not cover the full declared board")

    def tile_at(self, coord: Coord) -> Tile:
        if self._snapshot is None:
            raise KeyError(coord)
        if not (0 <= coord.x < self.width and 0 <= coord.y < self.height):
            raise KeyError(coord)
        return self._tiles[coord]

    def _tile_from_payload(self, payload: TilePayload) -> Tile:
        coord = Coord(payload.x, payload.y)
        if payload.state == "hidden":
            return Tile(coord=coord, state=TileState.HIDDEN, is_mine=False)
        if payload.state == "flagged":
            return Tile(coord=coord, state=TileState.FLAGGED, is_mine=False)
        if payload.state == "exploded":
            return Tile(coord=coord, state=TileState.EXPLODED, is_mine=True)
        if payload.state == "mine_revealed":
            return Tile(coord=coord, state=TileState.REVEALED, is_mine=True, adjacent_mines=0)
        return Tile(
            coord=coord,
            state=TileState.REVEALED,
            is_mine=False,
            adjacent_mines=payload.adjacent_mines or 0,
        )


class DelayedBridge(BrowserBridgeServer):
    def __init__(self, ready_after_calls: int, snapshot: BoardSnapshotPayload) -> None:
        super().__init__()
        self._ready_after_calls = ready_after_calls
        self._snapshot = snapshot
        self.latest_snapshot_calls = 0

    def latest_snapshot(self, session_id: str) -> BoardSnapshotPayload:
        self.latest_snapshot_calls += 1
        if self.latest_snapshot_calls < self._ready_after_calls:
            raise RuntimeError("snapshot not ready")
        return self._snapshot


class SequencedBridge(BrowserBridgeServer):
    def __init__(self, snapshots: Sequence[BoardSnapshotPayload]) -> None:
        super().__init__()
        self._snapshots = list(snapshots)
        self.latest_snapshot_calls = 0

    def latest_snapshot(self, session_id: str) -> BoardSnapshotPayload:
        self.latest_snapshot_calls += 1
        if not self._snapshots:
            raise RuntimeError("snapshot not ready")
        if len(self._snapshots) == 1:
            return self._snapshots[0]
        return self._snapshots.pop(0)


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


class RecordingAnalyzer(Analyzer):
    def __init__(self) -> None:
        self.calls = 0

    def analyze(self, board) -> object:  # type: ignore[override]
        self.calls += 1
        return super().analyze(board)


def snapshot(*tiles: TilePayload) -> BoardSnapshotPayload:
    width = max(tile.x for tile in tiles) + 1
    height = max(tile.y for tile in tiles) + 1
    return BoardSnapshotPayload(
        width=width,
        height=height,
        face_state="smile",
        tiles=tuple(tiles),
    )


def terminal_snapshot() -> BoardSnapshotPayload:
    return snapshot(
        TilePayload(x=0, y=0, state="revealed", adjacent_mines=0),
    )


def hidden_snapshot() -> BoardSnapshotPayload:
    return snapshot(
        TilePayload(x=0, y=0, state="hidden"),
    )


def test_browser_app_stops_when_board_is_terminal_before_analyzing() -> None:
    bridge = BrowserBridgeServer()
    session_id = "tab-123"
    bridge.register_session(session_id)
    bridge.receive_snapshot_message(session_id, terminal_snapshot().to_dict())

    reader = FakeDomReader()
    analyzer = RecordingAnalyzer()
    strategy = FakeStrategy("Never", [Move(ActionType.REVEAL, Coord(0, 0))])
    sent_commands: list[object] = []
    executor = DomMoveExecutor(session_id=session_id, send=sent_commands.append)

    app = BrowserApp(
        session_id=session_id,
        bridge=bridge,
        board_reader=reader,
        executor=executor,
        analyzer=analyzer,
        strategies=[strategy],
    )

    reason = app.run()

    assert reason == STOP_REASONS.terminal_board_detected
    assert analyzer.calls == 0
    assert strategy.calls == 0
    assert sent_commands == []
    assert reader.update_calls == 1


def test_browser_app_stops_when_no_moves_are_available() -> None:
    bridge = BrowserBridgeServer()
    session_id = "tab-123"
    bridge.register_session(session_id)
    bridge.receive_snapshot_message(session_id, hidden_snapshot().to_dict())

    reader = FakeDomReader()
    analyzer = RecordingAnalyzer()
    strategy = FakeStrategy("Empty", [])
    sent_commands: list[object] = []
    executor = DomMoveExecutor(session_id=session_id, send=sent_commands.append)

    app = BrowserApp(
        session_id=session_id,
        bridge=bridge,
        board_reader=reader,
        executor=executor,
        analyzer=analyzer,
        strategies=[strategy],
    )

    reason = app.run()

    assert reason == STOP_REASONS.no_moves_available
    assert analyzer.calls == 1
    assert strategy.calls == 1
    assert sent_commands == []
    assert reader.update_calls == 1


def test_browser_app_waits_for_initial_snapshot_before_starting() -> None:
    snapshot_payload = hidden_snapshot()
    bridge = DelayedBridge(ready_after_calls=5, snapshot=snapshot_payload)
    session_id = "tab-123"
    bridge.register_session(session_id)

    reader = FakeDomReader()
    analyzer = RecordingAnalyzer()
    strategy = FakeStrategy("Empty", [])
    sent_commands: list[object] = []
    sleep_calls: list[float] = []
    executor = DomMoveExecutor(session_id=session_id, send=sent_commands.append)

    app = BrowserApp(
        session_id=session_id,
        bridge=bridge,
        board_reader=reader,
        executor=executor,
        analyzer=analyzer,
        strategies=[strategy],
        startup_wait_ms=1000,
        refresh_poll_interval_ms=100,
        sleep=sleep_calls.append,
    )

    reason = app.run()

    assert reason == STOP_REASONS.no_moves_available
    assert bridge.latest_snapshot_calls == 5
    assert reader.update_calls == 1
    assert analyzer.calls == 1
    assert strategy.calls == 1
    assert sent_commands == []
    assert sleep_calls == [0.1, 0.1, 0.1, 0.1]


def test_browser_app_can_wait_indefinitely_for_initial_snapshot() -> None:
    snapshot_payload = hidden_snapshot()
    bridge = DelayedBridge(ready_after_calls=8, snapshot=snapshot_payload)
    session_id = "tab-123"
    bridge.register_session(session_id)

    reader = FakeDomReader()
    analyzer = RecordingAnalyzer()
    strategy = FakeStrategy("Empty", [])
    sent_commands: list[object] = []
    sleep_calls: list[float] = []
    executor = DomMoveExecutor(session_id=session_id, send=sent_commands.append)

    app = BrowserApp(
        session_id=session_id,
        bridge=bridge,
        board_reader=reader,
        executor=executor,
        analyzer=analyzer,
        strategies=[strategy],
        startup_wait_ms=None,
        refresh_poll_interval_ms=100,
        sleep=sleep_calls.append,
    )

    reason = app.run()

    assert reason == STOP_REASONS.no_moves_available
    assert bridge.latest_snapshot_calls == 8
    assert reader.update_calls == 1
    assert analyzer.calls == 1
    assert strategy.calls == 1
    assert sent_commands == []
    assert sleep_calls == [0.1] * 7


def test_browser_app_executes_moves_in_strategy_order_and_rechecks_terminal_board() -> None:
    bridge = BrowserBridgeServer()
    session_id = "tab-123"
    bridge.register_session(session_id)
    bridge.receive_snapshot_message(session_id, hidden_snapshot().to_dict())

    reader = FakeDomReader()
    analyzer = RecordingAnalyzer()
    empty_strategy = FakeStrategy("Empty", [])
    ordered_moves = [
        Move(ActionType.FLAG, Coord(0, 0)),
        Move(ActionType.REVEAL, Coord(0, 0)),
    ]
    ordering_strategy = FakeStrategy("Ordered", ordered_moves)
    sent_commands: list[object] = []

    def send(command: object) -> None:
        sent_commands.append(command)
        bridge.queue_command(session_id, command)  # type: ignore[arg-type]
        bridge.receive_snapshot_message(session_id, terminal_snapshot().to_dict())

    executor = DomMoveExecutor(session_id=session_id, send=send)

    app = BrowserApp(
        session_id=session_id,
        bridge=bridge,
        board_reader=reader,
        executor=executor,
        analyzer=analyzer,
        strategies=[empty_strategy, ordering_strategy],
    )

    reason = app.run()

    assert reason == STOP_REASONS.terminal_board_detected


def test_browser_app_waits_for_changed_snapshot_after_executing_moves() -> None:
    session_id = "tab-123"
    bridge = SequencedBridge(
        [
            hidden_snapshot(),
            hidden_snapshot(),
            hidden_snapshot(),
            terminal_snapshot(),
        ]
    )
    bridge.register_session(session_id)

    reader = FakeDomReader()
    analyzer = RecordingAnalyzer()
    strategy = FakeStrategy("Ordered", [Move(ActionType.REVEAL, Coord(0, 0))])
    sent_commands: list[object] = []
    sleep_calls: list[float] = []
    executor = DomMoveExecutor(session_id=session_id, send=sent_commands.append)

    app = BrowserApp(
        session_id=session_id,
        bridge=bridge,
        board_reader=reader,
        executor=executor,
        analyzer=analyzer,
        strategies=[strategy],
        refresh_poll_interval_ms=100,
        post_move_refresh_retries=3,
        sleep=sleep_calls.append,
    )

    reason = app.run()

    assert reason == STOP_REASONS.terminal_board_detected
    assert bridge.latest_snapshot_calls == 4
    assert sleep_calls == [0.1, 0.1]
    assert analyzer.calls == 1
    assert strategy.calls == 1
    assert reader.update_calls == 4
    assert sent_commands == [
        MoveCommandPayload(
            session_id=session_id,
            moves=(
                MovePayload(x=0, y=0, action="reveal"),
            ),
        )
    ]
