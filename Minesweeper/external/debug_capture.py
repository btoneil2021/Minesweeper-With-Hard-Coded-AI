from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any


def dump_capture(image: Any, path: Path, warn: Callable[[str], None]) -> None:
    save = getattr(image, "save", None)
    if not callable(save):
        warn(f"Debug capture could not be saved to {path}")
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        save(path)
    except Exception:
        warn(f"Debug capture could not be saved to {path}")
