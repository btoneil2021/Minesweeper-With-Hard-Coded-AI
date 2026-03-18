from pathlib import Path

import pytest

from minesweeper.domain.move import Move
from minesweeper.domain.types import ActionType
from minesweeper.domain.tile import Tile
from minesweeper.domain.types import Coord, TileState
from minesweeper.external.board_reader import ScreenBoardReader
from minesweeper.external.capture import ScreenRegion, TileSize
from minesweeper.external.errors import BoardReadError
from minesweeper.external.grid import TileGrid


class DummyBoardPixels:
    def __init__(self, width: int, height: int) -> None:
        self.size = (width, height)

    def getpixel(self, position: tuple[int, int]) -> tuple[int, int, int]:
        x, y = position
        return (x, y, 0)


class SavingBoardPixels(DummyBoardPixels):
    def __init__(self, width: int, height: int, saved_paths: list[Path]) -> None:
        super().__init__(width, height)
        self._saved_paths = saved_paths

    def save(self, path: Path) -> None:
        self._saved_paths.append(Path(path))


class FakeCapture:
    def __init__(self, board_pixels: DummyBoardPixels) -> None:
        self._board_pixels = board_pixels
        self.calls: list[ScreenRegion] = []

    def grab(self, region: ScreenRegion) -> DummyBoardPixels:
        self.calls.append(region)
        return self._board_pixels


class RecordingClassifier:
    def __init__(self) -> None:
        self.calls: list[tuple[Coord, tuple[int, int], tuple[int, int, int]]] = []
        self.tiles: dict[Coord, Tile] = {}

    def classify(self, pixels, coord: Coord) -> Tile:
        self.calls.append((coord, pixels.size, pixels.getpixel((0, 0))))
        return self.tiles.get(
            coord,
            Tile(coord=coord, state=TileState.HIDDEN, is_mine=False),
        )


class ExplodingClassifier:
    def classify(self, _pixels, _coord: Coord) -> Tile:
        raise RuntimeError("boom")


def test_refresh_classifies_every_tile_once_per_snapshot() -> None:
    capture = FakeCapture(DummyBoardPixels(8, 8))
    classifier = RecordingClassifier()
    reader = ScreenBoardReader(
        capture=capture,
        classifier=classifier,
        board_region=ScreenRegion(10, 20, 8, 8),
        tile_size=TileSize(4, 4),
        width=2,
        height=2,
        num_mines=3,
    )

    reader.refresh()

    assert capture.calls == [ScreenRegion(10, 20, 8, 8)]
    recorded = {coord: (size, origin) for coord, size, origin in classifier.calls}
    assert recorded == {
        Coord(0, 0): ((4, 4), (0, 0, 0)),
        Coord(0, 1): ((4, 4), (0, 4, 0)),
        Coord(1, 0): ((4, 4), (4, 0, 0)),
        Coord(1, 1): ((4, 4), (4, 4, 0)),
    }


def test_refresh_uses_per_tile_rects_from_empirical_grid() -> None:
    capture = FakeCapture(DummyBoardPixels(63, 61))
    classifier = RecordingClassifier()
    reader = ScreenBoardReader(
        capture=capture,
        classifier=classifier,
        board_region=ScreenRegion(10, 20, 63, 61),
        tile_size=TileSize(31, 30),
        width=2,
        height=2,
        num_mines=3,
        grid=TileGrid(
            origin_left=10,
            origin_top=20,
            col_boundaries=(0, 31, 63),
            row_boundaries=(0, 30, 61),
        ),
    )

    reader.refresh()

    recorded = {coord: (size, origin) for coord, size, origin in classifier.calls}
    assert recorded == {
        Coord(0, 0): ((31, 30), (0, 0, 0)),
        Coord(0, 1): ((31, 31), (0, 30, 0)),
        Coord(1, 0): ((32, 30), (31, 0, 0)),
        Coord(1, 1): ((32, 31), (31, 30, 0)),
    }


def test_tile_at_uses_cached_snapshot_after_refresh() -> None:
    capture = FakeCapture(DummyBoardPixels(4, 4))
    classifier = RecordingClassifier()
    coord = Coord(0, 0)
    classifier.tiles[coord] = Tile(coord=coord, state=TileState.HIDDEN, is_mine=False)
    reader = ScreenBoardReader(
        capture=capture,
        classifier=classifier,
        board_region=ScreenRegion(0, 0, 4, 4),
        tile_size=TileSize(4, 4),
        width=1,
        height=1,
        num_mines=1,
    )

    reader.refresh()
    classifier.tiles[coord] = Tile(coord=coord, state=TileState.FLAGGED, is_mine=False)

    assert reader.tile_at(coord).state == TileState.HIDDEN


def test_refresh_preserves_successfully_placed_external_flags_when_classifier_still_reads_hidden() -> None:
    capture = FakeCapture(DummyBoardPixels(4, 4))
    classifier = RecordingClassifier()
    coord = Coord(0, 0)
    classifier.tiles[coord] = Tile(coord=coord, state=TileState.HIDDEN, is_mine=False)
    reader = ScreenBoardReader(
        capture=capture,
        classifier=classifier,
        board_region=ScreenRegion(0, 0, 4, 4),
        tile_size=TileSize(4, 4),
        width=1,
        height=1,
        num_mines=1,
    )

    reader.refresh()
    reader.remember_moves([Move(ActionType.FLAG, coord)])
    reader.refresh()

    assert reader.tile_at(coord).state == TileState.FLAGGED


