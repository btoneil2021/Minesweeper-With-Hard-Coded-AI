from __future__ import annotations

import minesweeper.app as app_module
from minesweeper.ai.analyzer import AnalyzedBoard
from minesweeper.domain.move import Move
from minesweeper.domain.tile import Tile
from minesweeper.domain.types import (
    ActionType,
    Coord,
    GameConfig,
    GamePhase,
    PLAYER_ONLY,
    TileState,
)


class StubBoard:
    def __init__(self, width: int, height: int, num_mines: int, tiles: list[Tile]) -> None:
        self.width = width
        self.height = height
        self.num_mines = num_mines
        self._tiles = {tile.coord: tile for tile in tiles}

    def tile_at(self, coord: Coord) -> Tile:
        return self._tiles[coord]


class StubGame:
    def __init__(self, board: StubBoard, reset_board: StubBoard, phase: GamePhase) -> None:
        self.board = board
        self._reset_board = reset_board
        self.phase = phase
        self.reset_calls = 0

    def reset(self, config: GameConfig) -> None:
        self.reset_calls += 1
        self.board = self._reset_board
        self.phase = GamePhase.NOT_STARTED


class RecordingRenderer:
    def __init__(self) -> None:
        self.rendered_states: list[dict[Coord, TileState]] = []

    def render(self, board: StubBoard, win_rate: float, mode: object, ai_active: bool) -> None:
        self.rendered_states.append(
            {
                Coord(x, y): board.tile_at(Coord(x, y)).state
                for x in range(board.width)
                for y in range(board.height)
            }
        )

    def board_coord_from_screen(self, screen_x: int, screen_y: int) -> Coord | None:
        return None


class RecordingMoveGame:
    def __init__(self) -> None:
        self.board = object()
        self.phase = GamePhase.IN_PROGRESS
        self.applied_moves: list[Move] = []

    def apply_move(self, move: Move) -> list[Coord]:
        self.applied_moves.append(move)
        return [move.coord]


class StubAnalyzer:
    def __init__(self, analysis: AnalyzedBoard) -> None:
        self._analysis = analysis

    def analyze(self, board: object) -> AnalyzedBoard:
        return self._analysis


class StubBatchStrategy:
    def __init__(self, moves: list[Move]) -> None:
        self._moves = moves
        self.calls = 0

    @property
    def name(self) -> str:
        return "StubBatchStrategy"

    def find_moves(self, analysis: AnalyzedBoard) -> list[Move]:
        self.calls += 1
        return self._moves


class FailingStrategy:
    calls = 0

    @property
    def name(self) -> str:
        return "FailingStrategy"

    def find_moves(self, analysis: AnalyzedBoard) -> list[Move]:
        self.calls += 1
        raise AssertionError("lower-priority strategy should not be called")


def test_app_renders_lost_board_before_reset(monkeypatch) -> None:
    lost_board = StubBoard(
        2,
        2,
        1,
        [
            Tile(Coord(0, 0), TileState.EXPLODED, True),
            Tile(Coord(1, 0), TileState.HIDDEN, False),
            Tile(Coord(0, 1), TileState.HIDDEN, False),
            Tile(Coord(1, 1), TileState.HIDDEN, False),
        ],
    )
    reset_board = StubBoard(
        2,
        2,
        1,
        [
            Tile(Coord(0, 0), TileState.HIDDEN, False),
            Tile(Coord(1, 0), TileState.HIDDEN, False),
            Tile(Coord(0, 1), TileState.HIDDEN, False),
            Tile(Coord(1, 1), TileState.HIDDEN, True),
        ],
    )
    game = StubGame(lost_board, reset_board, GamePhase.LOST)
    renderer = RecordingRenderer()

    monkeypatch.setattr(app_module, "PygameRenderer", lambda _config: renderer)
    monkeypatch.setattr(app_module, "Game", lambda _config, _rng: game)
    monkeypatch.setattr(app_module, "poll_events", lambda _mode, _renderer: [app_module.QuitEvent()])
    monkeypatch.setattr(app_module.pygame.time, "delay", lambda _ms: None)
    monkeypatch.setattr(app_module.pygame, "quit", lambda: None)

    app = app_module.App(GameConfig(width=2, height=2, num_mines=1, restart_delay_ms=0), PLAYER_ONLY)

    app.run()

    assert renderer.rendered_states == [
        {
            Coord(0, 0): TileState.EXPLODED,
            Coord(1, 0): TileState.HIDDEN,
            Coord(0, 1): TileState.HIDDEN,
            Coord(1, 1): TileState.HIDDEN,
        }
    ]
    assert game.reset_calls == 1


def test_ai_turn_applies_full_batch_from_first_matching_strategy(monkeypatch) -> None:
    game = RecordingMoveGame()
    batch = [
        Move(ActionType.REVEAL, Coord(0, 0)),
        Move(ActionType.FLAG, Coord(1, 1)),
    ]
    first = StubBatchStrategy(batch)
    second = FailingStrategy()

    monkeypatch.setattr(app_module, "PygameRenderer", lambda _config: object())
    monkeypatch.setattr(app_module, "Game", lambda _config, _rng: game)

    app = app_module.App(GameConfig())
    app._analyzer = StubAnalyzer(
        AnalyzedBoard(unknown_coords=frozenset({Coord(0, 0), Coord(1, 1)}))
    )
    app._strategies = [first, second]

    app._run_ai_turn()

    assert game.applied_moves == batch
    assert first.calls == 1
    assert second.calls == 0
    assert app._is_evaluable is True
