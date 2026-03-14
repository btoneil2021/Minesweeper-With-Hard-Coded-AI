from minesweeper.domain.move import Move
from minesweeper.domain.types import ActionType, Coord
from minesweeper.external.capture import ScreenRegion, TileSize
from minesweeper.external.executor import ScreenMoveExecutor


def test_execute_targets_tile_center_for_reveal() -> None:
    clicks: list[tuple[str, int, int]] = []
    delays: list[float] = []
    executor = ScreenMoveExecutor(
        board_region=ScreenRegion(10, 20, 30, 30),
        tile_size=TileSize(10, 10),
        left_click=lambda x, y: clicks.append(("left", x, y)),
        right_click=lambda x, y: clicks.append(("right", x, y)),
        delay=lambda seconds: delays.append(seconds),
    )

    executor.execute(Move(ActionType.REVEAL, Coord(1, 2)))

    assert clicks == [("left", 25, 45)]
    assert delays == []


def test_execute_batch_orders_flags_before_reveals() -> None:
    clicks: list[tuple[str, int, int]] = []
    delays: list[float] = []
    executor = ScreenMoveExecutor(
        board_region=ScreenRegion(0, 0, 20, 20),
        tile_size=TileSize(10, 10),
        click_delay_ms=40,
        left_click=lambda x, y: clicks.append(("left", x, y)),
        right_click=lambda x, y: clicks.append(("right", x, y)),
        delay=lambda seconds: delays.append(seconds),
    )

    executor.execute_batch(
        [
            Move(ActionType.REVEAL, Coord(1, 1)),
            Move(ActionType.FLAG, Coord(0, 0)),
            Move(ActionType.UNFLAG, Coord(1, 0)),
        ]
    )

    assert clicks == [
        ("right", 5, 5),
        ("right", 15, 5),
        ("left", 15, 15),
    ]
    assert delays == [0.04, 0.04]


def test_execute_skips_positions_outside_board_region() -> None:
    clicks: list[tuple[str, int, int]] = []
    executor = ScreenMoveExecutor(
        board_region=ScreenRegion(0, 0, 10, 10),
        tile_size=TileSize(10, 10),
        left_click=lambda x, y: clicks.append(("left", x, y)),
        right_click=lambda x, y: clicks.append(("right", x, y)),
    )

    executor.execute(Move(ActionType.REVEAL, Coord(2, 2)))

    assert clicks == []
