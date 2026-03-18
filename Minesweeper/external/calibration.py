from __future__ import annotations

import colorsys
import math
import threading
import time
from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from typing import Any, NamedTuple

from minesweeper.domain.types import Coord
from minesweeper.external.capture import ScreenCapture, ScreenRegion, TileSize
from minesweeper.external.classifier import (
    ColorProfiles,
    average_color,
    color_distance,
    sample_accent,
    sample_background,
    sample_center,
)
from minesweeper.external.debug_capture import dump_capture
from minesweeper.external.grid import TileGrid, detect_tile_grid


class CalibrationResult(NamedTuple):
    board_region: ScreenRegion
    tile_size: TileSize
    width: int
    height: int
    num_mines: int
    profiles: ColorProfiles
    grid: TileGrid | None = None


class _PointCaptureUnavailable(RuntimeError):
    pass


class _PointCaptureCancelled(RuntimeError):
    pass


class _PynputModules(NamedTuple):
    keyboard: Any
    mouse: Any


QUIET_ALIGNMENT_TOLERANCE = 0.15
SNAP_ALIGNMENT_TOLERANCE = 0.45
ROUGH_CALIBRATION_MARGIN_PX = 96


class _GuardedClickCollector:
    def __init__(
        self,
        left_button: Any,
        guard_keys: set[Any],
        cancel_key: Any,
    ) -> None:
        self._left_button = left_button
        self._guard_keys = guard_keys
        self._cancel_key = cancel_key
        self._guard_pressed = False
        self.cancelled = False
        self.point: tuple[int, int] | None = None

    def on_press(self, key: Any) -> bool | None:
        if key == self._cancel_key:
            self.cancelled = True
            return False
        if key in self._guard_keys:
            self._guard_pressed = True
        return None

    def on_release(self, key: Any) -> None:
        if key in self._guard_keys:
            self._guard_pressed = False

    def on_click(self, x: int, y: int, button: Any, pressed: bool) -> bool | None:
        if not pressed:
            return None
        if button != self._left_button:
            return None
        if not self._guard_pressed:
            return None
        self.point = (x, y)
        return False


class _TilePixelGrid:
    def __init__(
        self,
        pixels: Any,
        origin_x: int,
        origin_y: int,
        width: int,
        height: int,
    ) -> None:
        self._pixels = pixels
        self._origin_x = origin_x
        self._origin_y = origin_y
        self.size = (width, height)

    def getpixel(self, position: tuple[int, int]) -> Any:
        x, y = position
        return self._pixels.getpixel((self._origin_x + x, self._origin_y + y))


def _tile_pixels(
    pixels: Any,
    coord: Coord,
    tile_size: TileSize | None = None,
    grid: TileGrid | None = None,
) -> _TilePixelGrid:
    if grid is not None:
        rect = grid.tile_rect(coord)
        return _TilePixelGrid(
            pixels=pixels,
            origin_x=rect.left - grid.origin_left,
            origin_y=rect.top - grid.origin_top,
            width=rect.width,
            height=rect.height,
        )
    if tile_size is None:
        raise ValueError("tile_size is required when grid is not provided")
    return _TilePixelGrid(
        pixels=pixels,
        origin_x=coord.x * tile_size.width,
        origin_y=coord.y * tile_size.height,
        width=tile_size.width,
        height=tile_size.height,
    )


def _changed_tiles(
    before_pixels: Any,
    after_pixels: Any,
    width: int | None = None,
    height: int | None = None,
    tile_size: TileSize | None = None,
    grid: TileGrid | None = None,
) -> list[Coord]:
    if grid is not None:
        width = grid.width
        height = grid.height
    if width is None or height is None:
        raise ValueError("width and height are required when grid is not provided")

    changed: list[Coord] = []
    for x in range(width):
        for y in range(height):
            coord = Coord(x, y)
            before_tile = _tile_pixels(before_pixels, coord, tile_size=tile_size, grid=grid)
            after_tile = _tile_pixels(after_pixels, coord, tile_size=tile_size, grid=grid)
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
    width: int | None = None,
    height: int | None = None,
    tile_size: TileSize | None = None,
    grid: TileGrid | None = None,
) -> ColorProfiles:
    if grid is not None:
        width = grid.width
        height = grid.height
    if width is None or height is None:
        raise ValueError("width and height are required when grid is not provided")

    hidden_samples = [
        sample_center(_tile_pixels(before_pixels, Coord(x, y), tile_size=tile_size, grid=grid))
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
        grid=grid,
    )
    if not changed_coords:
        raise ValueError("No changed tiles detected after first reveal")

    revealed_samples: list[tuple[int, int, int]] = []
    number_colors: dict[int, tuple[int, int, int]] = {}
    for coord in changed_coords:
        tile = _tile_pixels(after_pixels, coord, tile_size=tile_size, grid=grid)
        background = sample_background(tile)
        center = sample_center(tile)
        accent = sample_accent(tile, background)
        if accent is None:
            revealed_samples.append(center)
        if accent is not None:
            number = _infer_number_from_color(accent)
            if number is not None:
                number_colors[number] = accent

    if not revealed_samples:
        revealed_samples = [
            sample_background(_tile_pixels(after_pixels, coord, tile_size=tile_size, grid=grid))
            for coord in changed_coords
        ]

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


