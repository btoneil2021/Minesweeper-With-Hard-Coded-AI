from __future__ import annotations

import minesweeper.app as app_module
from minesweeper.domain.tile import Tile
from minesweeper.domain.types import Coord, GameConfig, GamePhase, PLAYER_ONLY, TileState


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
