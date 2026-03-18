from __future__ import annotations

import json
from pathlib import Path

from minesweeper.external.calibration import CalibrationResult
from minesweeper.external.config import DiagnosticsConfig, TimingConfig


class DiagnosticsRecorder:
    def __init__(
        self,
        config: DiagnosticsConfig | None,
        calibration: CalibrationResult,
        timing: TimingConfig,
    ) -> None:
        self._config = config or DiagnosticsConfig()
        self._calibration = calibration
        self._timing = timing
        self._root = self._config.debug_root

    def record_session(self) -> None:
        if not self._should_record():
            return
        self._write_json(
            self._root / "session.json",
            {
                "width": self._calibration.width,
                "height": self._calibration.height,
                "num_mines": self._calibration.num_mines,
                "diagnostics_mode": self._config.mode,
                "post_batch_settle_ms": self._timing.post_batch_settle_ms,
            },
        )

    def record_failure(self, reason: str) -> None:
        if not self._should_record():
            return
        if self._config.mode not in {"failure-only", "always"}:
            return
        self._write_json(
            self._root / "failures" / "latest_failure.json",
            {"reason": reason},
        )

    def _should_record(self) -> bool:
        return (
            self._config.capture_artifacts
            and self._config.mode != "off"
            and self._root is not None
        )

    def _write_json(self, path: Path, payload: dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
