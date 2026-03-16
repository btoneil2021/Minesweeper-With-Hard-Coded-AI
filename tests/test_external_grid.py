from minesweeper.domain.types import Coord
from minesweeper.external.capture import ScreenRegion
from minesweeper.external.grid import TileGrid, detect_tile_grid


class FakePixelGrid:
    def __init__(self, pixels: list[list[tuple[int, int, int]]]) -> None:
        self._pixels = pixels
        self.size = (len(pixels[0]), len(pixels))

    def getpixel(self, position: tuple[int, int]) -> tuple[int, int, int]:
        x, y = position
        return self._pixels[y][x]


def board_with_padding(
    *,
    left_pad: int,
    top_pad: int,
    col_boundaries: tuple[int, ...],
    row_boundaries: tuple[int, ...],
    tile_color: tuple[int, int, int],
    border_color: tuple[int, int, int],
    pad_color: tuple[int, int, int],
) -> list[list[tuple[int, int, int]]]:
    width = col_boundaries[-1] + left_pad + 4
    height = row_boundaries[-1] + top_pad + 4
    pixels = [[pad_color for _ in range(width)] for _ in range(height)]

    for y in range(top_pad + row_boundaries[0], top_pad + row_boundaries[-1]):
        for x in range(left_pad + col_boundaries[0], left_pad + col_boundaries[-1]):
            pixels[y][x] = tile_color

    for boundary in col_boundaries[:-1]:
        x = left_pad + boundary
        for y in range(top_pad + row_boundaries[0], top_pad + row_boundaries[-1]):
            pixels[y][x] = border_color

    for boundary in row_boundaries[:-1]:
        y = top_pad + boundary
        for x in range(left_pad + col_boundaries[0], left_pad + col_boundaries[-1]):
            pixels[y][x] = border_color

    return pixels


def test_tile_grid_returns_per_tile_rects_and_click_targets() -> None:
    grid = TileGrid(
        origin_left=100,
        origin_top=200,
        col_boundaries=(0, 31, 63, 94),
        row_boundaries=(0, 30, 61),
    )

    assert grid.width == 3
    assert grid.height == 2
    assert grid.tile_rect(Coord(1, 0)) == ScreenRegion(131, 200, 32, 30)
    assert grid.click_target(Coord(2, 1), inset=4) == (178, 245)


def test_detect_tile_grid_finds_boundaries_from_hidden_board_scan() -> None:
    pixels = FakePixelGrid(
        board_with_padding(
            left_pad=0,
            top_pad=0,
            col_boundaries=(3, 34, 66, 97),
            row_boundaries=(2, 32, 63),
            tile_color=(180, 180, 180),
            border_color=(120, 120, 120),
            pad_color=(20, 20, 20),
        )
    )

    grid = detect_tile_grid(
        pixels,
        board_left=400,
        board_top=500,
        output=lambda _message: None,
    )

    assert grid.col_boundaries == (3, 34, 66, 97)
    assert grid.row_boundaries == (2, 32, 63)


def test_tile_grid_click_target_clamps_large_insets_inside_tiny_tiles() -> None:
    grid = TileGrid(
        origin_left=10,
        origin_top=20,
        col_boundaries=(0, 1),
        row_boundaries=(0, 1),
    )

    assert grid.click_target(Coord(0, 0), inset=4) == (10, 20)