def test_reader_marks_successfully_clicked_reveals_as_externally_resolved_until_refresh_confirms_them() -> None:
    capture = FakeCapture(DummyBoardPixels(4, 4))
    classifier = RecordingClassifier()
    coord = Coord(0, 0)
    classifier.tiles[coord] = Tile(coord=coord, state=TileState.HIDDEN, is_mine=False)
    reader = ScreenBoardReader(
        capture=capture,
        classifier=classifier,
        board_region=ScreenRegion(0, 0, 4, 4),
        tile_size=TileSize(4, 4),
        width=1,
        height=1,
        num_mines=1,
    )

    reader.refresh()
    reader.remember_moves([Move(ActionType.REVEAL, coord)])

    assert reader.is_externally_resolved(coord) is True

    classifier.tiles[coord] = Tile(coord=coord, state=TileState.REVEALED, is_mine=False, adjacent_mines=0)
    reader.refresh()

    assert reader.is_externally_resolved(coord) is False


def test_tile_at_before_refresh_raises_runtime_error() -> None:
    reader = ScreenBoardReader(
        capture=FakeCapture(DummyBoardPixels(4, 4)),
        classifier=RecordingClassifier(),
        board_region=ScreenRegion(0, 0, 4, 4),
        tile_size=TileSize(4, 4),
        width=1,
        height=1,
        num_mines=1,
    )

    with pytest.raises(RuntimeError, match="refresh"):
        reader.tile_at(Coord(0, 0))


def test_tile_at_out_of_bounds_raises_key_error() -> None:
    reader = ScreenBoardReader(
        capture=FakeCapture(DummyBoardPixels(4, 4)),
        classifier=RecordingClassifier(),
        board_region=ScreenRegion(0, 0, 4, 4),
        tile_size=TileSize(4, 4),
        width=1,
        height=1,
        num_mines=1,
    )
    reader.refresh()

    with pytest.raises(KeyError):
        reader.tile_at(Coord(-1, 0))

    with pytest.raises(KeyError):
        reader.tile_at(Coord(1, 0))

    with pytest.raises(KeyError):
        reader.tile_at(Coord(0, 1))


def test_refresh_raises_board_read_error_when_any_tile_cannot_be_classified() -> None:
    reader = ScreenBoardReader(
        capture=FakeCapture(DummyBoardPixels(4, 4)),
        classifier=ExplodingClassifier(),
        board_region=ScreenRegion(0, 0, 4, 4),
        tile_size=TileSize(4, 4),
        width=1,
        height=1,
        num_mines=1,
    )

    with pytest.raises(BoardReadError, match="board refresh failed"):
        reader.refresh()


def test_refresh_writes_sequential_runtime_captures(tmp_path: Path) -> None:
    saved_paths: list[Path] = []
    capture = FakeCapture(SavingBoardPixels(4, 4, saved_paths))
    reader = ScreenBoardReader(
        capture=capture,
        classifier=RecordingClassifier(),
        board_region=ScreenRegion(0, 0, 4, 4),
        tile_size=TileSize(4, 4),
        width=1,
        height=1,
        num_mines=1,
        debug_capture_dir=tmp_path,
    )

    reader.refresh()
    reader.refresh()

    assert saved_paths == [
        tmp_path / "runtime" / "refresh_000.png",
        tmp_path / "runtime" / "refresh_001.png",
    ]


def test_save_move_overlay_uses_latest_snapshot_and_tile_bounds(tmp_path: Path) -> None:
    overlays: list[tuple[Path, tuple[int, int, int, int], tuple[int, int], str]] = []
    metadata_writes: list[tuple[Path, dict[str, object]]] = []
    capture = FakeCapture(SavingBoardPixels(63, 61, []))
    reader = ScreenBoardReader(
        capture=capture,
        classifier=RecordingClassifier(),
        board_region=ScreenRegion(100, 200, 63, 61),
        tile_size=TileSize(31, 30),
        width=2,
        height=2,
        num_mines=3,
        grid=TileGrid(
            origin_left=100,
            origin_top=200,
            col_boundaries=(0, 31, 63),
            row_boundaries=(0, 30, 61),
        ),
        debug_capture_dir=tmp_path,
    )

    reader.refresh()
    reader.save_move_overlay(
        coord=Coord(1, 1),
        click_point=(147, 245),
        label="REVEAL (1,1)",
        batch_index=2,
        move_index=7,
        move_index_in_batch=3,
        batch_size=5,
        dump_overlay=lambda image, path, tile_bounds, click_point, label, warn: overlays.append(
            (Path(path), tile_bounds, click_point, label)
        ),
        write_metadata=lambda payload, path, warn: metadata_writes.append((Path(path), payload)),
    )

    assert overlays == [
        (
            tmp_path / "runtime" / "move_000.png",
            (131, 230, 162, 260),
            (147, 245),
            "REVEAL (1,1)",
        )
    ]
    assert metadata_writes == [
        (
            tmp_path / "runtime" / "move_000.json",
            {
                "move_index": 7,
                "batch_index": 2,
                "move_index_in_batch": 3,
                "batch_size": 5,
                "coord": {"x": 1, "y": 1},
                "click_point": {"x": 147, "y": 245},
                "tile_bounds": {"left": 131, "top": 230, "right": 162, "bottom": 260},
                "label": "REVEAL (1,1)",
            },
        )
    ]
