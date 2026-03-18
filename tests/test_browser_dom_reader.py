import pytest

from minesweeper.external.browser.dom_reader import DomBoardReader
from minesweeper.external.browser.protocol import BoardSnapshotPayload, TilePayload
from minesweeper.domain.types import Coord, TileState


def make_snapshot() -> BoardSnapshotPayload:
    return BoardSnapshotPayload(
        width=3,
        height=2,
        face_state="smile",
        tiles=(
            TilePayload(x=0, y=0, state="hidden"),
            TilePayload(x=1, y=0, state="revealed", adjacent_mines=1),
            TilePayload(x=2, y=0, state="flagged"),
            TilePayload(x=0, y=1, state="exploded"),
            TilePayload(x=1, y=1, state="mine_revealed"),
            TilePayload(x=2, y=1, state="revealed"),
        ),
    )


def test_reader_exposes_board_dimensions_and_mines() -> None:
    reader = DomBoardReader(make_snapshot(), num_mines=7)

    assert reader.width == 3
    assert reader.height == 2
    assert reader.num_mines == 7


def test_reader_maps_dom_states_to_domain_tiles() -> None:
    reader = DomBoardReader(make_snapshot(), num_mines=7)

    hidden = reader.tile_at(Coord(0, 0))
    revealed = reader.tile_at(Coord(1, 0))
    flagged = reader.tile_at(Coord(2, 0))
    exploded = reader.tile_at(Coord(0, 1))
    mine_revealed = reader.tile_at(Coord(1, 1))
    revealed_zero = reader.tile_at(Coord(2, 1))

    assert hidden.state == TileState.HIDDEN
    assert hidden.is_mine is False

    assert revealed.state == TileState.REVEALED
    assert revealed.adjacent_mines == 1
    assert revealed.is_mine is False

    assert flagged.state == TileState.FLAGGED
    assert flagged.is_mine is False

    assert exploded.state == TileState.EXPLODED
    assert exploded.is_mine is True

    assert mine_revealed.state == TileState.REVEALED
    assert mine_revealed.is_mine is True

    assert revealed_zero.state == TileState.REVEALED
    assert revealed_zero.adjacent_mines == 0
    assert revealed_zero.is_mine is False


def test_reader_rejects_out_of_bounds_coords() -> None:
    reader = DomBoardReader(make_snapshot(), num_mines=7)

    with pytest.raises(KeyError):
        reader.tile_at(Coord(-1, 0))

    with pytest.raises(KeyError):
        reader.tile_at(Coord(3, 0))

    with pytest.raises(KeyError):
        reader.tile_at(Coord(0, 2))


def test_reader_can_update_snapshot() -> None:
    reader = DomBoardReader(make_snapshot(), num_mines=7)
    updated = BoardSnapshotPayload(
        width=3,
        height=2,
        face_state="smile",
        tiles=(
            TilePayload(x=0, y=0, state="revealed", adjacent_mines=2),
            TilePayload(x=1, y=0, state="flagged"),
            TilePayload(x=2, y=0, state="hidden"),
            TilePayload(x=0, y=1, state="revealed", adjacent_mines=3),
            TilePayload(x=1, y=1, state="mine_revealed"),
            TilePayload(x=2, y=1, state="exploded"),
        ),
    )

    reader.update_snapshot(updated)

    assert reader.tile_at(Coord(0, 0)).adjacent_mines == 2
    assert reader.tile_at(Coord(1, 0)).state == TileState.FLAGGED
    assert reader.tile_at(Coord(2, 1)).state == TileState.EXPLODED


def test_reader_rejects_incomplete_snapshot_coverage() -> None:
    snapshot = BoardSnapshotPayload(
        width=3,
        height=2,
        face_state="smile",
        tiles=(
            TilePayload(x=0, y=0, state="hidden"),
            TilePayload(x=1, y=0, state="revealed", adjacent_mines=1),
            TilePayload(x=2, y=0, state="flagged"),
            TilePayload(x=0, y=1, state="exploded"),
            TilePayload(x=1, y=1, state="mine_revealed"),
        ),
    )

    with pytest.raises(ValueError, match="cover the full declared board"):
        DomBoardReader(snapshot, num_mines=7)
