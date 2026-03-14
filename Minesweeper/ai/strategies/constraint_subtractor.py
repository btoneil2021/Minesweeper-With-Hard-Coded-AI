from collections.abc import Sequence

from minesweeper.ai.analyzer import AnalyzedBoard
from minesweeper.domain.move import Move
from minesweeper.domain.types import ActionType, Coord


class ConstraintSubtractor:
    @property
    def name(self) -> str:
        return "ConstraintSubtractor"

    def find_moves(self, analysis: AnalyzedBoard) -> Sequence[Move]:
        constraints = [
            self._constraint_for(coord, analysis)
            for coord in analysis.frontier
        ]
        moves: list[Move] = []
        seen: set[Move] = set()

        for left_unknowns, left_remaining in constraints:
            for right_unknowns, right_remaining in constraints:
                if left_unknowns == right_unknowns or not right_unknowns.issubset(left_unknowns):
                    continue

                difference = sorted(
                    left_unknowns - right_unknowns,
                    key=lambda coord: (coord.x, coord.y),
                )
                remaining = left_remaining - right_remaining

                if difference and remaining == 0:
                    for coord in difference:
                        move = Move(ActionType.REVEAL, coord)
                        if move not in seen:
                            seen.add(move)
                            moves.append(move)

                if difference and remaining == len(difference):
                    for coord in difference:
                        move = Move(ActionType.FLAG, coord)
                        if move not in seen:
                            seen.add(move)
                            moves.append(move)

        return moves

    def _constraint_for(
        self,
        coord: Coord,
        analysis: AnalyzedBoard,
    ) -> tuple[frozenset[Coord], int]:
        value = analysis.grid[coord]
        unknowns = frozenset(
            neighbor for neighbor in coord.neighbors() if neighbor in analysis.unknown_coords
        )
        flagged = sum(
            neighbor in analysis.flagged_coords for neighbor in coord.neighbors()
        )
        return unknowns, value - flagged
