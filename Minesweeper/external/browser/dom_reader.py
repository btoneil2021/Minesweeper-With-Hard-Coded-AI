from __future__ import annotations

from minesweeper.external.browser.protocol import BoardSnapshotPayload, TilePayload
from minesweeper.domain.tile import Tile
from minesweeper.domain.types import Coord, TileState


class DomBoardReader:
    """Snapshot-backed board view for a minesweeperonline DOM payload."""

    def __init__(self, snapshot: BoardSnapshotPayload, num_mines: int) -> None:
        self._snapshot = snapshot
        self._num_mines = num_mines
        self._tiles: dict[Coord, Tile] = {}
        self._load_snapshot(snapshot)

    @property
    def width(self) -> int:
        return self._snapshot.width

    @property
    def height(self) -> int:
        return self._snapshot.height

    @property
    def num_mines(self) -> int:
        return self._num_mines

    def update_snapshot(self, snapshot: BoardSnapshotPayload) -> None:
        self._snapshot = snapshot
        self._load_snapshot(snapshot)

    def tile_at(self, coord: Coord) -> Tile:
        if not (0 <= coord.x < self.width and 0 <= coord.y < self.height):
            raise KeyError(coord)
        return self._tiles[coord]

    def _load_snapshot(self, snapshot: BoardSnapshotPayload) -> None:
        self._tiles = {
            Coord(tile.x, tile.y): self._tile_from_payload(tile)
            for tile in snapshot.tiles
        }
        if len(self._tiles) != snapshot.width * snapshot.height:
            raise ValueError("snapshot does not cover the full declared board")

    def _tile_from_payload(self, payload: TilePayload) -> Tile:
        coord = Coord(payload.x, payload.y)
        if payload.state == "hidden":
            return Tile(coord=coord, state=TileState.HIDDEN, is_mine=False)
        if payload.state == "flagged":
            return Tile(coord=coord, state=TileState.FLAGGED, is_mine=False)
        if payload.state == "exploded":
            return Tile(coord=coord, state=TileState.EXPLODED, is_mine=True)
        if payload.state == "mine_revealed":
            return Tile(coord=coord, state=TileState.REVEALED, is_mine=True, adjacent_mines=0)
        return Tile(
            coord=coord,
            state=TileState.REVEALED,
            is_mine=False,
            adjacent_mines=payload.adjacent_mines or 0,
        )
