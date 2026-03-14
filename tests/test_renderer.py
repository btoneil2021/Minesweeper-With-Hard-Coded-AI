from __future__ import annotations

import pygame
import pytest

from minesweeper.domain.tile import Tile
from minesweeper.domain.types import Coord, GameConfig, GameMode, TileState
from minesweeper.ui.renderer import PygameRenderer


class StubBoard:
    def __init__(self, width: int, height: int, num_mines: int, tiles: list[Tile]) -> None:
        self.width = width
        self.height = height
        self.num_mines = num_mines
        self._tiles = {tile.coord: tile for tile in tiles}

    def tile_at(self, coord: Coord) -> Tile:
        return self._tiles[coord]


@pytest.fixture(autouse=True)
def pygame_dummy_display(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    pygame.quit()
    yield
    pygame.quit()


def test_renderer_builds_procedural_flag_and_mine_surfaces() -> None:
    renderer = PygameRenderer(GameConfig(tile_size_px=24))

    assert renderer._flag_surface.get_width() > 0
    assert renderer._mine_surface.get_width() > 0
    assert renderer._exploded_mine_surface.get_width() > 0


def test_renderer_uses_bomb_asset_for_default_mine_surface(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw = pygame.Surface((8, 8), pygame.SRCALPHA)
    raw.fill((12, 34, 56, 255))
    monkeypatch.setattr(pygame.image, "load", lambda _path: raw)

    renderer = PygameRenderer(GameConfig(tile_size_px=24))
    center = (
        renderer._mine_surface.get_width() // 2,
        renderer._mine_surface.get_height() // 2,
    )

    assert renderer._mine_surface.get_at(center)[:3] == (12, 34, 56)
    assert renderer._exploded_mine_surface.get_at(center)[:3] == (12, 34, 56)


def test_renderer_falls_back_to_procedural_mine_when_asset_load_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_load(_path: object) -> pygame.Surface:
        raise FileNotFoundError("missing")

    monkeypatch.setattr(pygame.image, "load", fail_load)

    renderer = PygameRenderer(GameConfig(tile_size_px=24))

    assert renderer._mine_surface.get_width() > 0
    assert renderer._exploded_mine_surface.get_width() > 0


def test_board_coord_from_screen_unchanged_by_sprite_support() -> None:
    renderer = PygameRenderer(GameConfig(width=10, height=8, num_mines=10, tile_size_px=20))

    assert renderer.board_coord_from_screen(10, 10) is None
    assert renderer.board_coord_from_screen(
        renderer._board_rect.left + renderer._config.tile_size_px + 5,
        renderer._board_rect.top + 5,
    ) == Coord(1, 0)


def test_draw_tile_renders_flag_without_external_assets() -> None:
    renderer = PygameRenderer(GameConfig(tile_size_px=24))
    tile = Tile(coord=Coord(0, 0), state=TileState.FLAGGED, is_mine=False)
    renderer._draw_tile(tile)

    center = (
        renderer._board_rect.left + renderer._config.tile_size_px // 2,
        renderer._board_rect.top + renderer._config.tile_size_px // 2,
    )
    assert renderer._surface.get_at(center)[:3] != renderer._theme.flagged_tile


def test_draw_tile_renders_exploded_mine_without_external_assets() -> None:
    renderer = PygameRenderer(GameConfig(tile_size_px=24))
    tile = Tile(coord=Coord(0, 0), state=TileState.EXPLODED, is_mine=True)
    renderer._draw_tile(tile)

    center = (
        renderer._board_rect.left + renderer._config.tile_size_px // 2,
        renderer._board_rect.top + renderer._config.tile_size_px // 2,
    )
    assert renderer._surface.get_at(center)[:3] != renderer._theme.exploded_tile


def test_remaining_mines_counts_flagged_tiles() -> None:
    renderer = PygameRenderer(GameConfig(width=2, height=2, num_mines=3, tile_size_px=24))
    board = StubBoard(
        2,
        2,
        3,
        [
            Tile(Coord(0, 0), TileState.FLAGGED, True),
            Tile(Coord(1, 0), TileState.FLAGGED, False),
            Tile(Coord(0, 1), TileState.HIDDEN, False),
            Tile(Coord(1, 1), TileState.REVEALED, False, adjacent_mines=1),
        ],
    )

    assert renderer._remaining_mines(board) == 1


def test_board_origin_uses_header_and_frame_offsets() -> None:
    renderer = PygameRenderer(GameConfig(width=10, height=8, num_mines=10, tile_size_px=20))

    assert renderer.board_coord_from_screen(10, 10) is None
    assert renderer.board_coord_from_screen(
        renderer._board_rect.left + 5,
        renderer._board_rect.top + 5,
    ) == Coord(0, 0)


def test_renderer_caches_number_surfaces_for_classic_values() -> None:
    renderer = PygameRenderer(GameConfig(tile_size_px=24))

    assert set(renderer._number_surfaces) == {1, 2, 3, 4, 5, 6, 7, 8}
    assert renderer._number_surfaces[1].get_width() > 0


def test_renderer_uses_dark_theme_defaults() -> None:
    renderer = PygameRenderer(GameConfig(tile_size_px=24))

    assert renderer._theme.window_bg != renderer._theme.hidden_tile
    assert renderer._theme.revealed_zero != renderer._theme.hidden_tile


def test_render_draws_distinct_header_panel_background() -> None:
    renderer = PygameRenderer(GameConfig(width=2, height=2, num_mines=1, tile_size_px=24))
    board = StubBoard(
        2,
        2,
        1,
        [
            Tile(Coord(0, 0), TileState.HIDDEN, False),
            Tile(Coord(1, 0), TileState.HIDDEN, False),
            Tile(Coord(0, 1), TileState.REVEALED, False, 1),
            Tile(Coord(1, 1), TileState.HIDDEN, True),
        ],
    )

    renderer.render(board, 0.5, GameMode("Player Only", True, False), False)

    assert renderer._surface.get_at((4, 4))[:3] == renderer._theme.header_bg


def test_board_rect_includes_outer_frame_margin() -> None:
    renderer = PygameRenderer(GameConfig(width=10, height=8, num_mines=10, tile_size_px=20))

    assert renderer._board_rect.left > 0
    assert renderer._surface.get_width() > renderer._board_rect.width


def test_hidden_tile_uses_lighter_top_left_edge_for_depth() -> None:
    renderer = PygameRenderer(GameConfig(tile_size_px=24))
    tile = Tile(coord=Coord(0, 0), state=TileState.HIDDEN, is_mine=False)

    renderer._draw_tile(tile)

    edge = renderer._surface.get_at((renderer._board_rect.left + 1, renderer._board_rect.top + 1))[:3]
    center = renderer._surface.get_at(
        (
            renderer._board_rect.left + renderer._config.tile_size_px // 2,
            renderer._board_rect.top + renderer._config.tile_size_px // 2,
        )
    )[:3]
    assert sum(edge) > sum(center)


def test_revealed_zero_uses_distinct_background() -> None:
    renderer = PygameRenderer(GameConfig(tile_size_px=24))
    tile = Tile(coord=Coord(0, 0), state=TileState.REVEALED, is_mine=False, adjacent_mines=0)

    renderer._draw_tile(tile)

    center = renderer._surface.get_at(
        (
            renderer._board_rect.left + renderer._config.tile_size_px // 2,
            renderer._board_rect.top + renderer._config.tile_size_px // 2,
        )
    )[:3]
    assert center == renderer._theme.revealed_zero


def test_hidden_tile_hover_uses_highlighted_surface(monkeypatch: pytest.MonkeyPatch) -> None:
    renderer = PygameRenderer(GameConfig(width=2, height=2, num_mines=1, tile_size_px=24))
    board = StubBoard(
        2,
        2,
        1,
        [
            Tile(Coord(0, 0), TileState.HIDDEN, False),
            Tile(Coord(1, 0), TileState.HIDDEN, False),
            Tile(Coord(0, 1), TileState.HIDDEN, False),
            Tile(Coord(1, 1), TileState.HIDDEN, True),
        ],
    )
    monkeypatch.setattr(
        pygame.mouse,
        "get_pos",
        lambda: (renderer._board_rect.left + 5, renderer._board_rect.top + 5),
    )

    renderer.render(board, 0.0, GameMode("Player Only", True, False), False)

    hovered = renderer._surface.get_at(
        (
            renderer._board_rect.left + renderer._config.tile_size_px // 2,
            renderer._board_rect.top + renderer._config.tile_size_px // 2,
        )
    )[:3]
    non_hovered = renderer._surface.get_at(
        (
            renderer._board_rect.left + renderer._config.tile_size_px + renderer._config.tile_size_px // 2,
            renderer._board_rect.top + renderer._config.tile_size_px // 2,
        )
    )[:3]
    assert hovered != non_hovered


def test_header_labels_use_remaining_mines_mode_and_win_rate() -> None:
    renderer = PygameRenderer(GameConfig(width=2, height=2, num_mines=3, tile_size_px=24))
    board = StubBoard(
        2,
        2,
        3,
        [
            Tile(Coord(0, 0), TileState.FLAGGED, True),
            Tile(Coord(1, 0), TileState.FLAGGED, False),
            Tile(Coord(0, 1), TileState.HIDDEN, False),
            Tile(Coord(1, 1), TileState.REVEALED, False, adjacent_mines=1),
        ],
    )

    left, center, right = renderer._header_labels(
        board,
        0.732,
        GameMode("Hybrid", True, True, True),
        True,
    )

    assert left == "Mines 1"
    assert center == "Hybrid • AI On"
    assert right == "Win Rate 73.2%"


def test_header_accent_uses_danger_for_exploded_board() -> None:
    renderer = PygameRenderer(GameConfig(width=2, height=2, num_mines=1, tile_size_px=24))
    board = StubBoard(
        2,
        2,
        1,
        [
            Tile(Coord(0, 0), TileState.EXPLODED, True),
            Tile(Coord(1, 0), TileState.HIDDEN, False),
            Tile(Coord(0, 1), TileState.HIDDEN, False),
            Tile(Coord(1, 1), TileState.HIDDEN, False),
        ],
    )

    assert renderer._header_accent(board) == renderer._theme.exploded_tile
