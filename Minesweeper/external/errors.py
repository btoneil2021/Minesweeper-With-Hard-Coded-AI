class ExternalRuntimeError(RuntimeError):
    """Base class for external runtime failures."""


class CalibrationError(ExternalRuntimeError):
    """Raised when external calibration cannot complete."""


class BoardReadError(ExternalRuntimeError):
    """Raised when a board snapshot cannot be read reliably."""


class ExecutionError(ExternalRuntimeError):
    """Raised when external move execution fails."""


class AdapterError(ExternalRuntimeError):
    """Raised when adapter hooks fail or return invalid data."""
