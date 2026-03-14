from __future__ import annotations

import sys
from types import ModuleType

import minesweeper.__main__ as main_module
from minesweeper.domain.types import AI_ONLY, HYBRID, PLAYER_ONLY


def test_parse_mode_maps_cli_values_to_constants() -> None:
    assert main_module.parse_mode("player") is PLAYER_ONLY
    assert main_module.parse_mode("ai") is AI_ONLY
    assert main_module.parse_mode("hybrid") is HYBRID
    assert main_module.parse_mode("external") == "external"


def test_main_builds_app_with_cli_config(monkeypatch) -> None:
    recorded: dict[str, object] = {}

    class StubApp:
        def __init__(self, config, mode) -> None:
            recorded["config"] = config
            recorded["mode"] = mode

        def run(self) -> None:
            recorded["ran"] = True

    monkeypatch.setattr(main_module, "App", StubApp)

    exit_code = main_module.main(
        ["--mode", "hybrid", "--width", "16", "--height", "16", "--mines", "40"]
    )

    assert exit_code == 0
    assert recorded["mode"] is HYBRID
    assert recorded["config"].width == 16
    assert recorded["config"].height == 16
    assert recorded["config"].num_mines == 40
    assert recorded["ran"] is True


def test_main_supports_tile_and_font_size_flags(monkeypatch) -> None:
    recorded: dict[str, object] = {}

    class StubApp:
        def __init__(self, config, mode) -> None:
            recorded["config"] = config
            recorded["mode"] = mode

        def run(self) -> None:
            recorded["ran"] = True

    monkeypatch.setattr(main_module, "App", StubApp)

    exit_code = main_module.main(
        ["--mode", "player", "--tile-size", "24", "--font-size", "28"]
    )

    assert exit_code == 0
    assert recorded["mode"] is PLAYER_ONLY
    assert recorded["config"].tile_size_px == 24
    assert recorded["config"].font_size_px == 28
    assert recorded["ran"] is True


def test_main_runs_external_mode_via_lazy_imports(monkeypatch) -> None:
    recorded: dict[str, object] = {}

    class UnexpectedApp:
        def __init__(self, *_args, **_kwargs) -> None:
            raise AssertionError("local App should not be constructed in external mode")

    class StubCapture:
        def __init__(self) -> None:
            recorded["capture_created"] = True

    class StubWizard:
        def __init__(self, capture) -> None:
            recorded["wizard_capture"] = capture

        def run(self):
            recorded["wizard_ran"] = True
            return "calibration-result"

    class StubExternalApp:
        def __init__(self, calibration) -> None:
            recorded["calibration"] = calibration

        def run(self) -> None:
            recorded["external_ran"] = True

    monkeypatch.setattr(main_module, "App", UnexpectedApp)

    capture_module = ModuleType("minesweeper.external.capture")
    capture_module.ScreenCapture = StubCapture
    calibration_module = ModuleType("minesweeper.external.calibration")
    calibration_module.CalibrationWizard = StubWizard
    app_module = ModuleType("minesweeper.external.app")
    app_module.ExternalApp = StubExternalApp

    monkeypatch.setitem(sys.modules, "minesweeper.external.capture", capture_module)
    monkeypatch.setitem(sys.modules, "minesweeper.external.calibration", calibration_module)
    monkeypatch.setitem(sys.modules, "minesweeper.external.app", app_module)

    exit_code = main_module.main(["--mode", "external"])

    assert exit_code == 0
    assert recorded["capture_created"] is True
    assert recorded["wizard_ran"] is True
    assert recorded["calibration"] == "calibration-result"
    assert recorded["external_ran"] is True
