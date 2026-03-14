from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import NamedTuple


class Coord(NamedTuple):
    """A grid coordinate. Origin (0, 0) is top-left."""

    x: int
    y: int

    def neighbors(self) -> list["Coord"]:
        """All 8 surrounding coordinates. No bounds checking."""
        return [
            Coord(self.x + dx, self.y + dy)
            for dx in (-1, 0, 1)
            for dy in (-1, 0, 1)
            if (dx, dy) != (0, 0)
        ]


class TileState(Enum):
    """Observable state of a tile from the outside."""

    HIDDEN = auto()
    REVEALED = auto()
    FLAGGED = auto()
    EXPLODED = auto()


class ActionType(Enum):
    """What the player or AI wants to do."""

    REVEAL = auto()
    FLAG = auto()
    UNFLAG = auto()


class GamePhase(Enum):
    """High-level lifecycle of a single game."""

    NOT_STARTED = auto()
    IN_PROGRESS = auto()
    WON = auto()
    LOST = auto()


@dataclass(frozen=True)
class GameMode:
    """
    Capability-based game mode. The game loop checks flags, not identity.

    New modes are just new instances with different flag combinations.
    """

    name: str
    player_input: bool
    ai_enabled: bool
    ai_togglable: bool = False


AI_ONLY = GameMode("AI Only", player_input=False, ai_enabled=True)
PLAYER_ONLY = GameMode("Player Only", player_input=True, ai_enabled=False)
HYBRID = GameMode("Hybrid", player_input=True, ai_enabled=True, ai_togglable=True)


@dataclass(frozen=True)
class GameConfig:
    """All user-tunable knobs. Frozen so it's safe to pass around."""

    width: int = 30
    height: int = 16
    num_mines: int = 99
    tile_size_px: int = 20
    font_size_px: int = 30
    restart_delay_ms: int = 1000
    ai_click_feedback: bool = False

    def __post_init__(self) -> None:
        if self.num_mines >= self.width * self.height:
            raise ValueError(
                f"num_mines ({self.num_mines}) must be less than "
                f"total tiles ({self.width * self.height})"
            )
