import pytest

from minesweeper.domain.types import Coord
from minesweeper.external.capture import CaptureError, ScreenCapture, ScreenRegion, TileSize


class StubMSS:
    def __init__(self) -> None:
        self.monitors = [{"left": 0, "top": 0, "width": 100, "height": 80}]
        self.regions: list[dict[str, int]] = []

    def grab(self, region: dict[str, int]) -> dict[str, int]:
        self.regions.append(region)
        return region


def test_screen_capture_prefers_mss_backend() -> None:
    backend = StubMSS()
    pillow_calls: list[tuple[int, int, int, int]] = []

    def fake_pillow(bbox: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        pillow_calls.append(bbox)
        return bbox

    capture = ScreenCapture(mss_factory=lambda: backend, image_grab=fake_pillow)

    result = capture.grab(ScreenRegion(10, 20, 30, 40))

    assert result == {"left": 10, "top": 20, "width": 30, "height": 40}
    assert backend.regions == [{"left": 10, "top": 20, "width": 30, "height": 40}]
    assert pillow_calls == []


def test_screen_capture_falls_back_to_pillow_backend() -> None:
    pillow_calls: list[tuple[int, int, int, int]] = []

    def fake_pillow(bbox: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        pillow_calls.append(bbox)
        return bbox

    capture = ScreenCapture(
        mss_factory=lambda: None,
        image_grab=fake_pillow,
        screen_size=(100, 80),
    )

    result = capture.grab(ScreenRegion(3, 4, 5, 6))

    assert result == (3, 4, 8, 10)
    assert pillow_calls == [(3, 4, 8, 10)]


def test_screen_capture_raises_capture_error_without_backend() -> None:
    capture = ScreenCapture(
        mss_factory=lambda: None,
        image_grab=None,
        screen_size=(100, 80),
    )

    with pytest.raises(CaptureError, match="No screenshot backend"):
        capture.grab(ScreenRegion(0, 0, 10, 10))


def test_grab_tile_uses_tile_subregion() -> None:
    pillow_calls: list[tuple[int, int, int, int]] = []

    def fake_pillow(bbox: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        pillow_calls.append(bbox)
        return bbox

    capture = ScreenCapture(
        mss_factory=lambda: None,
        image_grab=fake_pillow,
        screen_size=(100, 80),
    )

    result = capture.grab_tile(
        ScreenRegion(10, 15, 50, 40),
        Coord(2, 1),
        TileSize(10, 10),
    )

    assert result == (30, 25, 40, 35)
    assert pillow_calls == [(30, 25, 40, 35)]


def test_grab_rejects_region_outside_screen_bounds() -> None:
    capture = ScreenCapture(
        mss_factory=lambda: None,
        image_grab=lambda bbox: bbox,
        screen_size=(100, 80),
    )

    with pytest.raises(ValueError, match="outside screen bounds"):
        capture.grab(ScreenRegion(90, 70, 20, 20))
