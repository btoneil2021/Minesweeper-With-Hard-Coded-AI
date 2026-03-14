from typing import Optional

from minesweeper.ai.analyzer import AnalyzedBoard
from minesweeper.domain.move import Move
from minesweeper.domain.types import ActionType, Coord


class PatternDetector:
    @property
    def name(self) -> str:
        return "PatternDetector"

    def find_move(self, analysis: AnalyzedBoard) -> Optional[Move]:
        for coord in analysis.frontier:
            value = analysis.grid.get(coord)
            if value is None or value <= 0:
                continue

            unknown_neighbors = sorted(
                (neighbor for neighbor in coord.neighbors() if neighbor in analysis.unknown_coords),
                key=lambda candidate: (candidate.x, candidate.y),
            )
            flagged_count = sum(
                neighbor in analysis.flagged_coords for neighbor in coord.neighbors()
            )

            if unknown_neighbors and value == flagged_count:
                return Move(ActionType.REVEAL, unknown_neighbors[0])

            if unknown_neighbors and value - flagged_count == len(unknown_neighbors):
                return Move(ActionType.FLAG, unknown_neighbors[0])

        return None