def _default_capture_point(
    prompt: str,
    manual_read_point: Callable[[str], tuple[int, int]],
    live_picker: Callable[[str], tuple[int, int]],
    output: Callable[[str], None] | None = None,
) -> tuple[int, int]:
    emit = output or (lambda _message: None)
    try:
        return live_picker(prompt)
    except _PointCaptureUnavailable as exc:
        emit(f"{exc}. Falling back to manual coordinates.")
        return manual_read_point(prompt)
    except _PointCaptureCancelled as exc:
        emit(f"{exc}. Falling back to manual coordinates.")
        return manual_read_point(prompt)


def _wait_for_guarded_click(
    prompt: str,
    output: Callable[[str], None] | None = None,
    timeout_seconds: float = 10.0,
    pynput_loader: Callable[[], _PynputModules | None] | None = None,
) -> tuple[int, int]:
    modules = (pynput_loader or _load_pynput)()
    if modules is None:
        raise _PointCaptureUnavailable("pynput is not installed")

    emit = output or (lambda _message: None)
    emit(f"{prompt}: hold Shift and left-click. Press Esc to cancel.")

    keyboard_key = modules.keyboard.Key
    collector = _GuardedClickCollector(
        left_button=modules.mouse.Button.left,
        guard_keys={keyboard_key.shift, keyboard_key.shift_l, keyboard_key.shift_r},
        cancel_key=keyboard_key.esc,
    )
    finished = threading.Event()

    def on_press(key: Any) -> bool | None:
        should_stop = collector.on_press(key)
        if should_stop is False:
            finished.set()
        return should_stop

    def on_release(key: Any) -> None:
        collector.on_release(key)

    def on_click(x: int, y: int, button: Any, pressed: bool) -> bool | None:
        should_stop = collector.on_click(x, y, button, pressed)
        if should_stop is False:
            finished.set()
        return should_stop

    keyboard_listener = modules.keyboard.Listener(on_press=on_press, on_release=on_release)
    mouse_listener = modules.mouse.Listener(on_click=on_click)

    with keyboard_listener, mouse_listener:
        if not finished.wait(timeout_seconds):
            raise _PointCaptureCancelled("Live point capture timed out")

    if collector.point is not None:
        return collector.point
    raise _PointCaptureCancelled("Live point capture was cancelled")


def _default_profile_builder(
    before_pixels: Any,
    after_pixels: Any,
    width: int,
    height: int,
    _tile_size: TileSize,
    grid: TileGrid,
) -> ColorProfiles:
    return _build_live_profiles(
        before_pixels=before_pixels,
        after_pixels=after_pixels,
        width=width,
        height=height,
        tile_size=_tile_size,
        grid=grid,
    )


def _default_click(x: int, y: int) -> None:
    pyautogui = _load_pyautogui()
    if pyautogui is None:
        raise RuntimeError("pyautogui is required for live calibration clicks")
    pyautogui.click(x, y)


def _derive_dimension(
    axis_name: str,
    total_pixels: int,
    tile_pixels: int,
    warn: Callable[[str], None],
) -> int:
    if tile_pixels <= 0:
        raise ValueError("tile alignment requires positive tile dimensions")

    ratio = total_pixels / tile_pixels
    rounded = math.floor(ratio + 0.5)
    drift = abs(ratio - rounded)

    if drift <= QUIET_ALIGNMENT_TOLERANCE:
        return rounded
    if drift <= SNAP_ALIGNMENT_TOLERANCE:
        warn(f"{axis_name} looked slightly off ({ratio:.2f}); snapping to {rounded} tiles.")
        return rounded
    raise ValueError("tile alignment appears inaccurate")


