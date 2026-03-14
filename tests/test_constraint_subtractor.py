from minesweeper.ai.analyzer import AnalyzedBoard
from minesweeper.ai.strategies.constraint_subtractor import ConstraintSubtractor
from minesweeper.domain.types import ActionType, Coord


def test_subset_deduction_reveals_safe() -> None:
    a = Coord(1, 1)
    b = Coord(1, 0)
    p = Coord(0, 0)
    q = Coord(0, 1)
    r = Coord(0, 2)
    s = Coord(1, 2)
    analysis = AnalyzedBoard(
        grid={a: 2, b: 2},
        frontier=[a, b],
        unknown_coords=frozenset({p, q, r, s}),
        flagged_coords=frozenset(),
    )

    assert ConstraintSubtractor().find_moves(analysis) == [
        (ActionType.REVEAL, r),
        (ActionType.REVEAL, s),
    ]


def test_subset_deduction_flags_mine() -> None:
    a = Coord(1, 1)
    b = Coord(1, 0)
    p = Coord(0, 0)
    q = Coord(0, 2)
    r = Coord(1, 2)
    analysis = AnalyzedBoard(
        grid={a: 3, b: 1},
        frontier=[a, b],
        unknown_coords=frozenset({p, q, r}),
        flagged_coords=frozenset(),
    )

    assert ConstraintSubtractor().find_moves(analysis) == [
        (ActionType.FLAG, q),
        (ActionType.FLAG, r),
    ]


def test_no_subset_relationship_returns_none() -> None:
    a = Coord(1, 1)
    b = Coord(3, 1)
    p = Coord(0, 0)
    q = Coord(4, 0)
    analysis = AnalyzedBoard(
        grid={a: 1, b: 1},
        frontier=[a, b],
        unknown_coords=frozenset({p, q}),
        flagged_coords=frozenset(),
    )

    assert ConstraintSubtractor().find_moves(analysis) == []


def test_handles_flagged_neighbors() -> None:
    a = Coord(1, 1)
    b = Coord(1, -1)
    p = Coord(0, 0)
    q = Coord(0, 1)
    flagged = Coord(2, 2)
    analysis = AnalyzedBoard(
        grid={a: 2, b: 1},
        frontier=[a, b],
        unknown_coords=frozenset({p, q}),
        flagged_coords=frozenset({flagged}),
    )

    assert ConstraintSubtractor().find_moves(analysis) == [
        (ActionType.REVEAL, q),
    ]
