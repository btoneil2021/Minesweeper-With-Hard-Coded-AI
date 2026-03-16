"""External screen-reading bot adapters."""

from minesweeper.external.app import ExternalApp
from minesweeper.external.capture import CaptureError, ScreenCapture, ScreenRegion, TileSize
from minesweeper.external.calibration import CalibrationResult, CalibrationWizard
from minesweeper.external.classifier import ColorProfiles, TileClassifier
from minesweeper.external.board_reader import ScreenBoardReader
from minesweeper.external.executor import ScreenMoveExecutor
from minesweeper.external.grid import TileGrid

__all__ = [
    "CaptureError",
    "CalibrationResult",
    "CalibrationWizard",
    "ColorProfiles",
    "ExternalApp",
    "ScreenCapture",
    "ScreenRegion",
    "ScreenBoardReader",
    "ScreenMoveExecutor",
    "TileGrid",
    "TileSize",
    "TileClassifier",
]
