import itertools

from minesweeper.ai.analyzer import AnalyzedBoard
from minesweeper.ai.strategies import probability_solver as probability_solver_module
from minesweeper.ai.strategies.probability_solver import ProbabilitySolver
from minesweeper.domain.types import ActionType, Coord


def test_certain_mine_flags() -> None:
    frontier = Coord(1, 1)
    target = Coord(0, 0)
    analysis = AnalyzedBoard(
        grid={frontier: 1},
        frontier=[frontier],
        unknown_coords=frozenset({target}),
        flagged_coords=frozenset(),
        total_mines=1,
    )

    assert ProbabilitySolver().find_moves(analysis) == [
        (ActionType.FLAG, target),
    ]


def test_certain_safe_reveals() -> None:
    frontier = Coord(1, 1)
    flagged = Coord(0, 1)
    target = Coord(0, 0)
    analysis = AnalyzedBoard(
        grid={frontier: 1},
        frontier=[frontier],
        unknown_coords=frozenset({target}),
        flagged_coords=frozenset({flagged}),
        total_mines=1,
    )

    assert ProbabilitySolver().find_moves(analysis) == [
        (ActionType.REVEAL, target),
    ]


def test_returns_all_certain_safe_moves() -> None:
    frontier = Coord(1, 1)
    flagged = Coord(0, 1)
    safe_tiles = [Coord(0, 0), Coord(1, 0)]
    analysis = AnalyzedBoard(
        grid={frontier: 1},
        frontier=[frontier],
        unknown_coords=frozenset(safe_tiles),
        flagged_coords=frozenset({flagged}),
        total_mines=1,
    )

    assert ProbabilitySolver().find_moves(analysis) == [
        (ActionType.REVEAL, Coord(0, 0)),
        (ActionType.REVEAL, Coord(1, 0)),
    ]


def test_returns_all_certain_mines() -> None:
    frontier = Coord(1, 1)
    mine_tiles = [Coord(0, 0), Coord(1, 0)]
    analysis = AnalyzedBoard(
        grid={frontier: 2},
        frontier=[frontier],
        unknown_coords=frozenset(mine_tiles),
        flagged_coords=frozenset(),
        total_mines=2,
    )

    assert ProbabilitySolver().find_moves(analysis) == [
        (ActionType.FLAG, Coord(0, 0)),
        (ActionType.FLAG, Coord(1, 0)),
    ]


def test_chooses_lowest_probability() -> None:
    frontier = Coord(1, 1)
    p = Coord(0, 0)
    q = Coord(0, 1)
    r = Coord(3, 3)
    analysis = AnalyzedBoard(
        grid={frontier: 1},
        frontier=[frontier],
        unknown_coords=frozenset({p, q, r}),
        flagged_coords=frozenset(),
        total_mines=1,
    )

    assert ProbabilitySolver().find_moves(analysis) == [
        (ActionType.REVEAL, r),
    ]


def test_high_probability_flags() -> None:
    frontier = Coord(1, 1)
    target = Coord(0, 0)
    analysis = AnalyzedBoard(
        grid={frontier: 1},
        frontier=[frontier],
        unknown_coords=frozenset({target}),
        flagged_coords=frozenset(),
        total_mines=1,
    )

    assert ProbabilitySolver().find_moves(analysis) == [
        (ActionType.FLAG, target),
    ]


def test_falls_back_to_global_probability() -> None:
    analysis = AnalyzedBoard(
        unknown_coords=frozenset({Coord(0, 0), Coord(0, 1), Coord(1, 0), Coord(1, 1)}),
        total_mines=2,
    )

    moves = ProbabilitySolver().find_moves(analysis)

    assert len(moves) == 1
    assert moves[0][0] == ActionType.REVEAL
    assert moves[0][1] in analysis.unknown_coords


def test_unconstrained_tiles_weighted_by_configurations() -> None:
    frontier = Coord(1, 1)
    p = Coord(0, 0)
    q = Coord(0, 1)
    r = Coord(4, 4)
    s = Coord(5, 5)
    analysis = AnalyzedBoard(
        grid={frontier: 1},
        frontier=[frontier],
        unknown_coords=frozenset({p, q, r, s}),
        flagged_coords=frozenset(),
        total_mines=1,
    )

    assert ProbabilitySolver().find_moves(analysis) == [
        (ActionType.REVEAL, r),
        (ActionType.REVEAL, s),
    ]


def test_returns_none_when_no_unknowns() -> None:
    analysis = AnalyzedBoard(unknown_coords=frozenset(), total_mines=0)

    assert ProbabilitySolver().find_moves(analysis) == []


def test_does_not_enumerate_unconstrained_unknowns(monkeypatch) -> None:
    frontier = Coord(1, 1)
    constrained = {Coord(0, 0), Coord(0, 1)}
    unconstrained = {Coord(10 + i, 10 + i) for i in range(30)}
    analysis = AnalyzedBoard(
        grid={frontier: 1},
        frontier=[frontier],
        unknown_coords=frozenset(constrained | unconstrained),
        flagged_coords=frozenset(),
        total_mines=10,
    )

    original_combinations = itertools.combinations

    def guarded_combinations(iterable: object, r: int):
        items = tuple(iterable)
        if len(items) > 2:
            raise AssertionError("solver tried to enumerate unconstrained tiles")
        return original_combinations(items, r)

    monkeypatch.setattr(probability_solver_module, "combinations", guarded_combinations)

    assert ProbabilitySolver().find_moves(analysis) == [
        (ActionType.REVEAL, Coord(10, 10)),
    ]


def test_large_constrained_region_falls_back_without_exact_enumeration(monkeypatch) -> None:
    frontier = [Coord(i * 3, 0) for i in range(21)]
    unknowns = frozenset(Coord(i * 3, 1) for i in range(21))
    analysis = AnalyzedBoard(
        grid={coord: 1 for coord in frontier},
        frontier=frontier,
        unknown_coords=unknowns,
        flagged_coords=frozenset(),
        total_mines=21,
    )

    def guarded_combinations(iterable: object, r: int):
        items = tuple(iterable)
        if len(items) > 20:
            raise AssertionError("solver tried to exact-enumerate a large constrained region")
        return itertools.combinations(items, r)

    monkeypatch.setattr(probability_solver_module, "combinations", guarded_combinations)

    assert ProbabilitySolver().find_moves(analysis) == [
        (ActionType.FLAG, Coord(0, 1)),
    ]
