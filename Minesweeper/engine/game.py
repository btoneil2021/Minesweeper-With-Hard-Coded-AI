import random
from collections.abc import Sequence

from minesweeper.domain.move import Move
from minesweeper.domain.types import ActionType, Coord, GameConfig, GamePhase, TileState
from minesweeper.engine.board_impl import Board


class Game:
    """Concrete game engine."""

    def __init__(self, config: GameConfig, rng: random.Random | None = None) -> None:
        self._rng = rng
        self._board = Board(config, rng)
        self._phase = GamePhase.NOT_STARTED

    @property
    def phase(self) -> GamePhase:
        return self._phase

    @property
    def board(self) -> Board:
        return self._board

    def apply_move(self, move: Move) -> Sequence[Coord]:
        if self._phase in {GamePhase.WON, GamePhase.LOST}:
            raise ValueError("Cannot apply moves after the game is over")

        if move.action == ActionType.REVEAL:
            try:
                tile = self._board.tile_at(move.coord)
            except KeyError as exc:
                raise ValueError("Move is out of bounds") from exc

            if tile.state == TileState.REVEALED:
                raise ValueError("Tile is already revealed")

            if tile.state == TileState.FLAGGED:
                raise ValueError("Flagged tiles must be unflagged before revealing")

            starting_move = self._phase == GamePhase.NOT_STARTED
            if starting_move:
                self._phase = GamePhase.IN_PROGRESS
                if tile.is_mine:
                    self._board.relocate_mine(move.coord)
                    tile = self._board.tile_at(move.coord)

            if tile.is_mine and not starting_move:
                self._board.set_state(move.coord, TileState.EXPLODED)
                self._phase = GamePhase.LOST
                return [move.coord]

            changed = self._reveal_from(move.coord)
            if self._all_safe_tiles_revealed():
                self._phase = GamePhase.WON
            return changed

        if move.action == ActionType.FLAG:
            try:
                tile = self._board.tile_at(move.coord)
            except KeyError as exc:
                raise ValueError("Move is out of bounds") from exc

            if tile.state != TileState.HIDDEN:
                raise ValueError("Only hidden tiles can be flagged")

            self._board.set_state(move.coord, TileState.FLAGGED)
            return [move.coord]

        if move.action == ActionType.UNFLAG:
            try:
                tile = self._board.tile_at(move.coord)
            except KeyError as exc:
                raise ValueError("Move is out of bounds") from exc

            if tile.state != TileState.FLAGGED:
                raise ValueError("Only flagged tiles can be unflagged")

            self._board.set_state(move.coord, TileState.HIDDEN)
            return [move.coord]

        return []

    def _all_safe_tiles_revealed(self) -> bool:
        for x in range(self._board.width):
            for y in range(self._board.height):
                tile = self._board.tile_at(Coord(x, y))
                if not tile.is_mine and tile.state != TileState.REVEALED:
                    return False

        return True

    def _reveal_from(self, start: Coord) -> list[Coord]:
        changed: list[Coord] = []
        queue = [start]
        seen: set[Coord] = set()

        while queue:
            coord = queue.pop()
            if coord in seen:
                continue
            seen.add(coord)

            try:
                tile = self._board.tile_at(coord)
            except KeyError:
                continue

            if tile.is_mine or tile.state != TileState.HIDDEN:
                continue

            self._board.set_state(coord, TileState.REVEALED)
            changed.append(coord)

            if tile.adjacent_mines != 0:
                continue

            for neighbor in coord.neighbors():
                try:
                    neighbor_tile = self._board.tile_at(neighbor)
                except KeyError:
                    continue

                if neighbor_tile.is_mine or neighbor_tile.state != TileState.HIDDEN:
                    continue

                if neighbor_tile.adjacent_mines == 0:
                    queue.append(neighbor)
                    continue

                self._board.set_state(neighbor, TileState.REVEALED)
                changed.append(neighbor)
                seen.add(neighbor)

        return changed

    def reset(self, config: GameConfig) -> None:
        self._board = Board(config, self._rng)
        self._phase = GamePhase.NOT_STARTED
