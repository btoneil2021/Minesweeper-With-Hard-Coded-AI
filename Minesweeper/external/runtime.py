from __future__ import annotations

from typing import NamedTuple


class StopReasons(NamedTuple):
    terminal_board_detected: str = "terminal board detected"
    no_moves_available: str = "no moves available"
    board_unchanged_after_retry: str = "board unchanged after retry"
    board_refresh_failed_after_retry: str = "board refresh failed after retry"
    calibration_failed: str = "calibration failed"
    unsupported_move_type: str = "unsupported move type"
    execution_failed: str = "execution failed"


STOP_REASONS = StopReasons()
