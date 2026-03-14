from __future__ import annotations

from math import sqrt
from typing import Any, NamedTuple

from minesweeper.domain.tile import Tile
from minesweeper.domain.types import Coord, TileState

Color = tuple[int, int, int]
PixelGrid = Any


class ColorProfiles(NamedTuple):
    hidden_bg: Color
    revealed_bg: Color
    flagged_bg: Color | None
    number_colors: dict[int, Color]
    mine_bg: Color | None


def color_distance(a: Color, b: Color) -> float:
    return sqrt(sum((left - right) ** 2 for left, right in zip(a, b)))


def average_color(colors: list[Color]) -> Color:
    count = len(colors)
    return tuple(sum(color[channel] for color in colors) // count for channel in range(3))  # type: ignore[return-value]


def sample_background(pixels: PixelGrid) -> Color:
    width, height = pixels.size
    colors = [
        pixels.getpixel((x, y))
        for y in range(height)
        for x in range(width)
        if x in {0, width - 1} or y in {0, height - 1}
    ]
    return average_color(colors)


def sample_center(pixels: PixelGrid, patch_radius: int = 1) -> Color:
    width, height = pixels.size
    center_x = width // 2
    center_y = height // 2
    colors = [
        pixels.getpixel((x, y))
        for y in range(center_y - patch_radius, center_y + patch_radius + 1)
        for x in range(center_x - patch_radius, center_x + patch_radius + 1)
    ]
    return average_color(colors)


class TileClassifier:
    def __init__(
        self,
        profiles: ColorProfiles,
        background_threshold: float = 80.0,
        center_threshold: float = 20.0,
    ) -> None:
        self._profiles = profiles
        self._background_threshold = background_threshold
        self._center_threshold = center_threshold
        self._last_tiles: dict[Coord, Tile] = {}

    def classify(self, pixels: PixelGrid, coord: Coord) -> Tile:
        background = sample_background(pixels)
        state = self._match_background(background)

        if state is None or state == TileState.HIDDEN:
            return self._remember(Tile(coord=coord, state=TileState.HIDDEN, is_mine=False))

        if state == TileState.FLAGGED:
            return self._remember(Tile(coord=coord, state=TileState.FLAGGED, is_mine=False))

        center = sample_center(pixels)
        if color_distance(center, background) <= self._center_threshold:
            return self._remember(
                Tile(coord=coord, state=TileState.REVEALED, is_mine=False, adjacent_mines=0)
            )

        number = self._match_number(center)
        return self._remember(
            Tile(coord=coord, state=TileState.REVEALED, is_mine=False, adjacent_mines=number)
        )

    def verify_number(self, coord: Coord, expected: int) -> bool:
        tile = self._last_tiles.get(coord)
        if tile is None:
            return False
        return tile.state == TileState.REVEALED and tile.adjacent_mines == expected

    def _match_background(self, color: Color) -> TileState | None:
        candidates: dict[TileState, Color] = {
            TileState.HIDDEN: self._profiles.hidden_bg,
            TileState.REVEALED: self._profiles.revealed_bg,
        }
        if self._profiles.flagged_bg is not None:
            candidates[TileState.FLAGGED] = self._profiles.flagged_bg

        state, distance = min(
            (
                (state, color_distance(color, profile))
                for state, profile in candidates.items()
            ),
            key=lambda item: item[1],
        )
        if distance > self._background_threshold:
            return None
        return state

    def _match_number(self, color: Color) -> int:
        if not self._profiles.number_colors:
            return 0

        number, _ = min(
            (
                (number, color_distance(color, profile))
                for number, profile in self._profiles.number_colors.items()
            ),
            key=lambda item: item[1],
        )
        return number

    def _remember(self, tile: Tile) -> Tile:
        self._last_tiles[tile.coord] = tile
        return tile
