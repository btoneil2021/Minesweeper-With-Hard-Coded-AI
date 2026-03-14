from collections.abc import Sequence

import pytest

from minesweeper.domain.move import Move
from minesweeper.domain.types import ActionType, Coord, GameConfig, GamePhase, TileState
from minesweeper.engine.game import Game


class FixedSampleRandom:
    def __init__(self, mine_coords: Sequence[Coord]) -> None:
        self._mine_coords = list(mine_coords)

    def sample(self, population: object, k: int) -> list[Coord]:
        assert k == len(self._mine_coords)
        return list(self._mine_coords)


def test_starts_not_started() -> None:
    game = Game(GameConfig(width=4, height=4, num_mines=2))

    assert game.phase == GamePhase.NOT_STARTED


def test_first_move_transitions_to_in_progress() -> None:
    game = Game(
        GameConfig(width=4, height=4, num_mines=1),
        FixedSampleRandom([Coord(3, 3)]),
    )

    game.apply_move(Move(ActionType.REVEAL, Coord(2, 2)))

    assert game.phase == GamePhase.IN_PROGRESS


def test_reveal_numbered_tile() -> None:
    game = Game(
        GameConfig(width=3, height=3, num_mines=1),
        FixedSampleRandom([Coord(1, 1)]),
    )

    changed = game.apply_move(Move(ActionType.REVEAL, Coord(0, 0)))

    assert changed == [Coord(0, 0)]
    assert game.board.tile_at(Coord(0, 0)).state == TileState.REVEALED


def test_reveal_oob_raises() -> None:
    game = Game(GameConfig(width=3, height=3, num_mines=1))

    with pytest.raises(ValueError):
        game.apply_move(Move(ActionType.REVEAL, Coord(-1, 0)))


def test_reveal_already_revealed_raises() -> None:
    game = Game(
        GameConfig(width=3, height=3, num_mines=1),
        FixedSampleRandom([Coord(2, 2)]),
    )

    game.apply_move(Move(ActionType.REVEAL, Coord(0, 0)))

    with pytest.raises(ValueError):
        game.apply_move(Move(ActionType.REVEAL, Coord(0, 0)))


def test_flag_hidden_tile() -> None:
    game = Game(GameConfig(width=3, height=3, num_mines=1))

    changed = game.apply_move(Move(ActionType.FLAG, Coord(0, 0)))

    assert changed == [Coord(0, 0)]
    assert game.board.tile_at(Coord(0, 0)).state == TileState.FLAGGED


def test_unflag_flagged_tile() -> None:
    game = Game(GameConfig(width=3, height=3, num_mines=1))
    game.apply_move(Move(ActionType.FLAG, Coord(0, 0)))

    changed = game.apply_move(Move(ActionType.UNFLAG, Coord(0, 0)))

    assert changed == [Coord(0, 0)]
    assert game.board.tile_at(Coord(0, 0)).state == TileState.HIDDEN


def test_flag_already_flagged_raises() -> None:
    game = Game(GameConfig(width=3, height=3, num_mines=1))
    game.apply_move(Move(ActionType.FLAG, Coord(0, 0)))

    with pytest.raises(ValueError):
        game.apply_move(Move(ActionType.FLAG, Coord(0, 0)))


def test_unflag_non_flagged_raises() -> None:
    game = Game(GameConfig(width=3, height=3, num_mines=1))

    with pytest.raises(ValueError):
        game.apply_move(Move(ActionType.UNFLAG, Coord(0, 0)))


def test_flag_revealed_tile_raises() -> None:
    game = Game(
        GameConfig(width=3, height=3, num_mines=1),
        FixedSampleRandom([Coord(2, 2)]),
    )
    game.apply_move(Move(ActionType.REVEAL, Coord(0, 0)))

    with pytest.raises(ValueError):
        game.apply_move(Move(ActionType.FLAG, Coord(0, 0)))


def test_reveal_flagged_tile_raises() -> None:
    game = Game(GameConfig(width=3, height=3, num_mines=1))
    game.apply_move(Move(ActionType.FLAG, Coord(0, 0)))

    with pytest.raises(ValueError):
        game.apply_move(Move(ActionType.REVEAL, Coord(0, 0)))


