from minesweeper.external.errors import (
    AdapterError,
    BoardReadError,
    CalibrationError,
    ExecutionError,
    ExternalRuntimeError,
)
from minesweeper.external.runtime import STOP_REASONS


def test_external_errors_share_a_common_base() -> None:
    assert issubclass(CalibrationError, ExternalRuntimeError)
    assert issubclass(BoardReadError, ExternalRuntimeError)
    assert issubclass(ExecutionError, ExternalRuntimeError)
    assert issubclass(AdapterError, ExternalRuntimeError)


def test_stop_reasons_expose_canonical_spec_strings() -> None:
    assert STOP_REASONS.terminal_board_detected == "terminal board detected"
    assert STOP_REASONS.execution_failed == "execution failed"
