from __future__ import annotations

from typing import Any

from minesweeper.domain.tile import Tile
from minesweeper.domain.types import Coord
from minesweeper.external.capture import ScreenCapture, ScreenRegion, TileSize
from minesweeper.external.classifier import TileClassifier
from minesweeper.external.grid import TileGrid


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


class ScreenBoardReader:
    def __init__(
        self,
        capture: ScreenCapture,
        classifier: TileClassifier,
        board_region: ScreenRegion,
        tile_size: TileSize,
        width: int,
        height: int,
        num_mines: int,
        grid: TileGrid | None = None,
    ) -> None:
        self._capture = capture
        self._classifier = classifier
        self._board_region = board_region
        self._tile_size = tile_size
        self._width = width
        self._height = height
        self._num_mines = num_mines
        self._grid = grid
        self._tiles: dict[Coord, Tile] | None = None

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def num_mines(self) -> int:
        return self._num_mines

    def refresh(self) -> None:
        board_pixels = self._capture.grab(self._board_region)
        tiles: dict[Coord, Tile] = {}
        for x in range(self._width):
            for y in range(self._height):
                coord = Coord(x, y)
                tile_pixels = self._tile_pixels(board_pixels, coord)
                tiles[coord] = self._classifier.classify(tile_pixels, coord)

        self._tiles = tiles

    def tile_at(self, coord: Coord) -> Tile:
        if self._tiles is None:
            raise RuntimeError("ScreenBoardReader.refresh() must run before tile_at()")

        if not (0 <= coord.x < self._width and 0 <= coord.y < self._height):
            raise KeyError(coord)

        return self._tiles[coord]

    def _tile_pixels(self, board_pixels: Any, coord: Coord) -> _TilePixelGrid:
        if self._grid is not None:
            rect = self._grid.tile_rect(coord)
            return _TilePixelGrid(
                pixels=board_pixels,
                origin_x=rect.left - self._board_region.left,
                origin_y=rect.top - self._board_region.top,
                width=rect.width,
                height=rect.height,
            )
        return _TilePixelGrid(
            pixels=board_pixels,
            origin_x=coord.x * self._tile_size.width,
            origin_y=coord.y * self._tile_size.height,
            width=self._tile_size.width,
            height=self._tile_size.height,
        )
