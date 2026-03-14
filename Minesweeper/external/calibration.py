from __future__ import annotations

import colorsys
import time
from collections.abc import Callable
from importlib import import_module
from typing import Any, NamedTuple

from minesweeper.domain.types import Coord
from minesweeper.external.capture import ScreenCapture, ScreenRegion, TileSize
from minesweeper.external.classifier import (
    ColorProfiles,
    average_color,
    color_distance,
    sample_background,
    sample_center,
)


class CalibrationResult(NamedTuple):
    board_region: ScreenRegion
    tile_size: TileSize
    width: int
    height: int
    num_mines: int
    profiles: ColorProfiles


class _TilePixelGrid:
    def __init__(
        self,
        pixels: Any,
        coord: Coord,
        tile_size: TileSize,
    ) -> None:
        self._pixels = pixels
        self._origin_x = coord.x * tile_size.width
        self._origin_y = coord.y * tile_size.height
        self.size = (tile_size.width, tile_size.height)

    def getpixel(self, position: tuple[int, int]) -> Any:
        x, y = position
        return self._pixels.getpixel((self._origin_x + x, self._origin_y + y))


def _tile_pixels(pixels: Any, coord: Coord, tile_size: TileSize) -> _TilePixelGrid:
    return _TilePixelGrid(pixels=pixels, coord=coord, tile_size=tile_size)


def _changed_tiles(
    before_pixels: Any,
    after_pixels: Any,
    width: int,
    height: int,
    tile_size: TileSize,
) -> list[Coord]:
    changed: list[Coord] = []
    for x in range(width):
        for y in range(height):
            coord = Coord(x, y)
            before_tile = _tile_pixels(before_pixels, coord, tile_size)
            after_tile = _tile_pixels(after_pixels, coord, tile_size)
            if _tile_signature(before_tile) != _tile_signature(after_tile):
                changed.append(coord)
    return changed


def _tile_signature(tile_pixels: _TilePixelGrid) -> tuple[Any, ...]:
    width, height = tile_pixels.size
    return tuple(
        tile_pixels.getpixel((x, y))
        for y in range(height)
        for x in range(width)
    )


def _build_live_profiles(
    before_pixels: Any,
    after_pixels: Any,
    width: int,
    height: int,
    tile_size: TileSize,
) -> ColorProfiles:
    hidden_samples = [
        sample_background(_tile_pixels(before_pixels, Coord(x, y), tile_size))
        for x in range(width)
        for y in range(height)
    ]
    hidden_bg = average_color(hidden_samples)

    changed_coords = _changed_tiles(
        before_pixels=before_pixels,
        after_pixels=after_pixels,
        width=width,
        height=height,
        tile_size=tile_size,
    )
    if not changed_coords:
        raise ValueError("No changed tiles detected after first reveal")

    revealed_samples: list[tuple[int, int, int]] = []
    number_colors: dict[int, tuple[int, int, int]] = {}
    for coord in changed_coords:
        tile = _tile_pixels(after_pixels, coord, tile_size)
        background = sample_background(tile)
        center = sample_center(tile)
        revealed_samples.append(background)
        if color_distance(center, background) > 20:
            number = _infer_number_from_color(center)
            if number is not None:
                number_colors[number] = center

    revealed_bg = average_color(revealed_samples)
    return ColorProfiles(
        hidden_bg=hidden_bg,
        revealed_bg=revealed_bg,
        flagged_bg=None,
        number_colors=number_colors,
        mine_bg=None,
    )


def _infer_number_from_color(color: tuple[int, int, int]) -> int | None:
    red, green, blue = [channel / 255 for channel in color]
    hue, saturation, value = colorsys.rgb_to_hsv(red, green, blue)
    hue_degrees = hue * 360

    if saturation < 0.1:
        return None
    if 210 <= hue_degrees <= 250:
        return 1
    if 90 <= hue_degrees <= 150:
        return 2
    if hue_degrees <= 20 or hue_degrees >= 340:
        return 3
    if 240 <= hue_degrees <= 280:
        return 4
    if 160 <= hue_degrees <= 200:
        return 6
    return None


def _default_read_point(prompt: str) -> tuple[int, int]:
    raw = input(f"{prompt} (x,y): ")
    x_text, y_text = [part.strip() for part in raw.split(",", maxsplit=1)]
    return int(x_text), int(y_text)


def _default_read_int(prompt: str) -> int:
    return int(input(f"{prompt}: "))


def _default_profile_builder(
    before_pixels: Any,
    after_pixels: Any,
    width: int,
    height: int,
    _tile_size: TileSize,
) -> ColorProfiles:
    return _build_live_profiles(
        before_pixels=before_pixels,
        after_pixels=after_pixels,
        width=width,
        height=height,
        tile_size=_tile_size,
    )


def _default_click(x: int, y: int) -> None:
    pyautogui = _load_pyautogui()
    if pyautogui is None:
        raise RuntimeError("pyautogui is required for live calibration clicks")
    pyautogui.click(x, y)


def _load_pyautogui() -> Any | None:
    try:
        return import_module("pyautogui")
    except ImportError:
        return None


class CalibrationWizard:
    def __init__(
        self,
        capture: ScreenCapture,
        read_point: Callable[[str], tuple[int, int]] | None = None,
        read_int: Callable[[str], int] | None = None,
        click: Callable[[int, int], None] | None = None,
        sleep: Callable[[float], None] | None = None,
        settle_delay_ms: int = 750,
        profile_builder: Callable[[Any, Any, int, int, TileSize], ColorProfiles] | None = None,
    ) -> None:
        self._capture = capture
        self._read_point = read_point or _default_read_point
        self._read_int = read_int or _default_read_int
        self._click = click or _default_click
        self._sleep = sleep or time.sleep
        self._settle_delay_seconds = settle_delay_ms / 1000
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
        before_pixels = self._capture.grab(board_region)
        click_x, click_y = self._center_click_point(board_region, tile_size, width, height)
        self._click(click_x, click_y)
        self._sleep(self._settle_delay_seconds)
        after_pixels = self._capture.grab(board_region)
        profiles = self._profile_builder(before_pixels, after_pixels, width, height, tile_size)

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

    def _center_click_point(
        self,
        board_region: ScreenRegion,
        tile_size: TileSize,
        width: int,
        height: int,
    ) -> tuple[int, int]:
        center_coord = Coord(width // 2, height // 2)
        return (
            board_region.left + center_coord.x * tile_size.width + tile_size.width // 2,
            board_region.top + center_coord.y * tile_size.height + tile_size.height // 2,
        )
