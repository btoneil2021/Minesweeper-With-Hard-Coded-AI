from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from typing import Any, NamedTuple

from minesweeper.domain.types import Coord

PixelGrid = Any


class CaptureError(RuntimeError):
    """Raised when screen capture cannot be performed."""


class ScreenRegion(NamedTuple):
    left: int
    top: int
    width: int
    height: int


class TileSize(NamedTuple):
    width: int
    height: int


def _load_mss_backend() -> Any | None:
    try:
        module = import_module("mss")
    except ImportError:
        return None

    return module.mss()


def _load_image_grab() -> Callable[[tuple[int, int, int, int]], PixelGrid] | None:
    try:
        image_grab = import_module("PIL.ImageGrab")
    except ImportError:
        return None

    return image_grab.grab


class ScreenCapture:
    def __init__(
        self,
        mss_factory: Callable[[], Any | None] | None = None,
        image_grab: Callable[[tuple[int, int, int, int]], PixelGrid] | None = None,
        screen_size: tuple[int, int] | None = None,
    ) -> None:
        self._mss_factory = mss_factory or _load_mss_backend
        self._image_grab = image_grab if image_grab is not None else _load_image_grab()
        self._screen_size = screen_size

    def grab(self, region: ScreenRegion) -> PixelGrid:
        backend = self._mss_factory()
        self._validate_region(region, backend)

        if backend is not None:
            return backend.grab(
                {
                    "left": region.left,
                    "top": region.top,
                    "width": region.width,
                    "height": region.height,
                }
            )

        if self._image_grab is not None:
            return self._image_grab(self._to_bbox(region))

        raise CaptureError("No screenshot backend available")

    def grab_tile(
        self,
        region: ScreenRegion,
        coord: Coord,
        tile_size: TileSize,
    ) -> PixelGrid:
        return self.grab(
            ScreenRegion(
                left=region.left + coord.x * tile_size.width,
                top=region.top + coord.y * tile_size.height,
                width=tile_size.width,
                height=tile_size.height,
            )
        )

    def _validate_region(self, region: ScreenRegion, backend: Any | None) -> None:
        screen_size = self._screen_size or self._screen_size_from_backend(backend)
        if screen_size is None:
            return

        screen_width, screen_height = screen_size
        if (
            region.left < 0
            or region.top < 0
            or region.width <= 0
            or region.height <= 0
            or region.left + region.width > screen_width
            or region.top + region.height > screen_height
        ):
            raise ValueError("Screen region extends outside screen bounds")

    def _screen_size_from_backend(self, backend: Any | None) -> tuple[int, int] | None:
        monitors = getattr(backend, "monitors", None)
        if not monitors:
            return None

        monitor = monitors[0]
        return monitor["width"], monitor["height"]

    def _to_bbox(self, region: ScreenRegion) -> tuple[int, int, int, int]:
        return (
            region.left,
            region.top,
            region.left + region.width,
            region.top + region.height,
        )
