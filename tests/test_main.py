from __future__ import annotations

import minesweeper.__main__ as main_module
from minesweeper.domain.types import AI_ONLY, HYBRID, PLAYER_ONLY


def test_parse_mode_maps_cli_values_to_constants() -> None:
    assert main_module.parse_mode("player") is PLAYER_ONLY
    assert main_module.parse_mode("ai") is AI_ONLY
    assert main_module.parse_mode("hybrid") is HYBRID


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
