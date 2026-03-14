import random
from collections.abc import Sequence

from minesweeper.ai.analyzer import AnalyzedBoard
from minesweeper.domain.move import Move
from minesweeper.domain.types import ActionType


class RandomExplorer:
    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()

    @property
    def name(self) -> str:
        return "RandomExplorer"

    def find_moves(self, analysis: AnalyzedBoard) -> Sequence[Move]:
        if not analysis.unknown_coords:
            return []

        coord = self._rng.choice(tuple(analysis.unknown_coords))
        return [Move(ActionType.REVEAL, coord)]
