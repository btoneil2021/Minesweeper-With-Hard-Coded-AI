from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from minesweeper.ai.analyzer import Analyzer
from minesweeper.ai.strategy import AIStrategy
from minesweeper.domain.tile import Tile
from minesweeper.external.app import ExternalApp
from minesweeper.external.adapter import ExternalAdapter
from minesweeper.external.calibration import CalibrationResult, CalibrationWizard
from minesweeper.external.capture import ScreenCapture
from minesweeper.external.classifier import TileClassifier
from minesweeper.external.config import DiagnosticsConfig, RetryPolicy, TimingConfig
from minesweeper.external.diagnostics import DiagnosticsRecorder
from minesweeper.external.errors import CalibrationError
from minesweeper.external.executor import ScreenMoveExecutor
from minesweeper.domain.types import Coord
from minesweeper.external.board_reader import ScreenBoardReader
from minesweeper.external.runtime import STOP_REASONS


def calibrate(
    capture: ScreenCapture | None = None,
    *,
    adapter: ExternalAdapter | None = None,
    debug_capture_dir: Path | None = None,
    capture_point: Callable[[str], tuple[int, int]] | None = None,
    read_point: Callable[[str], tuple[int, int]] | None = None,
    read_int: Callable[[str], int] | None = None,
    click: Callable[[int, int], None] | None = None,
    sleep: Callable[[float], None] | None = None,
    timing: TimingConfig | None = None,
    output: Callable[[str], None] | None = None,
) -> CalibrationResult:
    runtime_capture = capture or ScreenCapture()
    timing_config = timing or _adapter_timing(adapter)
    wizard = CalibrationWizard(
        runtime_capture,
        capture_point=capture_point,
        read_point=read_point,
        read_int=read_int,
        click=click,
        sleep=sleep,
        settle_delay_ms=timing_config.calibration_click_settle_ms,
        output=output,
        debug_capture_dir=debug_capture_dir,
    )
    try:
        return wizard.run()
    except CalibrationError:
        raise
    except Exception as exc:
        raise CalibrationError(str(exc)) from exc


def read_once(
    calibration: CalibrationResult,
    *,
    adapter: ExternalAdapter | None = None,
    debug_capture_dir: Path | None = None,
    capture: ScreenCapture | None = None,
    classifier: TileClassifier | None = None,
) -> dict[Coord, Tile]:
    runtime_capture = capture or ScreenCapture()
    runtime_classifier = classifier or TileClassifier(
        calibration.profiles,
        **_adapter_classifier_config(adapter),
    )
    board_reader = calibration_read_board_reader(
        calibration,
        capture=runtime_capture,
        classifier=runtime_classifier,
        debug_capture_dir=debug_capture_dir,
    )
    board_reader.refresh()
    return {
        tile.coord: tile
        for x in range(board_reader.width)
        for y in range(board_reader.height)
        for tile in [board_reader.tile_at(Coord(x, y))]
    }


def run(
    calibration: CalibrationResult | None = None,
    *,
    adapter: ExternalAdapter | None = None,
    debug_capture_dir: Path | None = None,
    capture: ScreenCapture | None = None,
    classifier: TileClassifier | None = None,
    board_reader: ScreenBoardReader | None = None,
    executor: ScreenMoveExecutor | None = None,
    analyzer: Analyzer | None = None,
    strategies: Sequence[AIStrategy] | None = None,
    sleep: Callable[[float], None] | None = None,
    output: Callable[[str], None] | None = None,
    timing: TimingConfig | None = None,
    diagnostics: DiagnosticsConfig | None = None,
    retry: RetryPolicy | None = None,
) -> Any:
    retry_config = retry or RetryPolicy()
    try:
        runtime_calibration = calibration or calibrate(
            capture=capture,
            adapter=adapter,
            debug_capture_dir=debug_capture_dir,
            sleep=sleep,
            timing=timing,
            output=output,
        )
    except CalibrationError:
        return STOP_REASONS.calibration_failed
    timing_config = timing or _adapter_timing(adapter)
    runtime_classifier = classifier or TileClassifier(
        runtime_calibration.profiles,
        **_adapter_classifier_config(adapter),
    )
    recorder = DiagnosticsRecorder(diagnostics, runtime_calibration, timing_config)
    recorder.record_session()
    app = ExternalApp(
        runtime_calibration,
        settle_delay_ms=timing_config.post_batch_settle_ms,
        click_delay_ms=timing_config.inter_click_delay_ms,
        capture=capture,
        classifier=runtime_classifier,
        board_reader=board_reader,
        executor=executor,
        analyzer=analyzer,
        strategies=strategies,
        sleep=sleep,
        output=output,
        board_read_retries=retry_config.board_read_retries,
        unchanged_board_retries=retry_config.unchanged_board_retries,
        debug_capture_dir=debug_capture_dir,
    )
    reason = app.run()
    if reason in {
        STOP_REASONS.board_refresh_failed_after_retry,
        STOP_REASONS.execution_failed,
        STOP_REASONS.calibration_failed,
    }:
        recorder.record_failure(reason)
    return reason


def _adapter_classifier_config(adapter: ExternalAdapter | None) -> dict[str, object]:
    if adapter is None:
        return {}
    return adapter.classifier_config()


def _adapter_timing(adapter: ExternalAdapter | None) -> TimingConfig:
    if adapter is None:
        return TimingConfig()
    return adapter.timing_config()


def calibration_read_board_reader(
    calibration: CalibrationResult,
    *,
    capture: ScreenCapture,
    classifier: TileClassifier,
    debug_capture_dir: Path | None = None,
):
    from minesweeper.external.board_reader import ScreenBoardReader

    return ScreenBoardReader(
        capture=capture,
        classifier=classifier,
        board_region=calibration.board_region,
        tile_size=calibration.tile_size,
        width=calibration.width,
        height=calibration.height,
        num_mines=calibration.num_mines,
        grid=calibration.grid,
        debug_capture_dir=debug_capture_dir,
    )
