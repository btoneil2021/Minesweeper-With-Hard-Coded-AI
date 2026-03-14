import pytest

from minesweeper.external.calibration import (
    CalibrationResult,
    CalibrationWizard,
    _build_live_profiles,
    _changed_tiles,
    _tile_pixels,
)
from minesweeper.domain.types import Coord
from minesweeper.external.capture import ScreenRegion, TileSize
from minesweeper.external.classifier import ColorProfiles


class FakePixelGrid:
    def __init__(self, pixels: list[list[tuple[int, int, int]]]) -> None:
        self._pixels = pixels
        self.size = (len(pixels[0]), len(pixels))

    def getpixel(self, position: tuple[int, int]) -> tuple[int, int, int]:
        x, y = position
        return self._pixels[y][x]


class FakeCapture:
    def __init__(self, snapshots: list[FakePixelGrid]) -> None:
        self._snapshots = snapshots
        self.calls: list[ScreenRegion] = []
        self._index = 0

    def grab(self, region: ScreenRegion) -> FakePixelGrid:
        self.calls.append(region)
        snapshot = self._snapshots[min(self._index, len(self._snapshots) - 1)]
        self._index += 1
        return snapshot


def test_calibration_result_carries_shared_geometry_and_profiles() -> None:
    profiles = ColorProfiles(
        hidden_bg=(20, 20, 20),
        revealed_bg=(220, 220, 220),
        flagged_bg=None,
        number_colors={1: (0, 0, 255)},
        mine_bg=None,
    )

    result = CalibrationResult(
        board_region=ScreenRegion(10, 20, 90, 120),
        tile_size=TileSize(15, 15),
        width=6,
        height=8,
        num_mines=10,
        profiles=profiles,
    )

    assert result.board_region == ScreenRegion(10, 20, 90, 120)
    assert result.tile_size == TileSize(15, 15)
    assert result.width == 6
    assert result.height == 8
    assert result.num_mines == 10
    assert result.profiles is profiles


def test_wizard_derives_board_dimensions_from_region_and_tile_size() -> None:
    points = iter([(10, 20), (50, 60), (10, 20), (20, 30)])
    prompts: list[str] = []
    profile_calls: list[tuple[ScreenRegion, TileSize]] = []
    profiles = ColorProfiles(
        hidden_bg=(20, 20, 20),
        revealed_bg=(220, 220, 220),
        flagged_bg=None,
        number_colors={},
        mine_bg=None,
    )

    wizard = CalibrationWizard(
        capture=FakeCapture(
            [
                FakePixelGrid([[(20, 20, 20)] * 40 for _ in range(40)]),
                FakePixelGrid([[(220, 220, 220)] * 40 for _ in range(40)]),
            ]
        ),
        read_point=lambda prompt: prompts.append(prompt) or next(points),
        read_int=lambda prompt: prompts.append(prompt) or 12,
        click=lambda _x, _y: None,
        sleep=lambda _seconds: None,
        profile_builder=lambda before, after, width, height, tile_size: profile_calls.append((width, height, tile_size)) or profiles,
    )

    result = wizard.run()

    assert result.board_region == ScreenRegion(10, 20, 40, 40)
    assert result.tile_size == TileSize(10, 10)
    assert result.width == 4
    assert result.height == 4
    assert result.num_mines == 12
    assert result.profiles == profiles
    assert profile_calls == [(4, 4, TileSize(10, 10))]


def test_wizard_rejects_bad_tile_alignment() -> None:
    points = iter([(0, 0), (35, 30), (0, 0), (10, 10)])
    wizard = CalibrationWizard(
        capture=FakeCapture([FakePixelGrid([[(20, 20, 20)] * 35 for _ in range(30)])]),
        read_point=lambda _prompt: next(points),
        read_int=lambda _prompt: 10,
        click=lambda _x, _y: None,
        sleep=lambda _seconds: None,
        profile_builder=lambda *_args: ColorProfiles(
            hidden_bg=(20, 20, 20),
            revealed_bg=(220, 220, 220),
            flagged_bg=None,
            number_colors={},
            mine_bg=None,
        ),
    )

    with pytest.raises(ValueError, match="tile alignment"):
        wizard.run()


