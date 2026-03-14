import random

from minesweeper.ai.analyzer import AnalyzedBoard
from minesweeper.ai.strategies.random_explorer import RandomExplorer
from minesweeper.domain.types import ActionType, Coord


def test_returns_reveal_of_unknown_coord() -> None:
    analysis = AnalyzedBoard(
        unknown_coords=frozenset({Coord(0, 0), Coord(1, 1), Coord(2, 2)}),
    )

    move = RandomExplorer(random.Random(1234)).find_move(analysis)

    assert move is not None
    assert move.action == ActionType.REVEAL
    assert move.coord in analysis.unknown_coords


def test_returns_none_when_no_unknowns() -> None:
    analysis = AnalyzedBoard(unknown_coords=frozenset())

    assert RandomExplorer(random.Random(1234)).find_move(analysis) is None


def test_deterministic_with_seed() -> None:
    analysis = AnalyzedBoard(
        unknown_coords=frozenset({Coord(0, 0), Coord(1, 1), Coord(2, 2)}),
    )

    left = RandomExplorer(random.Random(1234)).find_move(analysis)
    right = RandomExplorer(random.Random(1234)).find_move(analysis)

    assert left == right
