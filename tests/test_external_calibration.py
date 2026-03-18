from pathlib import Path

import pytest

from minesweeper.external.calibration import (
    CalibrationResult,
    CalibrationWizard,
    _GuardedClickCollector,
    _PointCaptureCancelled,
    _PointCaptureUnavailable,
    _build_live_profiles,
    _changed_tiles,
    _default_capture_point,
    _derive_dimension,
    _tile_pixels,
    _wait_for_guarded_click,
)
from minesweeper.domain.types import Coord
from minesweeper.external.capture import ScreenRegion, TileSize
from minesweeper.external.classifier import ColorProfiles
from minesweeper.external.grid import TileGrid


class FakePixelGrid:
    def __init__(self, pixels: list[list[tuple[int, int, int]]]) -> None:
        self._pixels = pixels
        self.size = (len(pixels[0]), len(pixels))

    def getpixel(self, position: tuple[int, int]) -> tuple[int, int, int]:
        x, y = position
        return self._pixels[y][x]


class SavingPixelGrid(FakePixelGrid):
    def __init__(self, pixels: list[list[tuple[int, int, int]]], saved_paths: list[Path]) -> None:
        super().__init__(pixels)
        self._saved_paths = saved_paths

    def save(self, path: Path) -> None:
        self._saved_paths.append(Path(path))


def _board_with_padding(
    *,
    width: int,
    height: int,
    col_boundaries: tuple[int, ...],
    row_boundaries: tuple[int, ...],
    tile_color: tuple[int, int, int] = (180, 180, 180),
    border_color: tuple[int, int, int] = (120, 120, 120),
    pad_color: tuple[int, int, int] = (20, 20, 20),
) -> FakePixelGrid:
    pixels = [[pad_color for _ in range(width)] for _ in range(height)]

    for y in range(row_boundaries[0], row_boundaries[-1]):
        for x in range(col_boundaries[0], col_boundaries[-1]):
            pixels[y][x] = tile_color

    for boundary in col_boundaries[:-1]:
        for y in range(row_boundaries[0], row_boundaries[-1]):
            pixels[y][boundary] = border_color

    for boundary in row_boundaries[:-1]:
        for x in range(col_boundaries[0], col_boundaries[-1]):
            pixels[boundary][x] = border_color

    return FakePixelGrid(pixels)


def _fixed_grid_detector(
    *,
    col_boundaries: tuple[int, ...],
    row_boundaries: tuple[int, ...],
):
    return lambda _pixels, region: TileGrid(
        origin_left=region.left,
        origin_top=region.top,
        col_boundaries=col_boundaries,
        row_boundaries=row_boundaries,
    )


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


class RegionAwareCapture:
    def __init__(self) -> None:
        self.calls: list[ScreenRegion] = []
        self._index = 0

    def grab(self, region: ScreenRegion) -> FakePixelGrid:
        self.calls.append(region)
        fill = (20, 20, 20) if self._index == 0 else (220, 220, 220)
        self._index += 1
        return FakePixelGrid([[fill] * region.width for _ in range(region.height)])


class FakeListener:
    def __init__(self, **_kwargs: object) -> None:
        self.stopped = False

    def __enter__(self) -> "FakeListener":
        return self

    def __exit__(self, _exc_type: object, _exc: object, _tb: object) -> None:
        return None

    def stop(self) -> None:
        self.stopped = True


class FakeKeyboardModule:
    class Key:
        shift = "shift"
        shift_l = "shift_l"
        shift_r = "shift_r"
        esc = "esc"

    Listener = FakeListener


class FakeMouseModule:
    class Button:
        left = "left"
        right = "right"

    Listener = FakeListener


class FakePynputModules:
    keyboard = FakeKeyboardModule
    mouse = FakeMouseModule


def _raise_unavailable(_prompt: str) -> tuple[int, int]:
    raise _PointCaptureUnavailable("live picker unavailable")


def _raise_cancelled(_prompt: str) -> tuple[int, int]:
    raise _PointCaptureCancelled("live picker cancelled")


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


