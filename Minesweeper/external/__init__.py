"""External screen-reading bot adapters."""

from minesweeper.external.adapter import ExternalAdapter
from minesweeper.external.api import calibrate, read_once, run
from minesweeper.external.app import ExternalApp
from minesweeper.external.capture import CaptureError, ScreenCapture, ScreenRegion, TileSize
from minesweeper.external.calibration import CalibrationResult, CalibrationWizard
from minesweeper.external.classifier import ColorProfiles, TileClassifier
from minesweeper.external.board_reader import ScreenBoardReader
from minesweeper.external.config import DiagnosticsConfig, RetryPolicy, TimingConfig
from minesweeper.external.diagnostics import DiagnosticsRecorder
from minesweeper.external.executor import ScreenMoveExecutor
from minesweeper.external.errors import (
    AdapterError,
    BoardReadError,
    CalibrationError,
    ExecutionError,
    ExternalRuntimeError,
)
from minesweeper.external.grid import TileGrid
from minesweeper.external.runtime import STOP_REASONS, StopReasons

__all__ = [
    "AdapterError",
    "BoardReadError",
    "CaptureError",
    "CalibrationError",
    "CalibrationResult",
    "CalibrationWizard",
    "ColorProfiles",
    "DiagnosticsConfig",
    "DiagnosticsRecorder",
    "ExternalAdapter",
    "ExecutionError",
    "ExternalApp",
    "ExternalRuntimeError",
    "RetryPolicy",
    "ScreenCapture",
    "ScreenRegion",
    "ScreenBoardReader",
    "ScreenMoveExecutor",
    "STOP_REASONS",
    "StopReasons",
    "TimingConfig",
    "TileGrid",
    "TileSize",
    "TileClassifier",
    "calibrate",
    "read_once",
    "run",
]
