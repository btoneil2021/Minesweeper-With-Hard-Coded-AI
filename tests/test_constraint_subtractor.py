from minesweeper.ai.analyzer import AnalyzedBoard
from minesweeper.ai.strategies.constraint_subtractor import ConstraintSubtractor
from minesweeper.domain.types import ActionType, Coord


def test_subset_deduction_reveals_safe() -> None:
    a = Coord(1, 1)
    b = Coord(1, 0)
    p = Coord(0, 0)
    q = Coord(0, 1)
    r = Coord(0, 2)
    analysis = AnalyzedBoard(
        grid={a: 2, b: 2},
        frontier=[a, b],
        unknown_coords=frozenset({p, q, r}),
        flagged_coords=frozenset(),
    )

    move = ConstraintSubtractor().find_move(analysis)

    assert move is not None
    assert move.action == ActionType.REVEAL
    assert move.coord == r


def test_subset_deduction_flags_mine() -> None:
    a = Coord(1, 1)
    b = Coord(1, -1)
    p = Coord(0, 0)
    q = Coord(0, 1)
    analysis = AnalyzedBoard(
        grid={a: 2, b: 1},
        frontier=[a, b],
        unknown_coords=frozenset({p, q}),
        flagged_coords=frozenset(),
    )

    move = ConstraintSubtractor().find_move(analysis)

    assert move is not None
    assert move.action == ActionType.FLAG
    assert move.coord == q


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

    assert ConstraintSubtractor().find_move(analysis) is None


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

    move = ConstraintSubtractor().find_move(analysis)

    assert move is not None
    assert move.action == ActionType.REVEAL
    assert move.coord == q
