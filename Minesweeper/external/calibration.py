from __future__ import annotations

from collections.abc import Callable
from typing import Any, NamedTuple

from minesweeper.external.capture import ScreenCapture, ScreenRegion, TileSize
from minesweeper.external.classifier import ColorProfiles


class CalibrationResult(NamedTuple):
    board_region: ScreenRegion
    tile_size: TileSize
    width: int
    height: int
    num_mines: int
    profiles: ColorProfiles


def _default_read_point(prompt: str) -> tuple[int, int]:
    raw = input(f"{prompt} (x,y): ")
    x_text, y_text = [part.strip() for part in raw.split(",", maxsplit=1)]
    return int(x_text), int(y_text)


def _default_read_int(prompt: str) -> int:
    return int(input(f"{prompt}: "))


def _default_profile_builder(
    _capture: ScreenCapture,
    _board_region: ScreenRegion,
    _tile_size: TileSize,
) -> ColorProfiles:
    return ColorProfiles(
        hidden_bg=(0, 0, 0),
        revealed_bg=(0, 0, 0),
        flagged_bg=None,
        number_colors={},
        mine_bg=None,
    )


class CalibrationWizard:
    def __init__(
        self,
        capture: ScreenCapture,
        read_point: Callable[[str], tuple[int, int]] | None = None,
        read_int: Callable[[str], int] | None = None,
        profile_builder: Callable[[ScreenCapture, ScreenRegion, TileSize], ColorProfiles] | None = None,
    ) -> None:
        self._capture = capture
        self._read_point = read_point or _default_read_point
        self._read_int = read_int or _default_read_int
        self._profile_builder = profile_builder or _default_profile_builder

    def run(self) -> CalibrationResult:
        board_top_left = self._read_point("Click the top-left corner of the top-left tile")
        board_bottom_right = self._read_point(
            "Click the bottom-right corner of the bottom-right tile"
        )
        board_region = ScreenRegion(
            left=board_top_left[0],
            top=board_top_left[1],
            width=board_bottom_right[0] - board_top_left[0],
            height=board_bottom_right[1] - board_top_left[1],
        )

        tile_top_left = self._read_point("Click the top-left corner of any single tile")
        tile_bottom_right = self._read_point(
            "Click the bottom-right corner of that same tile"
        )
        tile_size = TileSize(
            width=tile_bottom_right[0] - tile_top_left[0],
            height=tile_bottom_right[1] - tile_top_left[1],
        )

        width = self._derive_dimension(board_region.width, tile_size.width)
        height = self._derive_dimension(board_region.height, tile_size.height)
        num_mines = self._read_int("How many mines are on this board")
        profiles = self._profile_builder(self._capture, board_region, tile_size)

        return CalibrationResult(
            board_region=board_region,
            tile_size=tile_size,
            width=width,
            height=height,
            num_mines=num_mines,
            profiles=profiles,
        )

    def _derive_dimension(self, total_pixels: int, tile_pixels: int) -> int:
        if tile_pixels <= 0:
            raise ValueError("tile alignment requires positive tile dimensions")

        ratio = total_pixels / tile_pixels
        rounded = round(ratio)
        if abs(ratio - rounded) > 0.15:
            raise ValueError("tile alignment appears inaccurate")

        return rounded
