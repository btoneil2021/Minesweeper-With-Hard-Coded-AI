import pytest

from minesweeper.external.browser.minesweeperonline import (
    MinesweeperOnlineParseError,
    parse_face_state,
    parse_tile_payload,
)
from minesweeper.external.browser.protocol import TilePayload


@pytest.mark.parametrize(
    ("tile_id", "class_name", "expected"),
    [
        ("7_4", "square open1", TilePayload(x=4, y=7, state="revealed", adjacent_mines=1)),
        ("7_4", "square open2", TilePayload(x=4, y=7, state="revealed", adjacent_mines=2)),
        ("7_4", "square open3", TilePayload(x=4, y=7, state="revealed", adjacent_mines=3)),
        ("7_4", "square open4", TilePayload(x=4, y=7, state="revealed", adjacent_mines=4)),
        ("7_4", "square open5", TilePayload(x=4, y=7, state="revealed", adjacent_mines=5)),
        ("7_4", "square open6", TilePayload(x=4, y=7, state="revealed", adjacent_mines=6)),
        ("7_4", "square open7", TilePayload(x=4, y=7, state="revealed", adjacent_mines=7)),
        ("7_4", "square open8", TilePayload(x=4, y=7, state="revealed", adjacent_mines=8)),
        ("7_4", "square", TilePayload(x=4, y=7, state="hidden")),
        ("7_4", "square blank", TilePayload(x=4, y=7, state="hidden")),
        ("7_4", "square bombflagged", TilePayload(x=4, y=7, state="flagged")),
        ("7_4", "square bombdeath", TilePayload(x=4, y=7, state="exploded")),
        ("7_4", "square bombrevealed", TilePayload(x=4, y=7, state="mine_revealed")),
    ],
)
def test_parse_tile_payload_maps_known_minesweeperonline_classes(
    tile_id: str,
    class_name: str,
    expected: TilePayload,
) -> None:
    assert parse_tile_payload(tile_id, class_name) == expected


@pytest.mark.parametrize(
    ("class_name", "expected"),
    [
        ("face", "in_progress"),
        ("face facesmile", "in_progress"),
        ("face facewin", "won"),
        ("face facedead", "lost"),
    ],
)
def test_parse_face_state_maps_known_variants(class_name: str, expected: str) -> None:
    assert parse_face_state(class_name) == expected


@pytest.mark.parametrize(
    ("tile_id", "class_name", "message"),
    [
        ("a_b", "square open1", "tile id"),
        ("7_4", "square open9", "unsupported tile class"),
        ("7_4", "square mystery", "unsupported tile class"),
        ("7_4", "square open1 mystery", "unsupported tile class"),
    ],
)
def test_parse_tile_payload_rejects_unknown_combinations(
    tile_id: str,
    class_name: str,
    message: str,
) -> None:
    with pytest.raises(MinesweeperOnlineParseError, match=message):
        parse_tile_payload(tile_id, class_name)


@pytest.mark.parametrize(
    ("class_name", "message"),
    [
        ("face confused", "unsupported face class"),
        ("button facewin", "unsupported face class"),
    ],
)
def test_parse_face_state_rejects_unknown_combinations(class_name: str, message: str) -> None:
    with pytest.raises(MinesweeperOnlineParseError, match=message):
        parse_face_state(class_name)
