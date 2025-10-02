class StatisticsTracker:
    """Tracks game statistics and win rate."""

    def __init__(self):
        self.games_played = 1
        self.games_won = 1
        self.last_can_be_evaluated = False

    def mark_if_can_be_evaluated(self, evaluable: bool):
        """Mark whether the current game can be evaluated for statistics."""
        self.last_can_be_evaluated = evaluable

    def update(self, won: bool):
        """Update statistics after a game ends."""
        if self.last_can_be_evaluated:
            self.games_played += 1
            if won:
                self.games_won += 1

    def get_win_rate(self) -> float:
        """Calculate and return the current win rate."""
        return self.games_won / self.games_played