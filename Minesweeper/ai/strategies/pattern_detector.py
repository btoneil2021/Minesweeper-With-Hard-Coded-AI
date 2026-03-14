from collections.abc import Sequence

from minesweeper.ai.analyzer import AnalyzedBoard
from minesweeper.domain.move import Move
from minesweeper.domain.types import ActionType, Coord


class PatternDetector:
    @property
    def name(self) -> str:
        return "PatternDetector"

    def find_moves(self, analysis: AnalyzedBoard) -> Sequence[Move]:
        moves: list[Move] = []
        seen: set[Move] = set()

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
                for neighbor in unknown_neighbors:
                    move = Move(ActionType.REVEAL, neighbor)
                    if move not in seen:
                        seen.add(move)
                        moves.append(move)

            if unknown_neighbors and value - flagged_count == len(unknown_neighbors):
                for neighbor in unknown_neighbors:
                    move = Move(ActionType.FLAG, neighbor)
                    if move not in seen:
                        seen.add(move)
                        moves.append(move)

        return moves
