from __future__ import annotations

import argparse
from collections.abc import Sequence

from minesweeper.app import App
from minesweeper.domain.types import AI_ONLY, HYBRID, PLAYER_ONLY, GameConfig, GameMode


def build_parser() -> argparse.ArgumentParser:
    defaults = GameConfig()
    parser = argparse.ArgumentParser(prog="python -m minesweeper")
    parser.add_argument(
        "--mode",
        choices=("player", "ai", "hybrid"),
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
    return parser


def parse_mode(value: str) -> GameMode:
    mapping = {
        "player": PLAYER_ONLY,
        "ai": AI_ONLY,
        "hybrid": HYBRID,
    }
    return mapping[value]


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

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

    App(config, parse_mode(args.mode)).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