def test_wizard_returns_detected_tile_grid_from_hidden_snapshot() -> None:
    points = iter([(10, 20), (120, 90)])
    profiles = ColorProfiles(
        hidden_bg=(20, 20, 20),
        revealed_bg=(220, 220, 220),
        flagged_bg=None,
        number_colors={},
        mine_bg=None,
    )

    result = CalibrationWizard(
        capture=FakeCapture(
            [
                _board_with_padding(
                    width=110,
                    height=70,
                    col_boundaries=(3, 34, 66, 97),
                    row_boundaries=(2, 32, 63),
                ),
                _board_with_padding(
                    width=94,
                    height=61,
                    col_boundaries=(0, 31, 63, 94),
                    row_boundaries=(0, 30, 61),
                ),
                _board_with_padding(
                    width=94,
                    height=61,
                    col_boundaries=(0, 31, 63, 94),
                    row_boundaries=(0, 30, 61),
                ),
            ]
        ),
        capture_point=lambda _prompt: next(points),
        read_int=lambda _prompt: 99,
        click=lambda _x, _y: None,
        sleep=lambda _seconds: None,
        profile_builder=lambda *_args: profiles,
        output=lambda _message: None,
    ).run()

    assert result.grid == TileGrid(
        origin_left=13,
        origin_top=22,
        col_boundaries=(0, 31, 63, 94),
        row_boundaries=(0, 30, 61),
    )
    assert result.board_region == ScreenRegion(13, 22, 94, 61)
    assert result.width == 3
    assert result.height == 2


def test_default_point_capture_falls_back_to_manual_when_live_picker_missing() -> None:
    manual_prompts: list[str] = []

    point = _default_capture_point(
        "Pick a point",
        manual_read_point=lambda prompt: manual_prompts.append(prompt) or (12, 34),
        live_picker=_raise_unavailable,
        output=lambda _message: None,
    )

    assert point == (12, 34)
    assert manual_prompts == ["Pick a point"]


def test_default_point_capture_falls_back_to_manual_when_live_picker_cancels() -> None:
    manual_prompts: list[str] = []

    point = _default_capture_point(
        "Pick a point",
        manual_read_point=lambda prompt: manual_prompts.append(prompt) or (56, 78),
        live_picker=_raise_cancelled,
        output=lambda _message: None,
    )

    assert point == (56, 78)
    assert manual_prompts == ["Pick a point"]


def test_default_point_capture_returns_live_point_when_picker_succeeds() -> None:
    manual_prompts: list[str] = []

    point = _default_capture_point(
        "Pick a point",
        manual_read_point=lambda prompt: manual_prompts.append(prompt) or (1, 2),
        live_picker=lambda _prompt: (90, 45),
        output=lambda _message: None,
    )

    assert point == (90, 45)
    assert manual_prompts == []


def test_live_picker_ignores_unmodified_clicks_until_guarded_click_arrives() -> None:
    collector = _GuardedClickCollector(
        left_button="left",
        guard_keys={"shift"},
        cancel_key="esc",
    )

    assert collector.on_click(10, 20, "left", True) is None
    assert collector.point is None

    collector.on_press("shift")
    assert collector.on_click(30, 40, "right", True) is None
    assert collector.point is None

    assert collector.on_click(50, 60, "left", True) is False
    assert collector.point == (50, 60)


def test_wait_for_guarded_click_times_out_without_input() -> None:
    with pytest.raises(_PointCaptureCancelled, match="timed out"):
        _wait_for_guarded_click(
            "Pick a point",
            output=lambda _message: None,
            timeout_seconds=0,
            pynput_loader=lambda: FakePynputModules(),
        )


def test_derive_dimension_accepts_small_alignment_drift_without_warning() -> None:
    warnings: list[str] = []

    result = _derive_dimension(
        axis_name="Board width",
        total_pixels=299,
        tile_pixels=10,
        warn=lambda message: warnings.append(message),
    )

    assert result == 30
    assert warnings == []


def test_derive_dimension_snaps_moderate_alignment_drift_with_warning() -> None:
    warnings: list[str] = []

    result = _derive_dimension(
        axis_name="Board width",
        total_pixels=296,
        tile_pixels=10,
        warn=lambda message: warnings.append(message),
    )

    assert result == 30
    assert warnings == ["Board width looked slightly off (29.60); snapping to 30 tiles."]


