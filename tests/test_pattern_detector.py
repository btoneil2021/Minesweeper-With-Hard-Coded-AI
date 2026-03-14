from minesweeper.ai.analyzer import AnalyzedBoard
from minesweeper.ai.strategies.pattern_detector import PatternDetector
from minesweeper.domain.types import ActionType, Coord


def test_all_bombs_flagged_reveals_safe() -> None:
    anchor = Coord(1, 1)
    safe_options = {Coord(1, 0), Coord(0, 1)}
    analysis = AnalyzedBoard(
        grid={
            anchor: 1,
            Coord(0, 0): AnalyzedBoard.FLAGGED,
            Coord(1, 0): AnalyzedBoard.UNKNOWN,
            Coord(0, 1): AnalyzedBoard.UNKNOWN,
        },
        frontier=[anchor],
        unknown_coords=frozenset(safe_options),
        flagged_coords=frozenset({Coord(0, 0)}),
    )

    move = PatternDetector().find_move(analysis)

    assert move is not None
    assert move.action == ActionType.REVEAL
    assert move.coord in safe_options


def test_all_unknowns_are_bombs_flags() -> None:
    anchor = Coord(1, 1)
    bomb_options = {Coord(1, 0), Coord(0, 1)}
    analysis = AnalyzedBoard(
        grid={anchor: 2},
        frontier=[anchor],
        unknown_coords=frozenset(bomb_options),
        flagged_coords=frozenset(),
    )

    move = PatternDetector().find_move(analysis)

    assert move is not None
    assert move.action == ActionType.FLAG
    assert move.coord in bomb_options


def test_no_pattern_returns_none() -> None:
    anchor = Coord(1, 1)
    analysis = AnalyzedBoard(
        grid={anchor: 3},
        frontier=[anchor],
        unknown_coords=frozenset({Coord(1, 0), Coord(0, 1), Coord(2, 1)}),
        flagged_coords=frozenset({Coord(0, 0)}),
    )

    assert PatternDetector().find_move(analysis) is None


def test_skips_non_frontier_tiles() -> None:
    anchor = Coord(1, 1)
    analysis = AnalyzedBoard(
        grid={anchor: 1},
        frontier=[],
        unknown_coords=frozenset({Coord(1, 0)}),
        flagged_coords=frozenset(),
    )

    assert PatternDetector().find_move(analysis) is None