def _warn_if_dimension_snapped(
    axis_name: str,
    total_pixels: int,
    tile_pixels: int,
    expected_tiles: int,
    warn: Callable[[str], None],
) -> None:
    if tile_pixels <= 0:
        return

    ratio = total_pixels / tile_pixels
    drift = abs(ratio - expected_tiles)
    if drift <= QUIET_ALIGNMENT_TOLERANCE:
        return
    if drift <= SNAP_ALIGNMENT_TOLERANCE:
        warn(f"{axis_name} looked slightly off ({ratio:.2f}); snapping to {expected_tiles} tiles.")


def _normalize_grid(grid: TileGrid) -> tuple[TileGrid, ScreenRegion]:
    left_offset = grid.col_boundaries[0]
    top_offset = grid.row_boundaries[0]
    normalized = TileGrid(
        origin_left=grid.origin_left + left_offset,
        origin_top=grid.origin_top + top_offset,
        col_boundaries=tuple(boundary - left_offset for boundary in grid.col_boundaries),
        row_boundaries=tuple(boundary - top_offset for boundary in grid.row_boundaries),
    )
    board_region = ScreenRegion(
        left=normalized.origin_left,
        top=normalized.origin_top,
        width=normalized.col_boundaries[-1],
        height=normalized.row_boundaries[-1],
    )
    return normalized, board_region


def _regular_grid_from_region(
    region: ScreenRegion,
    width: int,
    height: int,
) -> TileGrid:
    return TileGrid(
        origin_left=region.left,
        origin_top=region.top,
        col_boundaries=tuple(
            round(index * region.width / width)
            for index in range(width + 1)
        ),
        row_boundaries=tuple(
            round(index * region.height / height)
            for index in range(height + 1)
        ),
    )


def _grid_looks_implausibly_small(
    board_region: ScreenRegion,
    clicked_board_region: ScreenRegion,
) -> bool:
    return (
        board_region.width < clicked_board_region.width * 0.6
        or board_region.height < clicked_board_region.height * 0.6
    )


def _standard_board_dimensions(num_mines: int) -> tuple[int, int] | None:
    presets = {
        10: (9, 9),
        40: (16, 16),
        99: (30, 16),
    }
    return presets.get(num_mines)


def _expand_region(region: ScreenRegion, margin_px: int) -> ScreenRegion:
    if margin_px <= 0:
        return region

    left = max(0, region.left - margin_px)
    top = max(0, region.top - margin_px)
    right = region.left + region.width + margin_px
    bottom = region.top + region.height + margin_px
    return ScreenRegion(
        left=left,
        top=top,
        width=right - left,
        height=bottom - top,
    )


