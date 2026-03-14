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

    assert TransitiveMatcher().find_moves(analysis) == [
        (ActionType.REVEAL, expected),
    ]


def test_returns_all_moves_from_multiple_known_patterns() -> None:
    left_current = Coord(1, 1)
    left_neighbor = Coord(1, 0)
    right_current = Coord(4, 1)
    right_neighbor = Coord(4, 0)
    analysis = AnalyzedBoard(
        grid={
            left_current: 1,
            left_neighbor: 1,
            right_current: 1,
            right_neighbor: 1,
        },
        frontier=[left_current, left_neighbor, right_current, right_neighbor],
        unknown_coords=frozenset(
            {
                Coord(2, -1),
                Coord(2, 0),
                Coord(2, 1),
                Coord(5, -1),
                Coord(5, 0),
                Coord(5, 1),
            }
        ),
        flagged_coords=frozenset(),
    )

    assert TransitiveMatcher().find_moves(analysis) == [
        (ActionType.REVEAL, Coord(2, -1)),
        (ActionType.REVEAL, Coord(5, -1)),
    ]


def test_no_pattern_returns_none() -> None:
    analysis = AnalyzedBoard(
        grid={Coord(1, 1): 3, Coord(1, 0): 1},
        frontier=[Coord(1, 1), Coord(1, 0)],
        unknown_coords=frozenset({Coord(2, -1), Coord(2, 0), Coord(2, 1)}),
        flagged_coords=frozenset(),
    )

    assert TransitiveMatcher().find_moves(analysis) == []


def test_only_checks_cardinal_neighbors() -> None:
    current = Coord(1, 1)
    diagonal = Coord(2, 0)
    analysis = AnalyzedBoard(
        grid={current: 1, diagonal: 1},
        frontier=[current, diagonal],
        unknown_coords=frozenset({Coord(3, -1), Coord(3, 0), Coord(3, 1)}),
        flagged_coords=frozenset(),
    )

    assert TransitiveMatcher().find_moves(analysis) == []
