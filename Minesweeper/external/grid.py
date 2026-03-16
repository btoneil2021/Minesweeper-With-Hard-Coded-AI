from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from minesweeper.domain.types import Coord
from minesweeper.external.capture import ScreenRegion

PixelGrid = Any


@dataclass(frozen=True)
class TileGrid:
    origin_left: int
    origin_top: int
    col_boundaries: tuple[int, ...]
    row_boundaries: tuple[int, ...]

    @property
    def width(self) -> int:
        return len(self.col_boundaries) - 1

    @property
    def height(self) -> int:
        return len(self.row_boundaries) - 1

    def tile_rect(self, coord: Coord) -> ScreenRegion:
        left = self.origin_left + self.col_boundaries[coord.x]
        right = self.origin_left + self.col_boundaries[coord.x + 1]
        top = self.origin_top + self.row_boundaries[coord.y]
        bottom = self.origin_top + self.row_boundaries[coord.y + 1]
        return ScreenRegion(left=left, top=top, width=right - left, height=bottom - top)

    def click_target(self, coord: Coord, inset: int = 4) -> tuple[int, int]:
        rect = self.tile_rect(coord)
        safe_width = max(1, rect.width - inset * 2)
        safe_height = max(1, rect.height - inset * 2)
        x = rect.left + inset + safe_width // 2
        y = rect.top + inset + safe_height // 2
        return (
            min(max(x, rect.left), rect.left + rect.width - 1),
            min(max(y, rect.top), rect.top + rect.height - 1),
        )


def detect_tile_grid(
    pixels: PixelGrid,
    board_left: int,
    board_top: int,
    output: Any | None = None,
) -> TileGrid:
    return TileGrid(
        origin_left=board_left,
        origin_top=board_top,
        col_boundaries=tuple(detect_grid_lines(pixels, axis="x")),
        row_boundaries=tuple(detect_grid_lines(pixels, axis="y")),
    )


def detect_grid_lines(pixels: PixelGrid, axis: str) -> list[int]:
    profile = _line_profile(pixels, axis)
    board_start, board_end = _board_span(profile)
    board_runs = _color_runs(profile[board_start:board_end])
    candidate_runs = [runs for runs in board_runs.values() if len(runs) >= 2]
    if not candidate_runs:
        raise ValueError("could not detect repeating grid boundaries")

    border_runs = min(
        candidate_runs,
        key=lambda runs: (sum(end - start for start, end in runs), -len(runs)),
    )
    boundaries = [board_start + start for start, _end in border_runs]
    boundaries.append(board_end)
    return boundaries


def _line_profile(pixels: PixelGrid, axis: str) -> list[tuple[int, int, int]]:
    width, height = pixels.size
    if axis == "x":
        y = height // 2
        return [pixels.getpixel((x, y)) for x in range(width)]
    if axis == "y":
        x = width // 2
        return [pixels.getpixel((x, y)) for y in range(height)]
    raise ValueError(f"unsupported axis: {axis}")


def _color_runs(profile: list[tuple[int, int, int]]) -> dict[tuple[int, int, int], list[tuple[int, int]]]:
    runs: dict[tuple[int, int, int], list[tuple[int, int]]] = {}
    if not profile:
        return runs

    start = 0
    current = profile[0]
    for index, color in enumerate(profile[1:], start=1):
        if color == current:
            continue
        runs.setdefault(current, []).append((start, index))
        start = index
        current = color
    runs.setdefault(current, []).append((start, len(profile)))
    return runs


def _board_span(profile: list[tuple[int, int, int]]) -> tuple[int, int]:
    left_pad = profile[0]
    right_pad = profile[-1]

    start = 0
    while start < len(profile) and profile[start] == left_pad:
        start += 1

    end = len(profile)
    while end > start and profile[end - 1] == right_pad:
        end -= 1

    if start >= end:
        raise ValueError("could not locate board content")
    return start, end
