from itertools import combinations
import math
from collections.abc import Sequence

from minesweeper.ai.analyzer import AnalyzedBoard
from minesweeper.ai.constraint import Constraint
from minesweeper.domain.move import Move
from minesweeper.domain.types import ActionType, Coord


class ProbabilitySolver:
    MAX_EXACT_TILES = 20

    def __init__(self, flag_threshold: float = 0.95) -> None:
        self._flag_threshold = flag_threshold

    @property
    def name(self) -> str:
        return "ProbabilitySolver"

    def find_moves(self, analysis: AnalyzedBoard) -> Sequence[Move]:
        unknowns = sorted(analysis.unknown_coords, key=self._sort_key)
        if not unknowns:
            return []

        remaining_mines = analysis.total_mines - len(analysis.flagged_coords)
        constraints = self._constraints(analysis)

        if not constraints:
            return [self._global_move(unknowns, remaining_mines)]

        constrained_tiles = sorted(
            {tile for constraint in constraints for tile in constraint.unknowns},
            key=self._sort_key,
        )
        unconstrained_tiles = [
            tile for tile in unknowns if tile not in set(constrained_tiles)
        ]

        if len(constrained_tiles) > self.MAX_EXACT_TILES:
            return [self._global_move(unknowns, remaining_mines)]

        probabilities = self._exact_probabilities(
            constraints=constraints,
            constrained_tiles=constrained_tiles,
            unconstrained_tiles=unconstrained_tiles,
            remaining_mines=remaining_mines,
        )
        if not probabilities:
            return [self._global_move(unknowns, remaining_mines)]

        certain_moves = self._certain_moves(probabilities)
        if certain_moves:
            return certain_moves

        return [self._best_move(probabilities)]

    def _exact_probabilities(
        self,
        constraints: list[Constraint],
        constrained_tiles: list[Coord],
        unconstrained_tiles: list[Coord],
        remaining_mines: int,
    ) -> dict[Coord, float]:
        total_weight = 0
        mine_weights = {tile: 0 for tile in constrained_tiles}
        unconstrained_mine_weight = 0.0

        max_local_mines = min(len(constrained_tiles), remaining_mines)
        for local_mines in range(max_local_mines + 1):
            for assignment_tuple in combinations(constrained_tiles, local_mines):
                assignment = set(assignment_tuple)
                if not self._satisfies_constraints(assignment, constraints):
                    continue

                mines_for_unconstrained = remaining_mines - local_mines
                if not 0 <= mines_for_unconstrained <= len(unconstrained_tiles):
                    continue

                weight = math.comb(len(unconstrained_tiles), mines_for_unconstrained)
                total_weight += weight
                for tile in assignment:
                    mine_weights[tile] += weight

                if unconstrained_tiles:
                    unconstrained_mine_weight += (
                        weight * mines_for_unconstrained / len(unconstrained_tiles)
                    )

        if total_weight == 0:
            return {}

        probabilities = {
            tile: mine_weights[tile] / total_weight for tile in constrained_tiles
        }
        if unconstrained_tiles:
            unconstrained_probability = unconstrained_mine_weight / total_weight
            for tile in unconstrained_tiles:
                probabilities[tile] = unconstrained_probability

        return probabilities

    def _best_move(self, probabilities: dict[Coord, float]) -> Move:
        highest = max(
            probabilities.items(),
            key=lambda item: (item[1], -item[0].x, -item[0].y),
        )
        if highest[1] >= self._flag_threshold:
            return Move(ActionType.FLAG, highest[0])

        lowest = min(
            probabilities.items(),
            key=lambda item: (item[1], item[0].x, item[0].y),
        )
        return Move(ActionType.REVEAL, lowest[0])

    def _global_move(self, unknowns: list[Coord], remaining_mines: int) -> Move:
        probability = remaining_mines / len(unknowns)
        action = ActionType.FLAG if probability >= self._flag_threshold else ActionType.REVEAL
        return Move(action, unknowns[0])

    def _certain_moves(self, probabilities: dict[Coord, float]) -> list[Move]:
        flags = [
            Move(ActionType.FLAG, coord)
            for coord, probability in sorted(probabilities.items(), key=lambda item: self._sort_key(item[0]))
            if probability == 1.0
        ]
        reveals = [
            Move(ActionType.REVEAL, coord)
            for coord, probability in sorted(probabilities.items(), key=lambda item: self._sort_key(item[0]))
            if probability == 0.0
        ]
        return flags + reveals

    def _constraints(self, analysis: AnalyzedBoard) -> list[Constraint]:
        constraints: list[Constraint] = []
        for coord in analysis.frontier:
            value = analysis.grid[coord]
            unknown_neighbors = frozenset(
                neighbor for neighbor in coord.neighbors() if neighbor in analysis.unknown_coords
            )
            if not unknown_neighbors:
                continue

            flagged_neighbors = sum(
                neighbor in analysis.flagged_coords for neighbor in coord.neighbors()
            )
            constraints.append(
                Constraint(
                    unknowns=unknown_neighbors,
                    mines_needed=value - flagged_neighbors,
                )
            )

        return constraints

    def _satisfies_constraints(
        self,
        assignment: set[Coord],
        constraints: list[Constraint],
    ) -> bool:
        return all(
            sum(coord in assignment for coord in constraint.unknowns) == constraint.mines_needed
            for constraint in constraints
        )

    def _sort_key(self, coord: Coord) -> tuple[int, int]:
        return (coord.x, coord.y)
