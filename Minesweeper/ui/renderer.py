from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pygame

from minesweeper.domain.board import BoardView
from minesweeper.domain.tile import Tile
from minesweeper.domain.types import Coord, GameConfig, GameMode, TileState


@dataclass(frozen=True)
class _Theme:
    window_bg: tuple[int, int, int] = (15, 19, 31)
    header_bg: tuple[int, int, int] = (20, 26, 40)
    header_text: tuple[int, int, int] = (229, 231, 235)
    header_accent: tuple[int, int, int] = (56, 189, 248)
    success_accent: tuple[int, int, int] = (74, 222, 128)
    hidden_tile: tuple[int, int, int] = (43, 52, 74)
    revealed_tile: tuple[int, int, int] = (134, 146, 166)
    revealed_zero: tuple[int, int, int] = (112, 124, 145)
    border: tuple[int, int, int] = (23, 31, 48)
    text_primary: tuple[int, int, int] = (17, 24, 39)
    flagged_tile: tuple[int, int, int] = (181, 97, 57)
    exploded_tile: tuple[int, int, int] = (171, 59, 74)
    flag_fill: tuple[int, int, int] = (248, 113, 113)
    flag_pole: tuple[int, int, int] = (226, 232, 240)
    mine_fill: tuple[int, int, int] = (15, 23, 42)
    mine_highlight: tuple[int, int, int] = (226, 232, 240)
    exploded_mine_fill: tuple[int, int, int] = (255, 244, 247)
    number_colors: dict[int, tuple[int, int, int]] = field(
        default_factory=lambda: {
            1: (74, 134, 200),
            2: (42, 138, 42),
            3: (204, 51, 51),
            4: (25, 25, 112),
            5: (128, 0, 0),
            6: (0, 128, 128),
            7: (31, 41, 55),
            8: (107, 114, 128),
        }
    )


@dataclass(frozen=True)
class _Layout:
    header_height: int
    outer_padding: int = 12


