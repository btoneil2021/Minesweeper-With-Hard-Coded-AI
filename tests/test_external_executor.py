import pytest

from minesweeper.domain.move import Move
from minesweeper.domain.types import ActionType, Coord
from minesweeper.external.errors import ExecutionError
from minesweeper.external.capture import ScreenRegion, TileSize
from minesweeper.external.executor import ScreenMoveExecutor
from minesweeper.external.grid import TileGrid


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


def test_execute_batch_preserves_solver_order() -> None:
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
            Move(ActionType.REVEAL, Coord(1, 0)),
        ]
    )

    assert clicks == [
        ("left", 15, 15),
        ("right", 5, 5),
        ("left", 15, 5),
    ]
    assert delays == [0.04, 0.04]


def test_execute_uses_empirical_grid_click_target_with_inset() -> None:
    clicks: list[tuple[str, int, int]] = []
    executor = ScreenMoveExecutor(
        board_region=ScreenRegion(100, 200, 94, 61),
        tile_size=TileSize(31, 30),
        grid=TileGrid(
            origin_left=100,
            origin_top=200,
            col_boundaries=(0, 31, 63, 94),
            row_boundaries=(0, 30, 61),
        ),
        click_inset=4,
        left_click=lambda x, y: clicks.append(("left", x, y)),
        right_click=lambda x, y: clicks.append(("right", x, y)),
    )

    executor.execute(Move(ActionType.REVEAL, Coord(2, 1)))

    assert clicks == [("left", 178, 245)]


def test_execute_calls_before_click_hook_with_move_and_screen_point() -> None:
    callbacks: list[tuple[ActionType, Coord, int, int, int, int]] = []
    clicks: list[tuple[str, int, int]] = []
    executor = ScreenMoveExecutor(
        board_region=ScreenRegion(100, 200, 94, 61),
        tile_size=TileSize(31, 30),
        grid=TileGrid(
            origin_left=100,
            origin_top=200,
            col_boundaries=(0, 31, 63, 94),
            row_boundaries=(0, 30, 61),
        ),
        click_inset=4,
        before_click=lambda move, x, y, move_index, batch_size: callbacks.append(
            (move.action, move.coord, x, y, move_index, batch_size)
        ),
        left_click=lambda x, y: clicks.append(("left", x, y)),
        right_click=lambda x, y: clicks.append(("right", x, y)),
    )

    executor.execute(Move(ActionType.REVEAL, Coord(2, 1)))

    assert callbacks == [(ActionType.REVEAL, Coord(2, 1), 178, 245, 0, 1)]
    assert clicks == [("left", 178, 245)]


def test_execute_batch_reports_move_index_within_batch() -> None:
    callbacks: list[tuple[Coord, int, int]] = []
    executor = ScreenMoveExecutor(
        board_region=ScreenRegion(0, 0, 20, 20),
        tile_size=TileSize(10, 10),
        before_click=lambda move, _x, _y, move_index, batch_size: callbacks.append(
            (move.coord, move_index, batch_size)
        ),
        delay=lambda _seconds: None,
        left_click=lambda _x, _y: None,
        right_click=lambda _x, _y: None,
    )

    executor.execute_batch(
        [
            Move(ActionType.REVEAL, Coord(0, 0)),
            Move(ActionType.FLAG, Coord(1, 0)),
        ]
    )

    assert callbacks == [
        (Coord(0, 0), 0, 2),
        (Coord(1, 0), 1, 2),
    ]


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


def test_execute_raises_execution_error_for_unsupported_action() -> None:
    executor = ScreenMoveExecutor(
        board_region=ScreenRegion(0, 0, 10, 10),
        tile_size=TileSize(10, 10),
        left_click=lambda _x, _y: None,
        right_click=lambda _x, _y: None,
    )

    with pytest.raises(ExecutionError, match="unsupported move type"):
        executor.execute(Move(ActionType.UNFLAG, Coord(0, 0)))
