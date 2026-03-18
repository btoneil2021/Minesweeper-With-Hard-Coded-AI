from pathlib import Path

from minesweeper.external.calibration import CalibrationResult
from minesweeper.external.api import calibrate, read_once, run
from minesweeper.external.config import DiagnosticsConfig, RetryPolicy, TimingConfig
from minesweeper.external.capture import ScreenRegion, TileSize
from minesweeper.external.classifier import ColorProfiles
from minesweeper.external.errors import BoardReadError, CalibrationError
from minesweeper.external.grid import TileGrid
from minesweeper.external.runtime import STOP_REASONS
from minesweeper.external.debug_capture import dump_capture, dump_move_overlay, write_debug_metadata


def test_external_api_exports_spec_entrypoints() -> None:
    assert callable(calibrate)
    assert callable(read_once)
    assert callable(run)


def test_external_config_defaults_match_spec() -> None:
    assert TimingConfig().post_batch_settle_ms == 400
    assert RetryPolicy().board_read_retries == 1
    assert DiagnosticsConfig().mode == "off"


def test_run_applies_adapter_timing_and_classifier_overrides(monkeypatch) -> None:
    recorded: dict[str, object] = {}

    class FakeAdapter:
        def classifier_config(self) -> dict[str, object]:
            recorded["classifier_config_called"] = True
            return {"background_threshold": 12.0}

        def timing_config(self) -> TimingConfig:
            recorded["timing_config_called"] = True
            return TimingConfig(post_batch_settle_ms=50, inter_click_delay_ms=25)

    class StubClassifier:
        def __init__(self, profiles, **kwargs) -> None:
            recorded["classifier_profiles"] = profiles
            recorded["classifier_kwargs"] = kwargs

    class StubExternalApp:
        def __init__(self, calibration, settle_delay_ms, classifier=None, **kwargs) -> None:
            recorded["app_calibration"] = calibration
            recorded["settle_delay_ms"] = settle_delay_ms
            recorded["classifier"] = classifier
            recorded.update(kwargs)

        def run(self) -> str:
            return "no moves available"

    monkeypatch.setattr("minesweeper.external.api.TileClassifier", StubClassifier)
    monkeypatch.setattr("minesweeper.external.api.ExternalApp", StubExternalApp)

    reason = run(
        calibration=CalibrationResult(
            board_region=ScreenRegion(0, 0, 10, 10),
            tile_size=TileSize(10, 10),
            width=1,
            height=1,
            num_mines=1,
            profiles=ColorProfiles(
                hidden_bg=(20, 20, 20),
                revealed_bg=(220, 220, 220),
                flagged_bg=None,
                number_colors={},
                mine_bg=None,
            ),
            grid=TileGrid(
                origin_left=0,
                origin_top=0,
                col_boundaries=(0, 10),
                row_boundaries=(0, 10),
            ),
        ),
        adapter=FakeAdapter(),
    )

    assert reason == "no moves available"
    assert recorded["classifier_config_called"] is True
    assert recorded["timing_config_called"] is True
    assert recorded["classifier_kwargs"] == {"background_threshold": 12.0}
    assert recorded["settle_delay_ms"] == 50
    assert recorded["click_delay_ms"] == 25


def test_run_writes_failure_artifacts_in_failure_only_mode(tmp_path: Path) -> None:
    class ExplodingBoardReader:
        width = 1
        height = 1
        num_mines = 0

        def refresh(self) -> None:
            raise BoardReadError("boom")

        def tile_at(self, _coord) -> None:
            raise KeyError(_coord)

    reason = run(
        calibration=CalibrationResult(
            board_region=ScreenRegion(0, 0, 10, 10),
            tile_size=TileSize(10, 10),
            width=1,
            height=1,
            num_mines=1,
            profiles=ColorProfiles(
                hidden_bg=(20, 20, 20),
                revealed_bg=(220, 220, 220),
                flagged_bg=None,
                number_colors={},
                mine_bg=None,
            ),
            grid=TileGrid(
                origin_left=0,
                origin_top=0,
                col_boundaries=(0, 10),
                row_boundaries=(0, 10),
            ),
        ),
        board_reader=ExplodingBoardReader(),
        diagnostics=DiagnosticsConfig(
            mode="failure-only",
            debug_root=tmp_path,
            capture_artifacts=True,
        ),
    )

    assert reason == STOP_REASONS.board_refresh_failed_after_retry
    assert (tmp_path / "session.json").exists()
    assert (tmp_path / "failures" / "latest_failure.json").exists()