def test_calibration_extracts_one_tile_snapshot_from_board_pixels() -> None:
    board_pixels = FakePixelGrid(
        [
            [(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0)],
            [(0, 1, 0), (1, 1, 0), (2, 1, 0), (3, 1, 0)],
            [(0, 2, 0), (1, 2, 0), (2, 2, 0), (3, 2, 0)],
            [(0, 3, 0), (1, 3, 0), (2, 3, 0), (3, 3, 0)],
        ]
    )

    tile = _tile_pixels(board_pixels, Coord(1, 0), TileSize(2, 2))

    assert tile.size == (2, 2)
    assert tile.getpixel((0, 0)) == (2, 0, 0)
    assert tile.getpixel((1, 1)) == (3, 1, 0)


def test_calibration_detects_changed_tiles_between_snapshots() -> None:
    before = FakePixelGrid(
        [
            [(10, 10, 10), (10, 10, 10), (20, 20, 20), (20, 20, 20)],
            [(10, 10, 10), (10, 10, 10), (20, 20, 20), (20, 20, 20)],
            [(30, 30, 30), (30, 30, 30), (40, 40, 40), (40, 40, 40)],
            [(30, 30, 30), (30, 30, 30), (40, 40, 40), (40, 40, 40)],
        ]
    )
    after = FakePixelGrid(
        [
            [(10, 10, 10), (10, 10, 10), (20, 20, 20), (20, 20, 20)],
            [(10, 10, 10), (10, 10, 10), (20, 20, 20), (20, 20, 20)],
            [(30, 30, 30), (30, 30, 30), (200, 200, 200), (200, 200, 200)],
            [(30, 30, 30), (30, 30, 30), (200, 200, 200), (200, 200, 200)],
        ]
    )

    changed = _changed_tiles(
        before_pixels=before,
        after_pixels=after,
        width=2,
        height=2,
        tile_size=TileSize(2, 2),
    )

    assert changed == [Coord(1, 1)]


def test_live_profile_builder_learns_hidden_and_revealed_backgrounds() -> None:
    before = FakePixelGrid(
        [
            [(20, 20, 20)] * 10,
            [(20, 20, 20)] * 10,
            [(20, 20, 20)] * 10,
            [(20, 20, 20)] * 10,
            [(20, 20, 20)] * 10,
            [(20, 20, 20)] * 10,
            [(20, 20, 20)] * 10,
            [(20, 20, 20)] * 10,
            [(20, 20, 20)] * 10,
            [(20, 20, 20)] * 10,
        ]
    )
    after_pixels = [[(20, 20, 20)] * 10 for _ in range(10)]
    for y in range(0, 5):
        for x in range(0, 5):
            after_pixels[y][x] = (220, 220, 220)
    for y in range(5, 10):
        for x in range(5, 10):
            after_pixels[y][x] = (220, 220, 220)
    for y in range(6, 9):
        for x in range(6, 9):
            after_pixels[y][x] = (0, 0, 255)
    after = FakePixelGrid(after_pixels)

    profiles = _build_live_profiles(
        before_pixels=before,
        after_pixels=after,
        width=2,
        height=2,
        tile_size=TileSize(5, 5),
    )

    assert profiles.hidden_bg == (20, 20, 20)
    assert profiles.revealed_bg == (220, 220, 220)


def test_live_profile_builder_collects_visible_number_colors() -> None:
    before = FakePixelGrid([[(20, 20, 20)] * 10 for _ in range(10)])
    after_pixels = [[(20, 20, 20)] * 10 for _ in range(10)]
    for y in range(0, 5):
        for x in range(0, 5):
            after_pixels[y][x] = (220, 220, 220)
    for y in range(5, 10):
        for x in range(5, 10):
            after_pixels[y][x] = (220, 220, 220)
    for y in range(6, 9):
        for x in range(6, 9):
            after_pixels[y][x] = (0, 180, 0)
    after = FakePixelGrid(after_pixels)

    profiles = _build_live_profiles(
        before_pixels=before,
        after_pixels=after,
        width=2,
        height=2,
        tile_size=TileSize(5, 5),
    )

    assert profiles.number_colors[2] == (0, 180, 0)


