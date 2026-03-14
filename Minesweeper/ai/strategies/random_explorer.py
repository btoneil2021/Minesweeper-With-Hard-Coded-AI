import random
from typing import Optional

from minesweeper.ai.analyzer import AnalyzedBoard
from minesweeper.domain.move import Move
from minesweeper.domain.types import ActionType


class RandomExplorer:
    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()

    @property
    def name(self) -> str:
        return "RandomExplorer"

    def find_move(self, analysis: AnalyzedBoard) -> Optional[Move]:
        if not analysis.unknown_coords:
            return None

        coord = self._rng.choice(tuple(analysis.unknown_coords))
        return Move(ActionType.REVEAL, coord)
