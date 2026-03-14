import pytest

from minesweeper.domain.tile import Tile
from minesweeper.domain.types import Coord, TileState
from minesweeper.external.board_reader import ScreenBoardReader
from minesweeper.external.capture import ScreenRegion, TileSize


class DummyBoardPixels:
    def __init__(self, width: int, height: int) -> None:
        self.size = (width, height)

    def getpixel(self, position: tuple[int, int]) -> tuple[int, int, int]:
        x, y = position
        return (x, y, 0)


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