def test_run_passes_retry_policy_into_external_app(monkeypatch) -> None:
    recorded: dict[str, object] = {}

    class StubExternalApp:
        def __init__(self, _calibration, **kwargs) -> None:
            recorded.update(kwargs)

        def run(self) -> str:
            return "no moves available"

    monkeypatch.setattr("minesweeper.external.api.ExternalApp", StubExternalApp)

    reason = run(
        calibration=CalibrationResult(
            board_region=ScreenRegion(0, 0, 10, 10),
            tile_size=TileSize(10, 10),
            width=1,
            height=1,
            num_mines=1,
            profiles=ColorProfiles(
                hidden_bg=(20, 20, 20),
                revealed_bg=(220, 220, 220),
                flagged_bg=None,
                number_colors={},
                mine_bg=None,
            ),
            grid=TileGrid(
                origin_left=0,
                origin_top=0,
                col_boundaries=(0, 10),
                row_boundaries=(0, 10),
            ),
        ),
        retry=RetryPolicy(board_read_retries=0, unchanged_board_retries=2),
    )

    assert reason == "no moves available"
    assert recorded["board_read_retries"] == 0
    assert recorded["unchanged_board_retries"] == 2


def test_calibrate_wraps_wizard_failures_in_calibration_error(monkeypatch) -> None:
    class StubWizard:
        def __init__(self, *_args, **_kwargs) -> None:
            return None

        def run(self) -> None:
            raise ValueError("bad calibration")

    monkeypatch.setattr("minesweeper.external.api.CalibrationWizard", StubWizard)

    try:
        calibrate(capture=object())
    except CalibrationError as exc:
        assert "bad calibration" in str(exc)
    else:
        raise AssertionError("calibrate() should wrap wizard failures")


def test_run_returns_calibration_failed_when_public_calibrate_fails(monkeypatch) -> None:
    def stub_calibrate(**_kwargs):
        raise CalibrationError("bad calibration")

    monkeypatch.setattr("minesweeper.external.api.calibrate", stub_calibrate)

    reason = run(calibration=None)

    assert reason == STOP_REASONS.calibration_failed


def test_debug_capture_helper_saves_image_like_objects(tmp_path: Path) -> None:
    saved: list[Path] = []

    class FakeImage:
        def save(self, path: Path) -> None:
            saved.append(Path(path))

    dump_capture(FakeImage(), tmp_path / "capture.png", warn=lambda _message: None)

    assert saved == [tmp_path / "capture.png"]


def test_debug_capture_helper_writes_move_overlay_with_tile_and_click_annotations(
    tmp_path: Path,
) -> None:
    saved: list[Path] = []
    operations: list[tuple[str, object]] = []

    class FakeImage:
        def copy(self):
            operations.append(("copy", None))
            return self

        def save(self, path: Path) -> None:
            saved.append(Path(path))

    class FakeDraw:
        def rectangle(self, bounds, outline=None, width=1) -> None:
            operations.append(("rectangle", bounds, outline, width))

        def line(self, points, fill=None, width=1) -> None:
            operations.append(("line", tuple(points), fill, width))

        def ellipse(self, bounds, fill=None, outline=None, width=1) -> None:
            operations.append(("ellipse", bounds, fill, outline, width))

        def text(self, position, text, fill=None) -> None:
            operations.append(("text", position, text, fill))

    dump_move_overlay(
        FakeImage(),
        tmp_path / "move.png",
        tile_bounds=(10, 20, 19, 29),
        click_point=(15, 25),
        label="REVEAL (1,2)",
        warn=lambda _message: None,
        draw_factory=lambda image: FakeDraw(),
    )

    assert saved == [tmp_path / "move.png"]
    assert ("copy", None) in operations
    assert ("rectangle", (10, 20, 19, 29), "#ff00ff", 3) in operations
    assert ("rectangle", (12, 22, 17, 27), "#ffff00", 1) in operations
    assert ("line", ((15, 20), (15, 29)), "#00ffff", 1) in operations
    assert ("line", ((10, 25), (19, 25)), "#00ffff", 1) in operations
    assert ("ellipse", (12, 22, 18, 28), "#00ffff", "white", 1) in operations
    assert ("text", (10, 8), "REVEAL (1,2)", "#ff00ff") in operations


def test_debug_capture_helper_writes_json_metadata(tmp_path: Path) -> None:
    write_debug_metadata(
        {"move_index": 3, "coord": {"x": 4, "y": 5}},
        tmp_path / "move.json",
        warn=lambda _message: None,
    )

    assert (tmp_path / "move.json").read_text(encoding="utf-8") == (
        '{\n'
        '  "move_index": 3,\n'
        '  "coord": {\n'
        '    "x": 4,\n'
        '    "y": 5\n'
        '  }\n'
        '}'
    )
