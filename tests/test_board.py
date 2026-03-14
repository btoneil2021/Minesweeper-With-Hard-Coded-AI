import itertools
import random

import pytest

from minesweeper.domain.types import Coord, GameConfig, TileState
from minesweeper.engine.board_impl import Board


class FixedSampleRandom:
    def __init__(self, mine_coords: list[Coord]) -> None:
        self._mine_coords = mine_coords

    def sample(self, population: object, k: int) -> list[Coord]:
        assert k == len(self._mine_coords)
        return list(self._mine_coords)


def test_dimensions() -> None:
    board = Board(GameConfig(width=10, height=8, num_mines=15))

    assert board.width == 10
    assert board.height == 8


def test_mine_count() -> None:
    board = Board(GameConfig(width=6, height=5, num_mines=7))

    mine_count = sum(
        board.tile_at(Coord(x, y)).is_mine
        for x, y in itertools.product(range(board.width), range(board.height))
    )

    assert mine_count == 7


def test_deterministic_with_seed() -> None:
    config = GameConfig(width=6, height=5, num_mines=7)
    left = Board(config, random.Random(1234))
    right = Board(config, random.Random(1234))

    left_snapshot = [
        left.tile_at(Coord(x, y))
        for x, y in itertools.product(range(config.width), range(config.height))
    ]
    right_snapshot = [
        right.tile_at(Coord(x, y))
        for x, y in itertools.product(range(config.width), range(config.height))
    ]

    assert left_snapshot == right_snapshot


def test_adjacent_mines_non_mine_only() -> None:
    board = Board(
        GameConfig(width=3, height=3, num_mines=1),
        FixedSampleRandom([Coord(1, 1)]),
    )

    assert board.tile_at(Coord(1, 1)).is_mine is True
    assert board.tile_at(Coord(0, 0)).adjacent_mines == 1
    assert board.tile_at(Coord(0, 1)).adjacent_mines == 1
    assert board.tile_at(Coord(0, 2)).adjacent_mines == 1
    assert board.tile_at(Coord(1, 0)).adjacent_mines == 1
    assert board.tile_at(Coord(1, 2)).adjacent_mines == 1
    assert board.tile_at(Coord(2, 0)).adjacent_mines == 1
    assert board.tile_at(Coord(2, 1)).adjacent_mines == 1
    assert board.tile_at(Coord(2, 2)).adjacent_mines == 1


def test_all_tiles_exist() -> None:
    board = Board(GameConfig(width=4, height=3, num_mines=2))

    tiles = [
        board.tile_at(Coord(x, y))
        for x, y in itertools.product(range(board.width), range(board.height))
    ]

    assert len(tiles) == 12


def test_oob_raises() -> None:
    board = Board(GameConfig(width=4, height=3, num_mines=2))

    with pytest.raises(KeyError):
        board.tile_at(Coord(-1, 0))

    with pytest.raises(KeyError):
        board.tile_at(Coord(board.width, 0))

    with pytest.raises(KeyError):
        board.tile_at(Coord(0, board.height))


def test_initial_state_all_hidden() -> None:
    board = Board(GameConfig(width=4, height=3, num_mines=2))

    assert all(
        board.tile_at(Coord(x, y)).state == TileState.HIDDEN
        for x, y in itertools.product(range(board.width), range(board.height))
    )


def test_adjacent_mines_corners() -> None:
    board = Board(
        GameConfig(width=3, height=3, num_mines=2),
        FixedSampleRandom([Coord(1, 0), Coord(0, 1)]),
    )

    assert board.tile_at(Coord(0, 0)).adjacent_mines == 2
    assert board.tile_at(Coord(2, 0)).adjacent_mines == 1
    assert board.tile_at(Coord(0, 2)).adjacent_mines == 1
    assert board.tile_at(Coord(2, 2)).adjacent_mines == 0


def test_adjacent_mines_range() -> None:
    board = Board(GameConfig(width=6, height=5, num_mines=7), random.Random(1234))

    for x, y in itertools.product(range(board.width), range(board.height)):
        tile = board.tile_at(Coord(x, y))
        if not tile.is_mine:
            assert 0 <= tile.adjacent_mines <= 8
