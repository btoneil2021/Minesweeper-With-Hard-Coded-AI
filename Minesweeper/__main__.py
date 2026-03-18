from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Literal

from minesweeper.app import App
from minesweeper.domain.tile import Tile
from minesweeper.domain.types import AI_ONLY, HYBRID, PLAYER_ONLY, Coord, GameConfig, GameMode, TileState
from minesweeper.external.runtime import STOP_REASONS

ExternalMode = Literal["external"]
BrowserDomMode = Literal["browser-dom"]


def build_parser() -> argparse.ArgumentParser:
    defaults = GameConfig()
    parser = argparse.ArgumentParser(prog="python -m minesweeper")
    parser.add_argument(
        "--mode",
        choices=("player", "ai", "hybrid", "external", "browser-dom"),
        default="player",
        help="Game mode to launch",
    )
    parser.add_argument("--width", type=int, default=defaults.width, help="Board width in tiles")
    parser.add_argument("--height", type=int, default=defaults.height, help="Board height in tiles")
    parser.add_argument("--mines", type=int, default=defaults.num_mines, help="Number of mines")
    parser.add_argument(
        "--tile-size",
        type=int,
        default=defaults.tile_size_px,
        help="Tile size in pixels",
    )
    parser.add_argument(
        "--font-size",
        type=int,
        default=defaults.font_size_px,
        help="UI font size in pixels",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print external runtime progress and stop reasons",
    )
    parser.add_argument(
        "--debug-captures",
        type=Path,
        help="Write temporary raw external screenshots to the given directory",
    )
    return parser


def parse_mode(value: str) -> GameMode | ExternalMode | BrowserDomMode:
    mapping = {
        "player": PLAYER_ONLY,
        "ai": AI_ONLY,
        "hybrid": HYBRID,
        "external": "external",
        "browser-dom": "browser-dom",
    }
    return mapping[value]


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    mode = parse_mode(args.mode)

    if mode == "external":
        from minesweeper.external import run as run_external

        run_external(
            output=print if args.verbose else None,
            debug_capture_dir=args.debug_captures,
        )
        return 0

    if mode == "browser-dom":
        if args.debug_captures is not None:
            parser.error("--debug-captures is not supported with --mode browser-dom")

        try:
            reason = _run_browser_dom(output=print if args.verbose else None)
        except OSError as exc:
            parser.error(f"browser-dom HTTP bridge could not bind: {exc}")
        if reason == STOP_REASONS.board_refresh_failed_after_retry:
            parser.error("browser-dom mode requires a connected extension session")
        return 0

    try:
        config = GameConfig(
            width=args.width,
            height=args.height,
            num_mines=args.mines,
            tile_size_px=args.tile_size,
            font_size_px=args.font_size,
        )
    except ValueError as exc:
        parser.error(str(exc))

    App(config, mode).run()
    return 0


class _BrowserDomReader:
    def __init__(self) -> None:
        self.width = 0
        self.height = 0
        self.num_mines = 0
        self._tiles: dict[tuple[int, int], Tile] = {}
        self._has_snapshot = False

    def update_snapshot(self, snapshot) -> None:
        self.width = snapshot.width
        self.height = snapshot.height
        self._tiles = {
            (tile.x, tile.y): self._tile_from_snapshot(tile)
            for tile in snapshot.tiles
        }
        self._has_snapshot = True

    def tile_at(self, coord):
        if not self._has_snapshot:
            raise KeyError(coord)
        if not (0 <= coord.x < self.width and 0 <= coord.y < self.height):
            raise KeyError(coord)
        return self._tiles[(coord.x, coord.y)]

    def _tile_from_snapshot(self, tile) -> Tile:
        coord = Coord(tile.x, tile.y)
        if tile.state == "hidden":
            return Tile(coord=coord, state=TileState.HIDDEN, is_mine=False)
        if tile.state == "flagged":
            return Tile(coord=coord, state=TileState.FLAGGED, is_mine=False)
        if tile.state == "exploded":
            return Tile(coord=coord, state=TileState.EXPLODED, is_mine=True)
        if tile.state == "mine_revealed":
            return Tile(coord=coord, state=TileState.REVEALED, is_mine=True, adjacent_mines=0)
        return Tile(
            coord=coord,
            state=TileState.REVEALED,
            is_mine=False,
            adjacent_mines=tile.adjacent_mines or 0,
        )


def _run_browser_dom(
    output: Callable[[str], None] | None = None,
    *,
    bridge_factory: Callable[[], object] | None = None,
    http_server_factory: Callable[[object], object] | None = None,
    board_reader_factory: Callable[[], object] | None = None,
    executor_factory: Callable[[str, Callable[[object], None]], object] | None = None,
    app_factory: Callable[..., object] | None = None,
    session_id: str = "browser-dom",
) -> str:
    if bridge_factory is None:
        from minesweeper.external.browser.bridge.server import BrowserBridgeServer

        bridge_factory = BrowserBridgeServer
    if http_server_factory is None:
        from minesweeper.external.browser.bridge.http_server import BrowserHttpServer

        http_server_factory = BrowserHttpServer
    if board_reader_factory is None:
        board_reader_factory = _BrowserDomReader
    if executor_factory is None:
        from minesweeper.external.browser.dom_executor import DomMoveExecutor

        executor_factory = DomMoveExecutor
    if app_factory is None:
        from minesweeper.external.browser.app import BrowserApp

        app_factory = BrowserApp

    bridge = bridge_factory()
    http_server = http_server_factory(bridge)
    http_server.start()
    try:
        bridge.register_session(session_id)
        board_reader = board_reader_factory()
        executor = executor_factory(session_id, lambda command: bridge.queue_command(session_id, command))
        app = app_factory(
            session_id=session_id,
            bridge=bridge,
            board_reader=board_reader,
            executor=executor,
            output=output,
        )
        return app.run()
    finally:
        http_server.stop()


if __name__ == "__main__":
    raise SystemExit(main())
