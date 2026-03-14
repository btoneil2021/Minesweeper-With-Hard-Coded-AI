from minesweeper.domain.move import Move
from minesweeper.domain.tile import Tile
from minesweeper.domain.types import (
    AI_ONLY,
    HYBRID,
    PLAYER_ONLY,
    ActionType,
    Coord,
    GamePhase,
    TileState,
)


def test_remaining_domain_contracts() -> None:
    tile = Tile(coord=Coord(1, 2), state=TileState.HIDDEN, is_mine=False)
    move = Move(action=ActionType.REVEAL, coord=Coord(1, 2))

    assert TileState.HIDDEN.name == "HIDDEN"
    assert ActionType.REVEAL.name == "REVEAL"
    assert GamePhase.NOT_STARTED.name == "NOT_STARTED"
    assert tile.adjacent_mines == 0
    assert move.coord == Coord(1, 2)
    assert AI_ONLY.name == "AI Only"
    assert AI_ONLY.player_input is False
    assert AI_ONLY.ai_enabled is True
    assert PLAYER_ONLY.player_input is True
    assert PLAYER_ONLY.ai_enabled is False
    assert HYBRID.player_input is True
    assert HYBRID.ai_enabled is True
    assert HYBRID.ai_togglable is True
