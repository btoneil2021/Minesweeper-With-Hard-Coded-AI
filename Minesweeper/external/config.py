from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class TimingConfig:
    calibration_click_settle_ms: int = 400
    inter_click_delay_ms: int = 40
    post_batch_settle_ms: int = 400


@dataclass(frozen=True)
class RetryPolicy:
    board_read_retries: int = 1
    unchanged_board_retries: int = 1


@dataclass(frozen=True)
class DiagnosticsConfig:
    mode: Literal["off", "failure-only", "always"] = "off"
    debug_root: Path | None = None
    capture_artifacts: bool = False
