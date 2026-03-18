from __future__ import annotations

from math import sqrt
from typing import Any, NamedTuple

from minesweeper.domain.tile import Tile
from minesweeper.domain.types import Coord, TileState
from minesweeper.external.errors import BoardReadError

Color = tuple[int, int, int]
PixelGrid = Any


class ColorProfiles(NamedTuple):
    hidden_bg: Color
    revealed_bg: Color
    flagged_bg: Color | None
    number_colors: dict[int, Color]
    mine_bg: Color | None


MINESWEEPERONLINE_NUMBER_COLORS: dict[int, Color] = {
    1: (0, 0, 255),
    2: (0, 128, 0),
    3: (255, 0, 0),
    4: (0, 0, 128),
    5: (128, 0, 0),
    6: (0, 128, 128),
    7: (0, 0, 0),
    8: (128, 128, 128),
}
MINESWEEPERONLINE_FLAG_COLORS: tuple[Color, ...] = (
    (220, 0, 0),
    (200, 0, 0),
    (0, 0, 0),
)


def color_distance(a: Color, b: Color) -> float:
    return sqrt(sum((left - right) ** 2 for left, right in zip(a, b)))


def average_color(colors: list[Color]) -> Color:
    count = len(colors)
    return tuple(sum(color[channel] for color in colors) // count for channel in range(3))  # type: ignore[return-value]


def sample_background(pixels: PixelGrid, inset: int = 1) -> Color:
    width, height = pixels.size
    if width >= 8 and height >= 8 and width > inset * 2 + 1 and height > inset * 2 + 1:
        x_min = inset
        x_max = width - inset - 1
        y_min = inset
        y_max = height - inset - 1
    else:
        x_min = 0
        x_max = width - 1
        y_min = 0
        y_max = height - 1
    colors = [
        pixels.getpixel((x, y))
        for y in range(y_min, y_max + 1)
        for x in range(x_min, x_max + 1)
        if x in {x_min, x_max} or y in {y_min, y_max}
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


def sample_accent(
    pixels: PixelGrid,
    background: Color,
    min_distance: float = 30.0,
    relative_threshold: float = 0.75,
    min_chroma: int = 35,
) -> Color | None:
    width, height = pixels.size
    if width <= 2 or height <= 2:
        return None

    candidates: list[tuple[float, Color]] = []
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            color = pixels.getpixel((x, y))
            distance = color_distance(color, background)
            if distance < min_distance:
                continue
            if _color_chroma(color) < min_chroma:
                continue
            candidates.append((distance, color))

    if not candidates:
        return None

    strongest = max(distance for distance, _color in candidates)
    selected = [
        color
        for distance, color in candidates
        if distance >= strongest * relative_threshold
    ]
    if not selected:
        return None
    return average_color(selected)


def _color_chroma(color: Color) -> int:
    return max(color) - min(color)


class TileClassifier:
    def __init__(
        self,
        profiles: ColorProfiles,
        background_threshold: float = 80.0,
        center_threshold: float = 20.0,
        number_threshold: float = 80.0,
        flag_threshold: float = 70.0,
    ) -> None:
        self._profiles = profiles
        self._background_threshold = background_threshold
        self._center_threshold = center_threshold
        self._number_threshold = number_threshold
        self._flag_threshold = flag_threshold
        self._last_tiles: dict[Coord, Tile] = {}

    def classify(self, pixels: PixelGrid, coord: Coord) -> Tile:
        center = sample_center(pixels)
        background = sample_background(pixels)
        accent = sample_accent(pixels, background)
        if self._looks_flagged(accent):
            return self._remember(Tile(coord=coord, state=TileState.FLAGGED, is_mine=False))

        state = self._match_center_state(center)
        if state is None:
            state = self._match_background(background)

        if state is None:
            fallback_state = self._fallback_uniform_state(center=center, background=background, accent=accent)
            if fallback_state is None:
                raise BoardReadError(f"untrusted tile background at {coord}")
            state = fallback_state

        if state == TileState.HIDDEN:
            return self._remember(Tile(coord=coord, state=TileState.HIDDEN, is_mine=False))

        if state == TileState.FLAGGED:
            return self._remember(Tile(coord=coord, state=TileState.FLAGGED, is_mine=False))

        if accent is None:
            return self._remember(
                Tile(coord=coord, state=TileState.REVEALED, is_mine=False, adjacent_mines=0)
            )

        number = self._match_number(accent)
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

    def _match_center_state(self, color: Color) -> TileState | None:
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
        if distance > self._center_threshold:
            return None
        return state

    def _match_number(self, color: Color) -> int:
        candidates = dict(MINESWEEPERONLINE_NUMBER_COLORS)
        candidates.update(self._profiles.number_colors)
        if not candidates:
            return 0

        number, distance = min(
            (
                (number, color_distance(color, profile))
                for number, profile in candidates.items()
            ),
            key=lambda item: item[1],
        )
        if distance > self._number_threshold:
            raise BoardReadError("untrusted tile accent")
        return number

    def _fallback_uniform_state(
        self,
        *,
        center: Color,
        background: Color,
        accent: Color | None,
    ) -> TileState | None:
        if accent is not None:
            return None

        brightness = max(sum(background) / 3, sum(center) / 3)
        hidden_brightness = sum(self._profiles.hidden_bg) / 3
        revealed_brightness = sum(self._profiles.revealed_bg) / 3
        if brightness >= max(hidden_brightness, revealed_brightness) + 20:
            return TileState.REVEALED
        return None

    def _looks_flagged(self, accent: Color | None) -> bool:
        if accent is None:
            return False
        return min(color_distance(accent, flag_color) for flag_color in MINESWEEPERONLINE_FLAG_COLORS) <= self._flag_threshold

    def _remember(self, tile: Tile) -> Tile:
        self._last_tiles[tile.coord] = tile
        return tile
