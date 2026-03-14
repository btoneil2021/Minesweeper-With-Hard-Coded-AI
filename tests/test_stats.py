from minesweeper.engine.stats import GameResult, StatsTracker


def test_win_rate_starts_at_zero() -> None:
    assert StatsTracker().win_rate == 0.0


def test_non_evaluable_games_do_not_count() -> None:
    stats = StatsTracker()

    stats.record(GameResult(won=False, is_evaluable=False))

    assert stats.win_rate == 0.0


def test_evaluable_games_compute_win_rate() -> None:
    stats = StatsTracker()

    stats.record(GameResult(won=True, is_evaluable=True))
    stats.record(GameResult(won=False, is_evaluable=True))
    stats.record(GameResult(won=True, is_evaluable=False))

    assert stats.win_rate == 0.5
