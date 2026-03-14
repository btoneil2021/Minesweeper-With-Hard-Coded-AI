from __future__ import annotations

from typing import Any

from minesweeper.domain.tile import Tile
from minesweeper.domain.types import Coord
from minesweeper.external.capture import ScreenCapture, ScreenRegion, TileSize
from minesweeper.external.classifier import TileClassifier


class _TilePixelGrid:
    def __init__(
        self,
        pixels: Any,
        origin_x: int,
        origin_y: int,
        tile_size: TileSize,
    ) -> None:
        self._pixels = pixels
        self._origin_x = origin_x
        self._origin_y = origin_y
        self.size = (tile_size.width, tile_size.height)

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
    ) -> None:
        self._capture = capture
        self._classifier = classifier
        self._board_region = board_region
        self._tile_size = tile_size
        self._width = width
        self._height = height
        self._num_mines = num_mines
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
                tile_pixels = _TilePixelGrid(
                    pixels=board_pixels,
                    origin_x=x * self._tile_size.width,
                    origin_y=y * self._tile_size.height,
                    tile_size=self._tile_size,
                )
                tiles[coord] = self._classifier.classify(tile_pixels, coord)

        self._tiles = tiles

    def tile_at(self, coord: Coord) -> Tile:
        if self._tiles is None:
            raise RuntimeError("ScreenBoardReader.refresh() must run before tile_at()")

        if not (0 <= coord.x < self._width and 0 <= coord.y < self._height):
            raise KeyError(coord)

        return self._tiles[coord]
