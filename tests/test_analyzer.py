from minesweeper.ai.analyzer import Analyzer, AnalyzedBoard
from minesweeper.domain.move import Move
from minesweeper.domain.types import ActionType, Coord, GameConfig
from minesweeper.engine.board_impl import Board
from minesweeper.engine.game import Game


class FixedSampleRandom:
    def __init__(self, mine_coords: list[Coord]) -> None:
        self._mine_coords = list(mine_coords)

    def sample(self, population: object, k: int) -> list[Coord]:
        assert k == len(self._mine_coords)
        return list(self._mine_coords)


def test_fresh_board_all_unknown() -> None:
    board = Board(GameConfig(width=3, height=3, num_mines=1))

    analysis = Analyzer().analyze(board)

    assert set(analysis.grid.values()) == {AnalyzedBoard.UNKNOWN}
    assert analysis.frontier == []
    assert analysis.unknown_coords == frozenset(
        Coord(x, y) for x in range(board.width) for y in range(board.height)
    )


def test_revealed_tile_shows_value() -> None:
    game = Game(
        GameConfig(width=3, height=3, num_mines=1),
        FixedSampleRandom([Coord(2, 2)]),
    )
    game.apply_move(Move(ActionType.REVEAL, Coord(1, 1)))

    analysis = Analyzer().analyze(game.board)

    assert analysis.grid[Coord(1, 1)] == 1


def test_flagged_tile_shows_flagged() -> None:
    game = Game(GameConfig(width=3, height=3, num_mines=1))
    game.apply_move(Move(ActionType.FLAG, Coord(0, 0)))

    analysis = Analyzer().analyze(game.board)

    assert analysis.grid[Coord(0, 0)] == AnalyzedBoard.FLAGGED


def test_frontier_includes_numbered_with_unknown_neighbor() -> None:
    game = Game(
        GameConfig(width=3, height=3, num_mines=1),
        FixedSampleRandom([Coord(2, 2)]),
    )
    game.apply_move(Move(ActionType.REVEAL, Coord(1, 1)))

    analysis = Analyzer().analyze(game.board)

    assert Coord(1, 1) in analysis.frontier


def test_frontier_excludes_fully_revealed_neighborhood() -> None:
    game = Game(
        GameConfig(width=2, height=2, num_mines=1),
        FixedSampleRandom([Coord(1, 1)]),
    )
    game.apply_move(Move(ActionType.FLAG, Coord(1, 1)))
    game.apply_move(Move(ActionType.REVEAL, Coord(0, 0)))
    game.apply_move(Move(ActionType.REVEAL, Coord(0, 1)))
    game.apply_move(Move(ActionType.REVEAL, Coord(1, 0)))

    analysis = Analyzer().analyze(game.board)

    assert Coord(0, 0) not in analysis.frontier


def test_frontier_excludes_zeros() -> None:
    game = Game(
        GameConfig(width=3, height=3, num_mines=1),
        FixedSampleRandom([Coord(2, 2)]),
    )
    game.apply_move(Move(ActionType.REVEAL, Coord(0, 0)))

    analysis = Analyzer().analyze(game.board)

    assert Coord(0, 0) not in analysis.frontier


def test_unknown_coords_excludes_revealed_and_flagged() -> None:
    game = Game(
        GameConfig(width=3, height=3, num_mines=1),
        FixedSampleRandom([Coord(2, 2)]),
    )
    game.apply_move(Move(ActionType.REVEAL, Coord(1, 1)))
    game.apply_move(Move(ActionType.FLAG, Coord(0, 0)))

    analysis = Analyzer().analyze(game.board)

    assert Coord(1, 1) not in analysis.unknown_coords
    assert Coord(0, 0) not in analysis.unknown_coords


def test_total_mines_matches_board() -> None:
    board = Board(GameConfig(width=4, height=5, num_mines=6))

    analysis = Analyzer().analyze(board)

    assert analysis.total_mines == 6