def test_derive_dimension_rejects_large_alignment_drift() -> None:
    with pytest.raises(ValueError, match="tile alignment"):
        _derive_dimension(
            axis_name="Board width",
            total_pixels=355,
            tile_pixels=10,
            warn=lambda _message: None,
        )


def test_wizard_derives_board_dimensions_from_detected_grid() -> None:
    points = iter([(10, 20), (50, 60)])
    prompts: list[str] = []
    profile_calls: list[tuple[int, int, TileSize]] = []
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
        grid_detector=_fixed_grid_detector(
            col_boundaries=(0, 10, 20, 30, 40),
            row_boundaries=(0, 10, 20, 30, 40),
        ),
        profile_builder=lambda before, after, width, height, tile_size, grid: profile_calls.append((width, height, tile_size)) or profiles,
    )

    result = wizard.run()

    assert result.board_region == ScreenRegion(10, 20, 40, 40)
    assert result.tile_size == TileSize(10, 10)
    assert result.width == 4
    assert result.height == 4
    assert result.num_mines == 12
    assert result.profiles == profiles
    assert profile_calls == [(4, 4, TileSize(10, 10))]


def test_wizard_prompts_for_board_bounds_and_mine_count_only() -> None:
    points = iter([(10, 20), (50, 60)])
    prompts: list[str] = []

    CalibrationWizard(
        capture=FakeCapture(
            [
                FakePixelGrid([[(20, 20, 20)] * 40 for _ in range(40)]),
                FakePixelGrid([[(220, 220, 220)] * 40 for _ in range(40)]),
            ]
        ),
        capture_point=lambda prompt: prompts.append(prompt) or next(points),
        read_point=lambda _prompt: pytest.fail("manual point reader should not be used"),
        read_int=lambda prompt: prompts.append(prompt) or 12,
        click=lambda _x, _y: None,
        sleep=lambda _seconds: None,
        grid_detector=_fixed_grid_detector(
            col_boundaries=(0, 10, 20, 30, 40),
            row_boundaries=(0, 10, 20, 30, 40),
        ),
        profile_builder=lambda *_args: ColorProfiles(
            hidden_bg=(20, 20, 20),
            revealed_bg=(220, 220, 220),
            flagged_bg=None,
            number_colors={},
            mine_bg=None,
        ),
    ).run()

    assert prompts == [
        "Capture the top-left corner of the board.",
        "Capture the bottom-right corner of the board.",
        "Enter the mine count",
    ]


def test_wizard_warns_when_board_dimensions_are_snapped() -> None:
    points = iter([(10, 20), (306, 314)])
    outputs: list[str] = []

    result = CalibrationWizard(
        capture=FakeCapture(
            [
                FakePixelGrid([[(20, 20, 20)] * 296 for _ in range(294)]),
                FakePixelGrid([[(220, 220, 220)] * 296 for _ in range(294)]),
            ]
        ),
        capture_point=lambda _prompt: next(points),
        read_int=lambda _prompt: 12,
        click=lambda _x, _y: None,
        sleep=lambda _seconds: None,
        grid_detector=_fixed_grid_detector(
            col_boundaries=tuple(range(0, 301, 10)),
            row_boundaries=tuple(range(0, 291, 10)),
        ),
        profile_builder=lambda *_args: ColorProfiles(
            hidden_bg=(20, 20, 20),
            revealed_bg=(220, 220, 220),
            flagged_bg=None,
            number_colors={},
            mine_bg=None,
        ),
        output=lambda message: outputs.append(message),
    ).run()

    assert result.width == 30
    assert result.height == 29
    assert outputs == [
        "Board width looked slightly off (29.60); snapping to 30 tiles.",
        "Board height looked slightly off (29.40); snapping to 29 tiles.",
    ]


def test_wizard_aligns_board_region_to_snapped_tile_grid_before_capture() -> None:
    points = iter([(10, 20), (306, 314)])
    capture = RegionAwareCapture()

    result = CalibrationWizard(
        capture=capture,
        capture_point=lambda _prompt: next(points),
        read_int=lambda _prompt: 12,
        click=lambda _x, _y: None,
        sleep=lambda _seconds: None,
        grid_detector=_fixed_grid_detector(
            col_boundaries=tuple(range(0, 301, 10)),
            row_boundaries=tuple(range(0, 291, 10)),
        ),
        profile_builder=lambda *_args: ColorProfiles(
            hidden_bg=(20, 20, 20),
            revealed_bg=(220, 220, 220),
            flagged_bg=None,
            number_colors={},
            mine_bg=None,
        ),
        output=lambda _message: None,
    ).run()

    aligned_region = ScreenRegion(10, 20, 300, 290)
    assert result.board_region == aligned_region
    assert capture.calls == [
        ScreenRegion(10, 20, 296, 294),
        aligned_region,
        aligned_region,
    ]


