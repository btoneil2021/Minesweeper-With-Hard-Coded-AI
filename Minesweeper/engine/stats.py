from typing import NamedTuple


class GameResult(NamedTuple):
    won: bool
    is_evaluable: bool


class StatsTracker:
    def __init__(self) -> None:
        self._wins = 0
        self._evaluable_games = 0

    def record(self, result: GameResult) -> None:
        if not result.is_evaluable:
            return

        self._evaluable_games += 1
        if result.won:
            self._wins += 1

    @property
    def win_rate(self) -> float:
        if self._evaluable_games == 0:
            return 0.0

        return self._wins / self._evaluable_games
