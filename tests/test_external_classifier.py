import pytest

from minesweeper.domain.types import Coord, TileState
from minesweeper.external.errors import BoardReadError
from minesweeper.external.classifier import ColorProfiles, TileClassifier, color_distance


class FakePixelGrid:
    def __init__(self, pixels: list[list[tuple[int, int, int]]]) -> None:
        self._pixels = pixels
        self.size = (len(pixels[0]), len(pixels))

    def getpixel(self, position: tuple[int, int]) -> tuple[int, int, int]:
        x, y = position
        return self._pixels[y][x]


def make_tile(
    background: tuple[int, int, int],
    center: tuple[int, int, int] | None = None,
    size: int = 7,
) -> FakePixelGrid:
    pixels = [[background for _ in range(size)] for _ in range(size)]
    if center is not None:
        middle = size // 2
        for y in range(middle - 1, middle + 2):
            for x in range(middle - 1, middle + 2):
                pixels[y][x] = center
    return FakePixelGrid(pixels)


def make_tile_with_accent(
    background: tuple[int, int, int],
    accent: tuple[int, int, int],
    accent_origin: tuple[int, int],
    accent_size: int = 2,
    size: int = 7,
) -> FakePixelGrid:
    pixels = [[background for _ in range(size)] for _ in range(size)]
    start_x, start_y = accent_origin
    for y in range(start_y, min(size, start_y + accent_size)):
        for x in range(start_x, min(size, start_x + accent_size)):
            pixels[y][x] = accent
    return FakePixelGrid(pixels)


def make_tile_with_outer_frame(
    background: tuple[int, int, int],
    frame: tuple[int, int, int],
    size: int = 7,
) -> FakePixelGrid:
    pixels = [[background for _ in range(size)] for _ in range(size)]
    for index in range(size):
        pixels[0][index] = frame
        pixels[size - 1][index] = frame
        pixels[index][0] = frame
        pixels[index][size - 1] = frame
    return FakePixelGrid(pixels)


def test_color_distance_is_zero_for_identical_colors() -> None:
    assert color_distance((10, 20, 30), (10, 20, 30)) == 0.0


def test_classifier_returns_hidden_tile_for_matching_hidden_background() -> None:
    profiles = ColorProfiles(
        hidden_bg=(20, 20, 20),
        revealed_bg=(220, 220, 220),
        flagged_bg=(200, 0, 0),
        number_colors={1: (0, 0, 255)},
        mine_bg=None,
    )

    tile = TileClassifier(profiles).classify(
        make_tile(background=profiles.hidden_bg),
        Coord(2, 3),
    )

    assert tile.coord == Coord(2, 3)
    assert tile.state == TileState.HIDDEN
    assert tile.adjacent_mines == 0
    assert tile.is_mine is False


def test_classifier_returns_revealed_number_for_center_accent_color() -> None:
    profiles = ColorProfiles(
        hidden_bg=(20, 20, 20),
        revealed_bg=(220, 220, 220),
        flagged_bg=(200, 0, 0),
        number_colors={
            1: (0, 0, 255),
            2: (0, 180, 0),
        },
        mine_bg=None,
    )

    tile = TileClassifier(profiles).classify(
        make_tile(background=profiles.revealed_bg, center=(0, 0, 255)),
        Coord(1, 1),
    )

    assert tile.state == TileState.REVEALED
    assert tile.adjacent_mines == 1
    assert tile.is_mine is False


def test_classifier_returns_revealed_number_for_off_center_accent_color() -> None:
    profiles = ColorProfiles(
        hidden_bg=(20, 20, 20),
        revealed_bg=(220, 220, 220),
        flagged_bg=(200, 0, 0),
        number_colors={
            2: (0, 180, 0),
        },
        mine_bg=None,
    )

    tile = TileClassifier(profiles).classify(
        make_tile_with_accent(
            background=profiles.revealed_bg,
            accent=(0, 180, 0),
            accent_origin=(1, 4),
        ),
        Coord(1, 1),
    )

    assert tile.state == TileState.REVEALED
    assert tile.adjacent_mines == 2
    assert tile.is_mine is False


def test_classifier_raises_for_unknown_profile() -> None:
    profiles = ColorProfiles(
        hidden_bg=(20, 20, 20),
        revealed_bg=(220, 220, 220),
        flagged_bg=(200, 0, 0),
        number_colors={1: (0, 0, 255)},
        mine_bg=None,
    )

    with pytest.raises(BoardReadError):
        TileClassifier(profiles).classify(
            make_tile(background=(255, 0, 255)),
            Coord(0, 0),
        )


def test_classifier_ignores_outer_board_frame_when_matching_background() -> None:
    profiles = ColorProfiles(
        hidden_bg=(20, 20, 20),
        revealed_bg=(220, 220, 220),
        flagged_bg=(200, 0, 0),
        number_colors={},
        mine_bg=None,
    )

    tile = TileClassifier(profiles).classify(
        make_tile_with_outer_frame(
            background=profiles.revealed_bg,
            frame=(0, 0, 0),
            size=9,
        ),
        Coord(0, 0),
    )

    assert tile.state == TileState.REVEALED
    assert tile.adjacent_mines == 0


def test_classifier_treats_bright_uniform_tile_as_revealed_zero_when_backgrounds_are_dimmer() -> None:
    profiles = ColorProfiles(
        hidden_bg=(190, 190, 190),
        revealed_bg=(176, 177, 177),
        flagged_bg=None,
        number_colors={},
        mine_bg=None,
    )

    tile = TileClassifier(profiles).classify(
        make_tile(background=(237, 237, 237), size=9),
        Coord(24, 12),
    )

    assert tile.state == TileState.REVEALED
    assert tile.adjacent_mines == 0


def test_classifier_treats_red_center_accent_as_flagged_without_flag_background_profile() -> None:
    profiles = ColorProfiles(
        hidden_bg=(189, 189, 189),
        revealed_bg=(180, 181, 181),
        flagged_bg=None,
        number_colors={},
        mine_bg=None,
    )

    tile = TileClassifier(profiles).classify(
        make_tile(background=profiles.hidden_bg, center=(220, 0, 0), size=9),
        Coord(12, 5),
    )

    assert tile.state == TileState.FLAGGED
    assert tile.adjacent_mines == 0


def test_classifier_uses_site_palette_for_numbers_when_calibration_has_not_seen_them_yet() -> None:
    profiles = ColorProfiles(
        hidden_bg=(189, 189, 189),
        revealed_bg=(180, 181, 181),
        flagged_bg=None,
        number_colors={},
        mine_bg=None,
    )

    tile = TileClassifier(profiles).classify(
        make_tile(background=profiles.revealed_bg, center=(0, 0, 255), size=9),
        Coord(8, 4),
    )

    assert tile.state == TileState.REVEALED
    assert tile.adjacent_mines == 1