class PygameRenderer:
    def __init__(self, config: GameConfig) -> None:
        pygame.init()
        self._config = config
        self._theme = _Theme()
        self._layout = _Layout(header_height=max(config.tile_size_px * 2, config.font_size_px + 20))
        self._status_bar_height = self._layout.header_height
        self._board_rect = pygame.Rect(
            self._layout.outer_padding,
            self._layout.header_height + self._layout.outer_padding,
            config.width * config.tile_size_px,
            config.height * config.tile_size_px,
        )
        self._surface = pygame.display.set_mode(
            (
                self._board_rect.width + self._layout.outer_padding * 2,
                self._board_rect.height + self._board_rect.top + self._layout.outer_padding,
            )
        )
        self._tile_font = pygame.font.SysFont(None, max(16, int(config.tile_size_px * 0.72)), bold=True)
        self._font = self._tile_font
        self._header_font = pygame.font.SysFont(None, max(18, config.font_size_px - 8))
        self._header_strong_font = pygame.font.SysFont(None, max(20, config.font_size_px - 4), bold=True)
        self._small_font = self._header_font
        self._number_surfaces = self._build_number_surfaces()
        self._flag_surface = self._build_flag_surface()
        bomb_surface = self._load_bomb_surface()
        self._mine_surface = bomb_surface or self._build_mine_surface(exploded=False)
        self._exploded_mine_surface = (
            bomb_surface.copy() if bomb_surface is not None else self._build_mine_surface(exploded=True)
        )
        pygame.display.set_caption("Minesweeper Rewrite")

    def render(
        self,
        board: BoardView,
        win_rate: float,
        mode: GameMode,
        ai_active: bool,
    ) -> None:
        self._surface.fill(self._theme.window_bg)
        self._draw_header_panel()
        self._draw_board_frame()
        self._draw_status(board, win_rate, mode, ai_active)
        hovered_coord = self._hovered_coord(mode)

        for x in range(board.width):
            for y in range(board.height):
                coord = Coord(x, y)
                self._draw_tile(board.tile_at(coord), hovered=coord == hovered_coord)

        pygame.display.flip()

    def board_coord_from_screen(self, screen_x: int, screen_y: int) -> Coord | None:
        board_x = screen_x - self._board_rect.left
        board_y = screen_y - self._board_rect.top
        if board_x < 0 or board_y < 0:
            return None

        tile_x = board_x // self._config.tile_size_px
        tile_y = board_y // self._config.tile_size_px
        if tile_x >= self._config.width or tile_y >= self._config.height:
            return None

        return Coord(tile_x, tile_y)

    def _draw_header_panel(self) -> None:
        pygame.draw.rect(
            self._surface,
            self._theme.header_bg,
            pygame.Rect(0, 0, self._surface.get_width(), self._layout.header_height),
        )

    def _draw_board_frame(self) -> None:
        frame_rect = self._board_rect.inflate(8, 8)
        pygame.draw.rect(self._surface, self._theme.border, frame_rect, border_radius=6)

    def _has_exploded_tile(self, board: BoardView) -> bool:
        return any(
            board.tile_at(Coord(x, y)).state == TileState.EXPLODED
            for x in range(board.width)
            for y in range(board.height)
        )

    def _all_safe_tiles_revealed(self, board: BoardView) -> bool:
        return all(
            tile.is_mine or tile.state == TileState.REVEALED
            for x in range(board.width)
            for y in range(board.height)
            for tile in [board.tile_at(Coord(x, y))]
        )

    def _header_accent(self, board: BoardView) -> tuple[int, int, int]:
        if self._has_exploded_tile(board):
            return self._theme.exploded_tile
        if self._all_safe_tiles_revealed(board):
            return self._theme.success_accent
        return self._theme.header_accent

    def _header_labels(
        self,
        board: BoardView,
        win_rate: float,
        mode: GameMode,
        ai_active: bool,
    ) -> tuple[str, str, str]:
        return (
            f"Mines {self._remaining_mines(board)}",
            f"{mode.name} • AI {'On' if ai_active else 'Off'}",
            f"Win Rate {win_rate:.1%}",
        )

    def _draw_status(self, board: BoardView, win_rate: float, mode: GameMode, ai_active: bool) -> None:
        left, center, right = self._header_labels(board, win_rate, mode, ai_active)
        accent = self._header_accent(board)

        header_rect = pygame.Rect(0, 0, self._surface.get_width(), self._layout.header_height)
        pygame.draw.line(
            self._surface,
            accent,
            (0, header_rect.bottom - 2),
            (header_rect.right, header_rect.bottom - 2),
            2,
        )

        left_surface = self._header_strong_font.render(left, True, self._theme.header_text)
        center_surface = self._header_font.render(center, True, self._theme.header_text)
        right_surface = self._header_font.render(right, True, self._theme.header_text)

        self._surface.blit(
            left_surface,
            left_surface.get_rect(midleft=(12, header_rect.centery)),
        )
        self._surface.blit(
            center_surface,
            center_surface.get_rect(center=header_rect.center),
        )
        self._surface.blit(
            right_surface,
            right_surface.get_rect(midright=(self._surface.get_width() - 12, header_rect.centery)),
        )

    def _build_number_surfaces(self) -> dict[int, pygame.Surface]:
        return {
            value: self._tile_font.render(str(value), True, self._theme.number_colors[value])
            for value in range(1, 9)
        }

    def _count_flagged(self, board: BoardView) -> int:
        return sum(
            1
            for x in range(board.width)
            for y in range(board.height)
            if board.tile_at(Coord(x, y)).state == TileState.FLAGGED
        )

    def _remaining_mines(self, board: BoardView) -> int:
        return board.num_mines - self._count_flagged(board)

    def _icon_size(self) -> int:
        return max(8, self._config.tile_size_px - 6)

    def _load_bomb_surface(self) -> pygame.Surface | None:
        path = Path(__file__).resolve().parent.parent / "resources" / "bomb.png"
        try:
            loaded = pygame.image.load(path).convert_alpha()
        except (FileNotFoundError, pygame.error):
            return None

        size = self._icon_size()
        return pygame.transform.smoothscale(loaded, (size, size))

    def _build_flag_surface(self) -> pygame.Surface:
        size = self._icon_size()
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        pole_x = max(1, int(size * 0.28))
        top_y = max(1, int(size * 0.16))
        bottom_y = max(top_y + 1, int(size * 0.82))
        pole_width = max(2, size // 8)
        pygame.draw.line(
            surface,
            self._theme.flag_pole,
            (pole_x, top_y),
            (pole_x, bottom_y),
            pole_width,
        )
        pennant = [
            (pole_x + 1, top_y + 1),
            (int(size * 0.82), int(size * 0.42)),
            (pole_x + 1, int(size * 0.68)),
        ]
        pygame.draw.polygon(surface, self._theme.flag_fill, pennant)
        pygame.draw.line(
            surface,
            self._theme.flag_pole,
            (max(1, pole_x - pole_width), bottom_y),
            (int(size * 0.56), bottom_y),
            max(2, pole_width - 1),
        )
        return surface

    def _build_mine_surface(self, exploded: bool) -> pygame.Surface:
        size = self._icon_size()
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2
        core_radius = max(3, size // 4)
        spike_color = self._theme.exploded_mine_fill if exploded else self._theme.mine_fill
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            start = (center + dx * core_radius, center + dy * core_radius)
            end = (center + dx * (core_radius + max(2, size // 6)), center + dy * (core_radius + max(2, size // 6)))
            pygame.draw.line(surface, spike_color, start, end, max(1, size // 10))
        pygame.draw.circle(surface, spike_color, (center, center), core_radius)
        highlight_radius = max(1, size // 10)
        pygame.draw.circle(
            surface,
            self._theme.mine_highlight,
            (center - highlight_radius, center - highlight_radius),
            highlight_radius,
        )
        return surface

    def _draw_centered_icon(self, rect: pygame.Rect, icon: pygame.Surface) -> None:
        self._surface.blit(icon, icon.get_rect(center=rect.center))

    def _hovered_coord(self, mode: GameMode) -> Coord | None:
        if not mode.player_input:
            return None
        return self.board_coord_from_screen(*pygame.mouse.get_pos())

    def _tile_rect(self, coord: Coord) -> pygame.Rect:
        return pygame.Rect(
            self._board_rect.left + coord.x * self._config.tile_size_px,
            self._board_rect.top + coord.y * self._config.tile_size_px,
            self._config.tile_size_px,
            self._config.tile_size_px,
        )

    def _shade(self, color: tuple[int, int, int], delta: int) -> tuple[int, int, int]:
        return tuple(max(0, min(255, channel + delta)) for channel in color)

    def _draw_tile_background(self, rect: pygame.Rect, tile: Tile, hovered: bool) -> None:
        color = self._theme.hidden_tile
        top_left = self._shade(color, 22)
        bottom_right = self._shade(color, -24)

        if tile.state == TileState.REVEALED:
            color = self._theme.revealed_zero if tile.adjacent_mines == 0 else self._theme.revealed_tile
            top_left = self._shade(color, -18)
            bottom_right = self._shade(color, 8)
        elif tile.state == TileState.FLAGGED:
            color = self._theme.flagged_tile
            top_left = self._shade(color, 18)
            bottom_right = self._shade(color, -22)
        elif tile.state == TileState.EXPLODED:
            color = self._theme.exploded_tile
            top_left = self._shade(color, 10)
            bottom_right = self._shade(color, -24)

        if hovered and tile.state in {TileState.HIDDEN, TileState.FLAGGED}:
            color = self._shade(color, 16)
            top_left = self._shade(top_left, 10)

        pygame.draw.rect(self._surface, color, rect)
        pygame.draw.line(self._surface, top_left, rect.topleft, (rect.right - 1, rect.top), 2)
        pygame.draw.line(self._surface, top_left, rect.topleft, (rect.left, rect.bottom - 1), 2)
        pygame.draw.line(
            self._surface,
            bottom_right,
            (rect.left, rect.bottom - 1),
            (rect.right - 1, rect.bottom - 1),
            2,
        )
        pygame.draw.line(
            self._surface,
            bottom_right,
            (rect.right - 1, rect.top),
            (rect.right - 1, rect.bottom - 1),
            2,
        )

    def _draw_tile_content(self, rect: pygame.Rect, tile: Tile) -> None:
        if tile.state == TileState.FLAGGED:
            self._draw_centered_icon(rect, self._flag_surface)
            return

        if tile.state == TileState.EXPLODED:
            self._draw_centered_icon(rect, self._exploded_mine_surface)
            return

        if tile.state != TileState.REVEALED or tile.adjacent_mines <= 0:
            return

        text = self._number_surfaces.get(tile.adjacent_mines)
        if text is None:
            text = self._font.render(str(tile.adjacent_mines), True, self._theme.text_primary)
        self._surface.blit(text, text.get_rect(center=rect.center))

    def _draw_tile(self, tile: Tile, hovered: bool = False) -> None:
        rect = self._tile_rect(tile.coord)
        self._draw_tile_background(rect, tile, hovered)
        self._draw_tile_content(rect, tile)
