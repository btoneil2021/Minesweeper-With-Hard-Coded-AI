from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

import pytest

import minesweeper.__main__ as main_module
from minesweeper.domain.types import AI_ONLY, HYBRID, PLAYER_ONLY


def test_parse_mode_maps_cli_values_to_constants() -> None:
    assert main_module.parse_mode("player") is PLAYER_ONLY
    assert main_module.parse_mode("ai") is AI_ONLY
    assert main_module.parse_mode("hybrid") is HYBRID
    assert main_module.parse_mode("external") == "external"
    assert main_module.parse_mode("browser-dom") == "browser-dom"


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

    def stub_run(**kwargs):
        recorded.update(kwargs)
        recorded["external_ran"] = True
        return "no moves available"

    monkeypatch.setattr(main_module, "App", UnexpectedApp)

    external_module = ModuleType("minesweeper.external")
    external_module.run = stub_run
    monkeypatch.setitem(sys.modules, "minesweeper.external", external_module)

    exit_code = main_module.main(["--mode", "external"])

    assert exit_code == 0
    assert recorded["output"] is None
    assert recorded["external_ran"] is True


def test_main_passes_verbose_output_to_external_mode(monkeypatch) -> None:
    recorded: dict[str, object] = {}

    class UnexpectedApp:
        def __init__(self, *_args, **_kwargs) -> None:
            raise AssertionError("local App should not be constructed in external mode")

    def stub_run(**kwargs):
        recorded.update(kwargs)
        recorded["external_ran"] = True
        return "no moves available"

    monkeypatch.setattr(main_module, "App", UnexpectedApp)

    external_module = ModuleType("minesweeper.external")
    external_module.run = stub_run
    monkeypatch.setitem(sys.modules, "minesweeper.external", external_module)

    exit_code = main_module.main(["--mode", "external", "--verbose"])

    assert exit_code == 0
    assert recorded["output"] is print
    assert recorded["external_ran"] is True


def test_main_passes_debug_capture_dir_to_external_mode(monkeypatch) -> None:
    recorded: dict[str, object] = {}

    class UnexpectedApp:
        def __init__(self, *_args, **_kwargs) -> None:
            raise AssertionError("local App should not be constructed in external mode")

    def stub_run(**kwargs):
        recorded.update(kwargs)
        recorded["external_ran"] = True
        return "no moves available"

    monkeypatch.setattr(main_module, "App", UnexpectedApp)

    external_module = ModuleType("minesweeper.external")
    external_module.run = stub_run
    monkeypatch.setitem(sys.modules, "minesweeper.external", external_module)

    exit_code = main_module.main(
        ["--mode", "external", "--debug-captures", "tmp/debug-captures"]
    )

    assert exit_code == 0
    assert recorded["debug_capture_dir"] == Path("tmp/debug-captures")
    assert recorded["external_ran"] is True


def test_main_surfaces_browser_dom_bridge_bind_failure(monkeypatch, capsys) -> None:
    class UnexpectedApp:
        def __init__(self, *_args, **_kwargs) -> None:
            raise AssertionError("local App should not be constructed in browser-dom mode")

    def raise_bind_error(**_kwargs):
        raise OSError("address already in use")

    monkeypatch.setattr(main_module, "App", UnexpectedApp)
    monkeypatch.setattr(main_module, "_run_browser_dom", raise_bind_error)

    with pytest.raises(SystemExit) as excinfo:
        main_module.main(["--mode", "browser-dom"])

    assert excinfo.value.code == 2
    assert (
        "browser-dom HTTP bridge could not bind: address already in use"
        in capsys.readouterr().err
    )
