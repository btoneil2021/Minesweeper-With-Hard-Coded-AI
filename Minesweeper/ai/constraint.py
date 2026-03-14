from dataclasses import dataclass

from minesweeper.domain.types import Coord


@dataclass(frozen=True)
class Constraint:
    unknowns: frozenset[Coord]
    mines_needed: int