def test_wizard_rejects_bad_tile_alignment() -> None:
    points = iter([(0, 0), (365, 300)])
    wizard = CalibrationWizard(
        capture=FakeCapture([FakePixelGrid([[(20, 20, 20)] * 365 for _ in range(300)])]),
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

    with pytest.raises(ValueError, match="board content|tile alignment"):
        wizard.run()


def test_calibration_writes_before_and_after_open_captures(tmp_path: Path) -> None:
    saved_paths: list[Path] = []
    points = iter([(10, 20), (50, 60)])

    CalibrationWizard(
        capture=FakeCapture(
            [
                FakePixelGrid([[(20, 20, 20)] * 40 for _ in range(40)]),
                SavingPixelGrid([[(20, 20, 20)] * 40 for _ in range(40)], saved_paths),
                SavingPixelGrid([[(220, 220, 220)] * 40 for _ in range(40)], saved_paths),
            ]
        ),
        capture_point=lambda _prompt: next(points),
        read_int=lambda _prompt: 12,
        click=lambda _x, _y: None,
        sleep=lambda _seconds: None,
        grid_detector=_fixed_grid_detector(
            col_boundaries=(0, 10, 20, 30, 40),
            row_boundaries=(0, 10, 20, 30, 40),
        ),
        profile_builder=lambda *_args: ColorProfiles(
            hidden_bg=(20, 20, 20),
            revealed_bg=(220, 220, 220),
            flagged_bg=None,
            number_colors={},
            mine_bg=None,
        ),
        output=lambda _message: None,
        debug_capture_dir=tmp_path,
    ).run()

    assert saved_paths == [
        tmp_path / "calibration" / "board_before_open.png",
        tmp_path / "calibration" / "board_after_open.png",
    ]


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


def test_live_profile_builder_uses_variable_tile_rects_from_grid() -> None:
    before_pixels = [[(20, 20, 20)] * 10 for _ in range(9)]
    after_pixels = [[(20, 20, 20)] * 10 for _ in range(9)]

    for y in range(0, 4):
        for x in range(0, 4):
            after_pixels[y][x] = (220, 220, 220)

    for y in range(4, 9):
        for x in range(4, 10):
            after_pixels[y][x] = (220, 220, 220)
    for y in range(5, 8):
        for x in range(6, 9):
            after_pixels[y][x] = (0, 180, 0)

    profiles = _build_live_profiles(
        before_pixels=FakePixelGrid(before_pixels),
        after_pixels=FakePixelGrid(after_pixels),
        grid=TileGrid(
            origin_left=0,
            origin_top=0,
            col_boundaries=(0, 4, 10),
            row_boundaries=(0, 4, 9),
        ),
    )

    assert profiles.hidden_bg == (20, 20, 20)
    assert profiles.revealed_bg == (220, 220, 220)
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
        grid_detector=_fixed_grid_detector(
            col_boundaries=(0, 10, 20, 30, 40),
            row_boundaries=(0, 10, 20, 30, 40),
        ),
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
        grid_detector=_fixed_grid_detector(
            col_boundaries=(0, 10, 20, 30, 40),
            row_boundaries=(0, 10, 20, 30, 40),
        ),
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
    capture = FakeCapture([before, before, after])

    result = CalibrationWizard(
        capture=capture,
        read_point=lambda _prompt: next(points),
        read_int=lambda _prompt: 8,
        click=lambda _x, _y: None,
        sleep=lambda _seconds: None,
        grid_detector=_fixed_grid_detector(
            col_boundaries=(0, 5, 10),
            row_boundaries=(0, 5, 10),
        ),
    ).run()

    assert result.profiles.hidden_bg == (20, 20, 20)
    assert result.profiles.revealed_bg == (220, 220, 220)
    assert result.profiles.number_colors[1] == (0, 0, 255)
