class StatisticsTracker:
    """Tracks game statistics and win rate."""

    def __init__(self):
        self.games_played = 0
        self.games_won = 0
        self.last_can_be_evaluated = False

    def mark_if_can_be_evaluated(self, evaluable: bool):
        """Mark whether the current game can be evaluated for statistics."""
        self.last_can_be_evaluated = evaluable

    def update(self, won: bool):
        """Update statistics after a game ends."""
        if not self.last_can_be_evaluated:
            return
        self.games_played += 1
        if won:
            self.games_won += 1
        self.last_can_be_evaluated = False

    def get_win_rate(self) -> float:
        """Calculate and return the current win rate."""
        if self.games_played == 0:
            return 0.0
        return self.games_won / self.games_played