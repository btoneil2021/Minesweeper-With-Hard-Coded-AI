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


def board_with_misleading_center_row(
    *,
    left_pad: int,
    top_pad: int,
    col_boundaries: tuple[int, ...],
    row_boundaries: tuple[int, ...],
    tile_color: tuple[int, int, int],
    border_color: tuple[int, int, int],
    pad_color: tuple[int, int, int],
    band_color: tuple[int, int, int],
) -> list[list[tuple[int, int, int]]]:
    pixels = board_with_padding(
        left_pad=left_pad,
        top_pad=top_pad,
        col_boundaries=col_boundaries,
        row_boundaries=row_boundaries,
        tile_color=tile_color,
        border_color=border_color,
        pad_color=pad_color,
    )

    center_y = len(pixels) // 2
    board_left = left_pad + col_boundaries[0]
    board_right = left_pad + col_boundaries[-1]
    band_width = max(1, (board_right - board_left) // 3)
    for x in range(board_left, board_right):
        band_index = min(2, (x - board_left) // band_width)
        pixels[center_y][x] = band_color if band_index % 2 == 0 else tile_color

    return pixels


def minesweeperonline_hidden_board(
    *,
    left_pad: int,
    top_pad: int,
    width_tiles: int,
    height_tiles: int,
    tile_pitch: int = 25,
) -> list[list[tuple[int, int, int]]]:
    board_width = width_tiles * tile_pitch
    board_height = height_tiles * tile_pitch
    width = left_pad + board_width + 8
    height = top_pad + board_height + 8
    bg = (192, 192, 192)
    light = (255, 255, 255)
    dark = (128, 128, 128)
    shadow = (160, 160, 160)
    revealed = (210, 210, 210)
    pixels = [[bg for _ in range(width)] for _ in range(height)]

    board_left = left_pad
    board_top = top_pad
    board_right = board_left + board_width
    board_bottom = board_top + board_height

    for tile_y in range(height_tiles):
        for tile_x in range(width_tiles):
            left = board_left + tile_x * tile_pitch
            top = board_top + tile_y * tile_pitch
            right = left + tile_pitch
            bottom = top + tile_pitch
            for y in range(top, bottom):
                for x in range(left, right):
                    pixels[y][x] = bg
            for y in range(top, bottom):
                pixels[y][left] = light
                if left + 1 < right:
                    pixels[y][left + 1] = light
                pixels[y][right - 1] = dark
                if right - 2 >= left:
                    pixels[y][right - 2] = shadow
            for x in range(left, right):
                pixels[top][x] = light
                if top + 1 < bottom:
                    pixels[top + 1][x] = light
                pixels[bottom - 1][x] = dark
                if bottom - 2 >= top:
                    pixels[bottom - 2][x] = shadow

    # Add a revealed pocket to mimic live board mixing without disturbing the global lattice.
    pocket_left = board_left + tile_pitch * 2
    pocket_top = board_top + tile_pitch * 3
    for y in range(pocket_top + 2, pocket_top + tile_pitch * 4 - 2):
        for x in range(pocket_left + 2, pocket_left + tile_pitch * 5 - 2):
            pixels[y][x] = revealed

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


def test_detect_tile_grid_ignores_misleading_center_row_when_other_rows_match() -> None:
    pixels = FakePixelGrid(
        board_with_misleading_center_row(
            left_pad=8,
            top_pad=6,
            col_boundaries=tuple(range(0, 301, 10)),
            row_boundaries=tuple(range(0, 161, 10)),
            tile_color=(180, 180, 180),
            border_color=(120, 120, 120),
            pad_color=(20, 20, 20),
            band_color=(90, 90, 90),
        )
    )

    grid = detect_tile_grid(
        pixels,
        board_left=100,
        board_top=200,
        output=lambda _message: None,
    )

    assert grid.col_boundaries == tuple(range(8, 309, 10))
    assert grid.row_boundaries == tuple(range(6, 167, 10))


def test_detect_tile_grid_fits_minesweeperonline_beveled_hidden_tiles() -> None:
    pixels = FakePixelGrid(
        minesweeperonline_hidden_board(
            left_pad=12,
            top_pad=18,
            width_tiles=30,
            height_tiles=16,
            tile_pitch=25,
        )
    )

    grid = detect_tile_grid(
        pixels,
        board_left=100,
        board_top=200,
        output=lambda _message: None,
    )

    assert grid.col_boundaries == tuple(12 + index * 25 for index in range(31))
    assert grid.row_boundaries == tuple(18 + index * 25 for index in range(17))


def test_detect_tile_grid_extends_minesweeperonline_lattice_when_last_edge_is_clipped() -> None:
    full_pixels = minesweeperonline_hidden_board(
        left_pad=12,
        top_pad=18,
        width_tiles=30,
        height_tiles=16,
        tile_pitch=25,
    )
    clipped_pixels = full_pixels[:-15]
    pixels = FakePixelGrid(clipped_pixels)

    grid = detect_tile_grid(
        pixels,
        board_left=100,
        board_top=200,
        output=lambda _message: None,
    )

    assert grid.col_boundaries == tuple(12 + index * 25 for index in range(31))
    assert grid.row_boundaries == tuple(list(18 + index * 25 for index in range(16)) + [len(clipped_pixels)])


def test_tile_grid_click_target_clamps_large_insets_inside_tiny_tiles() -> None:
    grid = TileGrid(
        origin_left=10,
        origin_top=20,
        col_boundaries=(0, 1),
        row_boundaries=(0, 1),
    )

    assert grid.click_target(Coord(0, 0), inset=4) == (10, 20)
