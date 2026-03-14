import pytest

from minesweeper.external.calibration import CalibrationResult, CalibrationWizard
from minesweeper.external.capture import ScreenRegion, TileSize
from minesweeper.external.classifier import ColorProfiles


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
        capture=object(),
        read_point=lambda prompt: prompts.append(prompt) or next(points),
        read_int=lambda prompt: prompts.append(prompt) or 12,
        profile_builder=lambda capture, board_region, tile_size: profile_calls.append((board_region, tile_size)) or profiles,
    )

    result = wizard.run()

    assert result.board_region == ScreenRegion(10, 20, 40, 40)
    assert result.tile_size == TileSize(10, 10)
    assert result.width == 4
    assert result.height == 4
    assert result.num_mines == 12
    assert result.profiles == profiles
    assert profile_calls == [(ScreenRegion(10, 20, 40, 40), TileSize(10, 10))]


def test_wizard_rejects_bad_tile_alignment() -> None:
    points = iter([(0, 0), (35, 30), (0, 0), (10, 10)])
    wizard = CalibrationWizard(
        capture=object(),
        read_point=lambda _prompt: next(points),
        read_int=lambda _prompt: 10,
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
