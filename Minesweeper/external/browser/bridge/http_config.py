from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BridgeHttpConfig:
    host: str = "127.0.0.1"
    port: int = 8765

    def __post_init__(self) -> None:
        if self.host != "127.0.0.1":
            raise ValueError(f"host must be loopback-only for now: {self.host}")
        if not (1 <= self.port <= 65535):
            raise ValueError(f"port must be in range 1..65535: {self.port}")