def test_reveal_mine_transitions_to_lost() -> None:
    game = Game(
        GameConfig(width=3, height=3, num_mines=1),
        FixedSampleRandom([Coord(2, 2)]),
    )
    game.apply_move(Move(ActionType.REVEAL, Coord(1, 1)))

    game.apply_move(Move(ActionType.REVEAL, Coord(2, 2)))

    assert game.phase == GamePhase.LOST


def test_move_after_lost_raises() -> None:
    game = Game(
        GameConfig(width=3, height=3, num_mines=1),
        FixedSampleRandom([Coord(2, 2)]),
    )
    game.apply_move(Move(ActionType.REVEAL, Coord(1, 1)))
    game.apply_move(Move(ActionType.REVEAL, Coord(2, 2)))

    with pytest.raises(ValueError):
        game.apply_move(Move(ActionType.FLAG, Coord(1, 1)))


def test_reveal_all_safe_transitions_to_won() -> None:
    game = Game(
        GameConfig(width=2, height=2, num_mines=1),
        FixedSampleRandom([Coord(1, 1)]),
    )

    game.apply_move(Move(ActionType.REVEAL, Coord(0, 0)))
    game.apply_move(Move(ActionType.REVEAL, Coord(0, 1)))
    game.apply_move(Move(ActionType.REVEAL, Coord(1, 0)))

    assert game.phase == GamePhase.WON


def test_move_after_won_raises() -> None:
    game = Game(
        GameConfig(width=2, height=2, num_mines=1),
        FixedSampleRandom([Coord(1, 1)]),
    )
    game.apply_move(Move(ActionType.REVEAL, Coord(0, 0)))
    game.apply_move(Move(ActionType.REVEAL, Coord(0, 1)))
    game.apply_move(Move(ActionType.REVEAL, Coord(1, 0)))

    with pytest.raises(ValueError):
        game.apply_move(Move(ActionType.FLAG, Coord(1, 1)))


def test_first_reveal_on_mine_relocates() -> None:
    game = Game(
        GameConfig(width=3, height=3, num_mines=1),
        FixedSampleRandom([Coord(0, 0)]),
    )

    changed = game.apply_move(Move(ActionType.REVEAL, Coord(0, 0)))

    assert Coord(0, 0) in changed
    assert game.board.tile_at(Coord(0, 0)).is_mine is False

    mine_count = sum(
        game.board.tile_at(Coord(x, y)).is_mine
        for x in range(game.board.width)
        for y in range(game.board.height)
    )
    assert mine_count == 1


def test_first_reveal_on_safe_tile_no_change() -> None:
    game = Game(
        GameConfig(width=3, height=3, num_mines=1),
        FixedSampleRandom([Coord(2, 2)]),
    )

    game.apply_move(Move(ActionType.REVEAL, Coord(0, 0)))

    assert game.board.tile_at(Coord(2, 2)).is_mine is True


def test_reveal_zero_flood_fill() -> None:
    game = Game(
        GameConfig(width=4, height=4, num_mines=1),
        FixedSampleRandom([Coord(3, 3)]),
    )

    changed = game.apply_move(Move(ActionType.REVEAL, Coord(0, 0)))

    expected = {
        Coord(x, y)
        for x in range(4)
        for y in range(4)
        if Coord(x, y) != Coord(3, 3)
    }
    assert set(changed) == expected
    assert all(game.board.tile_at(coord).state == TileState.REVEALED for coord in expected)
    assert game.board.tile_at(Coord(3, 3)).state == TileState.HIDDEN


def test_reset_produces_fresh_board() -> None:
    game = Game(
        GameConfig(width=3, height=3, num_mines=1),
        FixedSampleRandom([Coord(2, 2)]),
    )
    game.apply_move(Move(ActionType.REVEAL, Coord(1, 1)))
    game.apply_move(Move(ActionType.REVEAL, Coord(2, 2)))

    game.reset(GameConfig(width=2, height=2, num_mines=1))

    assert game.phase == GamePhase.NOT_STARTED
    assert game.board.width == 2
    assert game.board.height == 2
    assert all(
        game.board.tile_at(Coord(x, y)).state == TileState.HIDDEN
        for x in range(2)
        for y in range(2)
    )
