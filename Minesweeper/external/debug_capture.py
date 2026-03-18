from __future__ import annotations

import json
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


def write_debug_metadata(payload: dict[str, object], path: Path, warn: Callable[[str], None]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception:
        warn(f"Debug metadata could not be saved to {path}")


def dump_move_overlay(
    image: Any,
    path: Path,
    *,
    tile_bounds: tuple[int, int, int, int],
    click_point: tuple[int, int],
    label: str,
    warn: Callable[[str], None],
    draw_factory: Callable[[Any], Any] | None = None,
) -> None:
    copy = getattr(image, "copy", None)
    save = getattr(image, "save", None)
    if not callable(copy) or not callable(save):
        warn(f"Debug capture could not be annotated at {path}")
        return

    annotated = copy()
    draw = _build_draw(annotated, draw_factory)
    if draw is None:
        warn(f"Debug capture could not be annotated at {path}")
        return

    left, top, right, bottom = tile_bounds
    x, y = click_point
    draw.rectangle((left, top, right, bottom), outline="#ff00ff", width=3)
    inner_left = min(right, left + 2)
    inner_top = min(bottom, top + 2)
    inner_right = max(inner_left, right - 2)
    inner_bottom = max(inner_top, bottom - 2)
    draw.rectangle((inner_left, inner_top, inner_right, inner_bottom), outline="#ffff00", width=1)
    draw.line(((x, top), (x, bottom)), fill="#00ffff", width=1)
    draw.line(((left, y), (right, y)), fill="#00ffff", width=1)
    draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill="#00ffff", outline="white", width=1)
    draw.text((left, max(0, top - 12)), label, fill="#ff00ff")

    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        annotated.save(path)
    except Exception:
        warn(f"Debug capture could not be annotated at {path}")


def _build_draw(image: Any, draw_factory: Callable[[Any], Any] | None) -> Any | None:
    if draw_factory is not None:
        return draw_factory(image)

    try:
        from PIL import ImageDraw
    except ImportError:
        return None

    return ImageDraw.Draw(image)
