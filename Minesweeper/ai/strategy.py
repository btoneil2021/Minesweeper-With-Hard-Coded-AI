from typing import Optional, Protocol

from minesweeper.ai.analyzer import AnalyzedBoard
from minesweeper.domain.move import Move


class AIStrategy(Protocol):
    def find_move(self, analysis: AnalyzedBoard) -> Optional[Move]: ...

    @property
    def name(self) -> str: ...
