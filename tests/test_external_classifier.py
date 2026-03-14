from minesweeper.domain.types import Coord, TileState
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


def test_classifier_defaults_to_hidden_for_unknown_profile() -> None:
    profiles = ColorProfiles(
        hidden_bg=(20, 20, 20),
        revealed_bg=(220, 220, 220),
        flagged_bg=(200, 0, 0),
        number_colors={1: (0, 0, 255)},
        mine_bg=None,
    )

    tile = TileClassifier(profiles).classify(
        make_tile(background=(255, 0, 255)),
        Coord(0, 0),
    )

    assert tile.state == TileState.HIDDEN
    assert tile.adjacent_mines == 0
