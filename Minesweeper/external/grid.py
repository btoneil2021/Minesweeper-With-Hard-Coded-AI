from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from minesweeper.domain.types import Coord
from minesweeper.external.capture import ScreenRegion

PixelGrid = Any
SITE_MIN_PITCH = 23
SITE_MAX_PITCH = 27
SITE_EDGE_DIFF = 20
SITE_EDGE_THRESHOLD_RATIO = 0.45
SITE_PEAK_TOLERANCE = 3
SITE_MIN_SEQUENCE = 4


@dataclass(frozen=True)
class TileGrid:
    origin_left: int
    origin_top: int
    col_boundaries: tuple[int, ...]
    row_boundaries: tuple[int, ...]

    @property
    def width(self) -> int:
        return len(self.col_boundaries) - 1

    @property
    def height(self) -> int:
        return len(self.row_boundaries) - 1

    def tile_rect(self, coord: Coord) -> ScreenRegion:
        left = self.origin_left + self.col_boundaries[coord.x]
        right = self.origin_left + self.col_boundaries[coord.x + 1]
        top = self.origin_top + self.row_boundaries[coord.y]
        bottom = self.origin_top + self.row_boundaries[coord.y + 1]
        return ScreenRegion(left=left, top=top, width=right - left, height=bottom - top)

    def click_target(self, coord: Coord, inset: int = 4) -> tuple[int, int]:
        rect = self.tile_rect(coord)
        safe_width = max(1, rect.width - inset * 2)
        safe_height = max(1, rect.height - inset * 2)
        x = rect.left + inset + safe_width // 2
        y = rect.top + inset + safe_height // 2
        return (
            min(max(x, rect.left), rect.left + rect.width - 1),
            min(max(y, rect.top), rect.top + rect.height - 1),
        )


def detect_tile_grid(
    pixels: PixelGrid,
    board_left: int,
    board_top: int,
    output: Any | None = None,
) -> TileGrid:
    return TileGrid(
        origin_left=board_left,
        origin_top=board_top,
        col_boundaries=tuple(detect_grid_lines(pixels, axis="x")),
        row_boundaries=tuple(detect_grid_lines(pixels, axis="y")),
    )


def detect_grid_lines(pixels: PixelGrid, axis: str) -> list[int]:
    try:
        return _detect_minesweeperonline_lines(pixels, axis)
    except ValueError:
        pass

    candidates: list[list[int]] = []
    for offset in _scan_offsets(pixels, axis):
        profile = _line_profile(pixels, axis, offset)
        try:
            candidates.append(_detect_grid_lines_from_profile(profile))
        except ValueError:
            continue

    if not candidates:
        raise ValueError("could not detect repeating grid boundaries")

    return max(
        candidates,
        key=lambda boundaries: (len(boundaries), -boundaries[0], -boundaries[-1]),
    )


def _detect_minesweeperonline_lines(pixels: PixelGrid, axis: str) -> list[int]:
    peaks = _site_edge_peaks(pixels, axis)
    pitch = _site_pitch(peaks)
    if pitch <= 0:
        raise ValueError("could not detect repeating grid boundaries")

    sequence = _best_peak_sequence(peaks, pitch)
    if len(sequence) < SITE_MIN_SEQUENCE:
        raise ValueError("could not detect repeating grid boundaries")

    fitted_pitch = round(_median([current - previous for previous, current in zip(sequence, sequence[1:])]))
    if fitted_pitch < SITE_MIN_PITCH or fitted_pitch > SITE_MAX_PITCH:
        raise ValueError("could not detect repeating grid boundaries")

    start = sequence[0]
    boundaries = [start + fitted_pitch * index for index in range(len(sequence))]
    span = pixels.size[0] if axis == "x" else pixels.size[1]
    if _should_extend_lattice(boundaries, fitted_pitch, span):
        boundaries.append(span)
    return boundaries


def _detect_grid_lines_from_profile(profile: list[tuple[int, int, int]]) -> list[int]:
    board_start, board_end = _board_span(profile)
    board_runs = _color_runs(profile[board_start:board_end])
    candidate_runs = [runs for runs in board_runs.values() if len(runs) >= 2]
    if not candidate_runs:
        raise ValueError("could not detect repeating grid boundaries")

    border_runs = min(
        candidate_runs,
        key=lambda runs: (sum(end - start for start, end in runs), -len(runs)),
    )
    boundaries = [board_start + start for start, _end in border_runs]
    boundaries.append(board_end)
    return boundaries


