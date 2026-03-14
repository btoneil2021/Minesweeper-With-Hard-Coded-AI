from collections.abc import Sequence
from typing import Protocol

from minesweeper.ai.analyzer import AnalyzedBoard
from minesweeper.domain.move import Move


class AIStrategy(Protocol):
    def find_moves(self, analysis: AnalyzedBoard) -> Sequence[Move]: ...

    @property
    def name(self) -> str: ...