def test_live_profile_builder_fails_when_no_tiles_change() -> None:
    before = FakePixelGrid([[(20, 20, 20)] * 10 for _ in range(10)])
    after = FakePixelGrid([[(20, 20, 20)] * 10 for _ in range(10)])

    with pytest.raises(ValueError, match="No changed tiles"):
        _build_live_profiles(
            before_pixels=before,
            after_pixels=after,
            width=2,
            height=2,
            tile_size=TileSize(5, 5),
        )


def test_wizard_clicks_board_center_before_second_capture() -> None:
    points = iter([(10, 20), (50, 60), (10, 20), (20, 30)])
    clicks: list[tuple[int, int]] = []
    capture = FakeCapture(
        [
            FakePixelGrid([[(20, 20, 20)] * 40 for _ in range(40)]),
            FakePixelGrid([[(220, 220, 220)] * 40 for _ in range(40)]),
        ]
    )

    CalibrationWizard(
        capture=capture,
        read_point=lambda _prompt: next(points),
        read_int=lambda _prompt: 12,
        click=lambda x, y: clicks.append((x, y)),
        sleep=lambda _seconds: None,
        profile_builder=lambda *_args: ColorProfiles(
            hidden_bg=(20, 20, 20),
            revealed_bg=(220, 220, 220),
            flagged_bg=None,
            number_colors={},
            mine_bg=None,
        ),
    ).run()

    assert clicks == [(35, 45)]


def test_wizard_waits_for_settle_after_first_click() -> None:
    points = iter([(10, 20), (50, 60), (10, 20), (20, 30)])
    sleeps: list[float] = []
    capture = FakeCapture(
        [
            FakePixelGrid([[(20, 20, 20)] * 40 for _ in range(40)]),
            FakePixelGrid([[(220, 220, 220)] * 40 for _ in range(40)]),
        ]
    )

    CalibrationWizard(
        capture=capture,
        read_point=lambda _prompt: next(points),
        read_int=lambda _prompt: 12,
        click=lambda _x, _y: None,
        sleep=lambda seconds: sleeps.append(seconds),
        settle_delay_ms=750,
        profile_builder=lambda *_args: ColorProfiles(
            hidden_bg=(20, 20, 20),
            revealed_bg=(220, 220, 220),
            flagged_bg=None,
            number_colors={},
            mine_bg=None,
        ),
    ).run()

    assert sleeps == [0.75]


def test_wizard_run_returns_profiles_learned_from_live_snapshots() -> None:
    points = iter([(0, 0), (10, 10), (0, 0), (5, 5)])
    before = FakePixelGrid([[(20, 20, 20)] * 10 for _ in range(10)])
    after_pixels = [[(20, 20, 20)] * 10 for _ in range(10)]
    for y in range(0, 5):
        for x in range(0, 5):
            after_pixels[y][x] = (220, 220, 220)
    for y in range(5, 10):
        for x in range(5, 10):
            after_pixels[y][x] = (220, 220, 220)
    for y in range(6, 9):
        for x in range(6, 9):
            after_pixels[y][x] = (0, 0, 255)
    after = FakePixelGrid(after_pixels)
    capture = FakeCapture([before, after])

    result = CalibrationWizard(
        capture=capture,
        read_point=lambda _prompt: next(points),
        read_int=lambda _prompt: 8,
        click=lambda _x, _y: None,
        sleep=lambda _seconds: None,
    ).run()

    assert result.profiles.hidden_bg == (20, 20, 20)
    assert result.profiles.revealed_bg == (220, 220, 220)
    assert result.profiles.number_colors[1] == (0, 0, 255)