def _scan_offsets(pixels: PixelGrid, axis: str) -> list[int]:
    width, height = pixels.size
    span = height if axis == "x" else width
    if span <= 1:
        return [0]

    sample_count = min(9, span)
    if sample_count == 1:
        return [span // 2]

    offsets = {
        ((index + 1) * span) // (sample_count + 1)
        for index in range(sample_count)
    }
    offsets.add(span // 2)
    return sorted(min(span - 1, max(0, offset)) for offset in offsets)


def _line_profile(pixels: PixelGrid, axis: str, offset: int) -> list[tuple[int, int, int]]:
    width, height = pixels.size
    if axis == "x":
        return [pixels.getpixel((x, offset)) for x in range(width)]
    if axis == "y":
        return [pixels.getpixel((offset, y)) for y in range(height)]
    raise ValueError(f"unsupported axis: {axis}")


def _site_edge_peaks(pixels: PixelGrid, axis: str) -> list[int]:
    scores = _site_edge_scores(pixels, axis)
    if not scores:
        return []
    threshold = max(1, int(max(scores) * SITE_EDGE_THRESHOLD_RATIO))
    return [position for position, score in enumerate(scores, start=1) if score >= threshold]


def _site_edge_scores(pixels: PixelGrid, axis: str) -> list[int]:
    width, height = pixels.size
    scores: list[int] = []
    if axis == "x":
        for x in range(1, width):
            score = 0
            for y in range(height):
                if _brightness_delta(pixels.getpixel((x - 1, y)), pixels.getpixel((x, y))) >= SITE_EDGE_DIFF:
                    score += 1
            scores.append(score)
        return scores
    if axis == "y":
        for y in range(1, height):
            score = 0
            for x in range(width):
                if _brightness_delta(pixels.getpixel((x, y - 1)), pixels.getpixel((x, y))) >= SITE_EDGE_DIFF:
                    score += 1
            scores.append(score)
        return scores
    raise ValueError(f"unsupported axis: {axis}")


def _brightness_delta(left: tuple[int, int, int], right: tuple[int, int, int]) -> int:
    return abs(sum(left) - sum(right)) // 3


def _site_pitch(peaks: list[int]) -> int:
    gaps: list[int] = []
    for index, peak in enumerate(peaks):
        for lookahead in range(index + 1, min(len(peaks), index + 6)):
            gap = peaks[lookahead] - peak
            if SITE_MIN_PITCH <= gap <= SITE_MAX_PITCH:
                gaps.append(gap)
    if not gaps:
        return 0
    return max(Counter(gaps), key=Counter(gaps).get)


def _best_peak_sequence(peaks: list[int], pitch: int) -> list[int]:
    best: list[int] = []
    for start in peaks:
        sequence = [start]
        target = start + pitch
        while target <= peaks[-1] + SITE_PEAK_TOLERANCE:
            match = _nearest_peak(peaks, target)
            if match is None:
                break
            sequence.append(match)
            target += pitch
        if len(sequence) > len(best) or (len(sequence) == len(best) and sequence[0] < best[0]):
            best = sequence
    return best


def _nearest_peak(peaks: list[int], target: int) -> int | None:
    matches = [peak for peak in peaks if abs(peak - target) <= SITE_PEAK_TOLERANCE]
    if not matches:
        return None
    return min(matches, key=lambda peak: (abs(peak - target), peak))


def _median(values: list[int]) -> float:
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return float(ordered[midpoint])
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2


def _should_extend_lattice(boundaries: list[int], pitch: int, span: int) -> bool:
    if not boundaries:
        return False
    remaining = span - boundaries[-1]
    if remaining <= 0:
        return False
    minimum_remaining = max(1, int(pitch * 0.7))
    return minimum_remaining <= remaining <= (pitch + SITE_PEAK_TOLERANCE)


def _color_runs(profile: list[tuple[int, int, int]]) -> dict[tuple[int, int, int], list[tuple[int, int]]]:
    runs: dict[tuple[int, int, int], list[tuple[int, int]]] = {}
    if not profile:
        return runs

    start = 0
    current = profile[0]
    for index, color in enumerate(profile[1:], start=1):
        if color == current:
            continue
        runs.setdefault(current, []).append((start, index))
        start = index
        current = color
    runs.setdefault(current, []).append((start, len(profile)))
    return runs


def _board_span(profile: list[tuple[int, int, int]]) -> tuple[int, int]:
    left_pad = profile[0]
    right_pad = profile[-1]

    start = 0
    while start < len(profile) and profile[start] == left_pad:
        start += 1

    end = len(profile)
    while end > start and profile[end - 1] == right_pad:
        end -= 1

    if start >= end:
        raise ValueError("could not locate board content")
    return start, end
