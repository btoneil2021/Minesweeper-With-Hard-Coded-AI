from __future__ import annotations

from typing import Protocol

from minesweeper.external.config import TimingConfig


class ExternalAdapter(Protocol):
    def classifier_config(self) -> dict[str, object]:
        ...

    def timing_config(self) -> TimingConfig:
        ...