def _grid_tile_size(grid: TileGrid) -> TileSize:
    widths = sorted(
        grid.col_boundaries[index + 1] - grid.col_boundaries[index]
        for index in range(grid.width)
    )
    heights = sorted(
        grid.row_boundaries[index + 1] - grid.row_boundaries[index]
        for index in range(grid.height)
    )
    return TileSize(
        width=widths[len(widths) // 2],
        height=heights[len(heights) // 2],
    )


def _load_pyautogui() -> Any | None:
    try:
        return import_module("pyautogui")
    except ImportError:
        return None


def _load_pynput() -> _PynputModules | None:
    try:
        return _PynputModules(
            keyboard=import_module("pynput.keyboard"),
            mouse=import_module("pynput.mouse"),
        )
    except ImportError:
        return None


class CalibrationWizard:
    def __init__(
        self,
        capture: ScreenCapture,
        capture_point: Callable[[str], tuple[int, int]] | None = None,
        read_point: Callable[[str], tuple[int, int]] | None = None,
        read_int: Callable[[str], int] | None = None,
        click: Callable[[int, int], None] | None = None,
        sleep: Callable[[float], None] | None = None,
        settle_delay_ms: int = 750,
        rough_calibration_margin_px: int = ROUGH_CALIBRATION_MARGIN_PX,
        profile_builder: Callable[[Any, Any, int, int, TileSize, TileGrid], ColorProfiles] | None = None,
        grid_detector: Callable[[Any, ScreenRegion], TileGrid] | None = None,
        output: Callable[[str], None] | None = None,
        debug_capture_dir: Path | None = None,
    ) -> None:
        self._capture = capture
        self._output = output or print
        self._debug_capture_dir = debug_capture_dir
        self._manual_read_point = read_point or _default_read_point
        if capture_point is not None:
            self._capture_point = capture_point
        elif read_point is not None:
            self._capture_point = read_point
        else:
            self._capture_point = lambda prompt: _default_capture_point(
                prompt,
                manual_read_point=self._manual_read_point,
                live_picker=lambda live_prompt: _wait_for_guarded_click(
                    live_prompt,
                    output=self._output,
                ),
                output=self._output,
            )
        self._read_int = read_int or _default_read_int
        self._click = click or _default_click
        self._sleep = sleep or time.sleep
        self._settle_delay_seconds = settle_delay_ms / 1000
        self._rough_calibration_margin_px = rough_calibration_margin_px
        self._profile_builder = profile_builder or _default_profile_builder
        self._grid_detector = grid_detector or (
            lambda pixels, region: detect_tile_grid(
                pixels,
                board_left=region.left,
                board_top=region.top,
                output=self._output,
            )
        )

    def run(self) -> CalibrationResult:
        board_top_left = self._capture_point("Capture the top-left corner of the board.")
        board_bottom_right = self._capture_point("Capture the bottom-right corner of the board.")
        clicked_board_region = ScreenRegion(
            left=board_top_left[0],
            top=board_top_left[1],
            width=board_bottom_right[0] - board_top_left[0],
            height=board_bottom_right[1] - board_top_left[1],
        )
        rough_board_region = _expand_region(clicked_board_region, self._rough_calibration_margin_px)
        num_mines = self._read_int("Enter the mine count")

        rough_before_pixels = self._capture.grab(rough_board_region)
        grid, board_region = _normalize_grid(
            self._grid_detector(rough_before_pixels, rough_board_region)
        )
        if _grid_looks_implausibly_small(board_region, clicked_board_region):
            standard_dimensions = _standard_board_dimensions(num_mines)
            if standard_dimensions is not None:
                fallback_width, fallback_height = standard_dimensions
            else:
                fallback_width = _derive_dimension(
                    "Board width",
                    clicked_board_region.width,
                    _grid_tile_size(grid).width,
                    self._output,
                )
                fallback_height = _derive_dimension(
                    "Board height",
                    clicked_board_region.height,
                    _grid_tile_size(grid).height,
                    self._output,
                )
            grid, board_region = _normalize_grid(
                _regular_grid_from_region(
                    clicked_board_region,
                    width=fallback_width,
                    height=fallback_height,
                )
            )
        width = grid.width
        height = grid.height
        tile_size = _grid_tile_size(grid)
        _warn_if_dimension_snapped(
            "Board width",
            rough_board_region.width,
            tile_size.width,
            width,
            self._output,
        )
        _warn_if_dimension_snapped(
            "Board height",
            rough_board_region.height,
            tile_size.height,
            height,
            self._output,
        )
        before_pixels = self._capture.grab(board_region)
        if self._debug_capture_dir is not None:
            dump_capture(
                before_pixels,
                self._debug_capture_dir / "calibration" / "board_before_open.png",
                warn=self._output,
            )
        click_x, click_y = self._center_click_point(board_region, tile_size, width, height, grid)
        self._click(click_x, click_y)
        self._sleep(self._settle_delay_seconds)
        after_pixels = self._capture.grab(board_region)
        if self._debug_capture_dir is not None:
            dump_capture(
                after_pixels,
                self._debug_capture_dir / "calibration" / "board_after_open.png",
                warn=self._output,
            )
        profiles = self._profile_builder(before_pixels, after_pixels, width, height, tile_size, grid)

        return CalibrationResult(
            board_region=board_region,
            tile_size=tile_size,
            width=width,
            height=height,
            num_mines=num_mines,
            profiles=profiles,
            grid=grid,
        )

    def _derive_dimension(self, axis_name: str, total_pixels: int, tile_pixels: int) -> int:
        return _derive_dimension(
            axis_name=axis_name,
            total_pixels=total_pixels,
            tile_pixels=tile_pixels,
            warn=self._output,
        )

    def _center_click_point(
        self,
        board_region: ScreenRegion,
        tile_size: TileSize,
        width: int,
        height: int,
        grid: TileGrid | None = None,
    ) -> tuple[int, int]:
        center_coord = Coord(width // 2, height // 2)
        if grid is not None:
            return grid.click_target(center_coord)
        return (
            board_region.left + center_coord.x * tile_size.width + tile_size.width // 2,
            board_region.top + center_coord.y * tile_size.height + tile_size.height // 2,
        )
