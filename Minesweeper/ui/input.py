from __future__ import annotations

from typing import NamedTuple, Sequence

import pygame

from minesweeper.domain.types import ActionType, Coord, GameMode
from minesweeper.ui.renderer import PygameRenderer


class QuitEvent(NamedTuple):
    pass


class TileClickEvent(NamedTuple):
    coord: Coord
    action: ActionType


class ToggleAIEvent(NamedTuple):
    pass


class StepAIEvent(NamedTuple):
    pass


InputEvent = QuitEvent | TileClickEvent | ToggleAIEvent | StepAIEvent


def poll_events(mode: GameMode, renderer: PygameRenderer) -> Sequence[InputEvent]:
    translated: list[InputEvent] = []
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            translated.append(QuitEvent())
            continue

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and mode.ai_togglable:
                translated.append(ToggleAIEvent())
            elif event.key == pygame.K_s and mode.ai_enabled:
                translated.append(StepAIEvent())
            continue

        if event.type == pygame.MOUSEBUTTONDOWN and mode.player_input:
            coord = renderer.board_coord_from_screen(*event.pos)
            if coord is None:
                continue

            if event.button == 1:
                translated.append(TileClickEvent(coord, ActionType.REVEAL))
            elif event.button == 3:
                translated.append(TileClickEvent(coord, ActionType.FLAG))

    return translated
