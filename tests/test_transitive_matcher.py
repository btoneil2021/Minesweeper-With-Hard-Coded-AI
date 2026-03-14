from minesweeper.ai.analyzer import AnalyzedBoard
from minesweeper.ai.strategies.transitive_matcher import TransitiveMatcher
from minesweeper.domain.types import ActionType, Coord


def test_known_pattern_produces_move() -> None:
    current = Coord(1, 1)
    neighbor = Coord(1, 0)
    expected = Coord(2, -1)
    analysis = AnalyzedBoard(
        grid={current: 1, neighbor: 1},
        frontier=[current, neighbor],
        unknown_coords=frozenset({Coord(2, -1), Coord(2, 0), Coord(2, 1)}),
        flagged_coords=frozenset(),
    )

    move = TransitiveMatcher().find_move(analysis)

    assert move is not None
    assert move.action == ActionType.REVEAL
    assert move.coord == expected


def test_no_pattern_returns_none() -> None:
    analysis = AnalyzedBoard(
        grid={Coord(1, 1): 3, Coord(1, 0): 1},
        frontier=[Coord(1, 1), Coord(1, 0)],
        unknown_coords=frozenset({Coord(2, -1), Coord(2, 0), Coord(2, 1)}),
        flagged_coords=frozenset(),
    )

    assert TransitiveMatcher().find_move(analysis) is None


def test_only_checks_cardinal_neighbors() -> None:
    current = Coord(1, 1)
    diagonal = Coord(2, 0)
    analysis = AnalyzedBoard(
        grid={current: 1, diagonal: 1},
        frontier=[current, diagonal],
        unknown_coords=frozenset({Coord(3, -1), Coord(3, 0), Coord(3, 1)}),
        flagged_coords=frozenset(),
    )

    assert TransitiveMatcher().find_move(analysis) is None
