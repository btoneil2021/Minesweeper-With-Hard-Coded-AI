from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from minesweeper.domain.move import Move
from minesweeper.domain.types import ActionType, TileState
from minesweeper.domain.tile import Tile
from minesweeper.domain.types import Coord
from minesweeper.external.capture import ScreenCapture, ScreenRegion, TileSize
from minesweeper.external.classifier import TileClassifier
from minesweeper.external.debug_capture import dump_capture, dump_move_overlay, write_debug_metadata
from minesweeper.external.errors import BoardReadError
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
        debug_capture_dir: Path | None = None,
        output: Callable[[str], None] | None = None,
    ) -> None:
        self._capture = capture
        self._classifier = classifier
        self._board_region = board_region
        self._tile_size = tile_size
        self._width = width
        self._height = height
        self._num_mines = num_mines
        self._grid = grid
        self._debug_capture_dir = debug_capture_dir
        self._output = output or (lambda _message: None)
        self._refresh_index = 0
        self._move_overlay_index = 0
        self._tiles: dict[Coord, Tile] | None = None
        self._latest_board_pixels: Any | None = None
        self._expected_flagged_coords: set[Coord] = set()
        self._expected_revealed_coords: set[Coord] = set()

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
        try:
            board_pixels = self._capture.grab(self._board_region)
            self._latest_board_pixels = board_pixels
            if self._debug_capture_dir is not None:
                dump_capture(
                    board_pixels,
                    self._debug_capture_dir / "runtime" / f"refresh_{self._refresh_index:03d}.png",
                    warn=self._output,
                )
                self._refresh_index += 1
            tiles: dict[Coord, Tile] = {}
            for x in range(self._width):
                for y in range(self._height):
                    coord = Coord(x, y)
                    tile_pixels = self._tile_pixels(board_pixels, coord)
                    tile = self._classifier.classify(tile_pixels, coord)
                    if tile.state == TileState.HIDDEN and coord in self._expected_flagged_coords:
                        tile = Tile(coord=coord, state=TileState.FLAGGED, is_mine=False)
                    elif tile.state != TileState.HIDDEN:
                        self._expected_revealed_coords.discard(coord)
                    elif tile.state != TileState.FLAGGED:
                        self._expected_flagged_coords.discard(coord)
                    tiles[coord] = tile
        except BoardReadError:
            raise
        except Exception as exc:
            raise BoardReadError("board refresh failed") from exc

        self._tiles = tiles

    def remember_moves(self, moves: list[Move] | tuple[Move, ...]) -> None:
        for move in moves:
            if move.action == ActionType.FLAG:
                self._expected_revealed_coords.discard(move.coord)
                self._expected_flagged_coords.add(move.coord)
                continue
            if move.action == ActionType.REVEAL:
                self._expected_flagged_coords.discard(move.coord)
                self._expected_revealed_coords.add(move.coord)
                continue
            self._expected_flagged_coords.discard(move.coord)
            self._expected_revealed_coords.discard(move.coord)

    def is_externally_resolved(self, coord: Coord) -> bool:
        return coord in self._expected_flagged_coords or coord in self._expected_revealed_coords

    def save_move_overlay(
        self,
        *,
        coord: Coord,
        click_point: tuple[int, int],
        label: str,
        batch_index: int,
        move_index: int,
        move_index_in_batch: int,
        batch_size: int,
        dump_overlay: Callable[..., None] = dump_move_overlay,
        write_metadata: Callable[[dict[str, object], Path, Callable[[str], None]], None] = write_debug_metadata,
    ) -> None:
        if self._debug_capture_dir is None or self._latest_board_pixels is None:
            return

        rect = self._tile_rect(coord)
        image_path = self._debug_capture_dir / "runtime" / f"move_{self._move_overlay_index:03d}.png"
        dump_overlay(
            self._latest_board_pixels,
            image_path,
            tile_bounds=(
                rect.left,
                rect.top,
                rect.left + rect.width - 1,
                rect.top + rect.height - 1,
            ),
            click_point=click_point,
            label=label,
            warn=self._output,
        )
        write_metadata(
            {
                "move_index": move_index,
                "batch_index": batch_index,
                "move_index_in_batch": move_index_in_batch,
                "batch_size": batch_size,
                "coord": {"x": coord.x, "y": coord.y},
                "click_point": {"x": click_point[0], "y": click_point[1]},
                "tile_bounds": {
                    "left": rect.left,
                    "top": rect.top,
                    "right": rect.left + rect.width - 1,
                    "bottom": rect.top + rect.height - 1,
                },
                "label": label,
            },
            image_path.with_suffix(".json"),
            warn=self._output,
        )
        self._move_overlay_index += 1

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

    def _tile_rect(self, coord: Coord) -> ScreenRegion:
        if self._grid is not None:
            return self._grid.tile_rect(coord)
        return ScreenRegion(
            left=self._board_region.left + coord.x * self._tile_size.width,
            top=self._board_region.top + coord.y * self._tile_size.height,
            width=self._tile_size.width,
            height=self._tile_size.height,
        )
