from __future__ import annotations

from collections.abc import Callable, Sequence
from importlib import import_module
from typing import Any

from minesweeper.domain.move import Move
from minesweeper.domain.types import ActionType
from minesweeper.external.capture import ScreenRegion, TileSize
from minesweeper.external.grid import TileGrid


def _load_pyautogui() -> Any | None:
    try:
        return import_module("pyautogui")
    except ImportError:
        return None


class ScreenMoveExecutor:
    def __init__(
        self,
        board_region: ScreenRegion,
        tile_size: TileSize,
        grid: TileGrid | None = None,
        click_inset: int = 4,
        click_delay_ms: int = 40,
        left_click: Callable[[int, int], None] | None = None,
        right_click: Callable[[int, int], None] | None = None,
        delay: Callable[[float], None] | None = None,
        pyautogui_loader: Callable[[], Any | None] | None = None,
    ) -> None:
        self._board_region = board_region
        self._tile_size = tile_size
        self._grid = grid
        self._click_inset = click_inset
        self._click_delay_seconds = click_delay_ms / 1000
        self._pyautogui_loader = pyautogui_loader or _load_pyautogui
        self._left_click = left_click
        self._right_click = right_click
        self._delay = delay

    def execute(self, move: Move) -> None:
        point = self._screen_point(move)
        if point is None:
            return

        x, y = point
        if move.action == ActionType.REVEAL:
            self._resolve_left_click()(x, y)
            return

        self._resolve_right_click()(x, y)

    def execute_batch(self, moves: Sequence[Move]) -> None:
        ordered_moves = sorted(
            moves,
            key=lambda move: 1 if move.action == ActionType.REVEAL else 0,
        )

        for index, move in enumerate(ordered_moves):
            self.execute(move)
            if index < len(ordered_moves) - 1:
                self._resolve_delay()(self._click_delay_seconds)

    def _screen_point(self, move: Move) -> tuple[int, int] | None:
        if self._grid is not None:
            x, y = self._grid.click_target(move.coord, inset=self._click_inset)
        else:
            x = self._board_region.left + move.coord.x * self._tile_size.width + self._tile_size.width // 2
            y = self._board_region.top + move.coord.y * self._tile_size.height + self._tile_size.height // 2
        if not self._contains_point(x, y):
            return None
        return x, y

    def _contains_point(self, x: int, y: int) -> bool:
        return (
            self._board_region.left <= x < self._board_region.left + self._board_region.width
            and self._board_region.top <= y < self._board_region.top + self._board_region.height
        )

    def _resolve_left_click(self) -> Callable[[int, int], None]:
        if self._left_click is None:
            pyautogui = self._require_pyautogui()
            self._left_click = pyautogui.click
        return self._left_click

    def _resolve_right_click(self) -> Callable[[int, int], None]:
        if self._right_click is None:
            pyautogui = self._require_pyautogui()
            self._right_click = pyautogui.rightClick
        return self._right_click

    def _resolve_delay(self) -> Callable[[float], None]:
        if self._delay is None:
            pyautogui = self._require_pyautogui()
            self._delay = pyautogui.sleep
        return self._delay

    def _require_pyautogui(self) -> Any:
        pyautogui = self._pyautogui_loader()
        if pyautogui is None:
            raise RuntimeError("pyautogui is required for live move execution")
        return pyautogui
