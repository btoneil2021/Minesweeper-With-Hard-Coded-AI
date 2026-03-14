# Minesweeper Rewrite

A modern Pygame rewrite of Minesweeper with a built-in AI solver.

The current rewrite lives under the lowercase `minesweeper/` package and separates the project into clear layers:

- `minesweeper/domain/` for shared types and protocols
- `minesweeper/engine/` for board state, rules, and stats
- `minesweeper/ai/` for analysis and solver strategies
- `minesweeper/ui/` for rendering and input translation
- `minesweeper/app.py` for top-level orchestration

The current UI includes:

- a dark, modern board theme
- framed playfield and header bar
- hover feedback for playable tiles
- classic Minesweeper number colors
- asset-backed bomb rendering with fallback behavior

## Requirements

- Python 3.10+
- `pygame`

For development and verification:

- `pytest`
- optionally `mypy`

Example setup:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install pygame pytest mypy
```

## Quick Start

Launch the default player mode:

```bash
python -m minesweeper
```

Show launcher help:

```bash
python -m minesweeper --help
```

## Launch Options

The launcher supports:

- `--mode {player,ai,hybrid}`
- `--width`
- `--height`
- `--mines`
- `--tile-size`
- `--font-size`

Examples:

Player mode:

```bash
python -m minesweeper --mode player
```

AI-only mode:

```bash
python -m minesweeper --mode ai
```

Hybrid mode:

```bash
python -m minesweeper --mode hybrid
```

Classic intermediate-style board:

```bash
python -m minesweeper --mode player --width 16 --height 16 --mines 40
```

Large demo board:

```bash
python -m minesweeper --mode hybrid --width 40 --height 40 --mines 300 --tile-size 20 --font-size 26
```

## Controls

Player input:

- Left click: reveal
- Right click: flag or unflag

AI-enabled modes:

- `Space`: toggle AI on/off when the mode allows toggling
- `S`: run one AI step

## AI Strategy Order

The solver currently evaluates strategies in this order:

1. `RandomExplorer`
2. `PatternDetector`
3. `ConstraintSubtractor`
4. `TransitiveMatcher`
5. `ProbabilitySolver`

The app only counts games as evaluable once the AI has moved beyond the random opening phase.

## Default Configuration

`GameConfig` defaults to:

- width: `30`
- height: `16`
- mines: `99`
- tile size: `20`
- font size: `30`
- restart delay: `1000 ms`
- AI click feedback: `False`

Mine count must always be less than `width * height`.

## Project Layout

```text
minesweeper/
├── __main__.py
├── ai/
├── app.py
├── domain/
├── engine/
└── ui/

tests/
├── test_analyzer.py
├── test_app.py
├── test_board.py
├── test_constraint_subtractor.py
├── test_coord.py
├── test_domain_contracts.py
├── test_game_config.py
├── test_game_engine.py
├── test_main.py
├── test_pattern_detector.py
├── test_probability_solver.py
├── test_random_explorer.py
├── test_renderer.py
├── test_stats.py
└── test_transitive_matcher.py
```

## Verification

Run the automated tests with:

```bash
python3 -m pytest -q -s
```

If you have `mypy` installed, you can also run:

```bash
python3 -m mypy --strict minesweeper
```

## Notes

- The active package is `minesweeper`, not the legacy uppercase `Minesweeper`
- The rewrite is intended to be runnable directly from the repo with `python -m minesweeper`
- The planning docs under `docs/plans/` are local working artifacts and may be git-ignored in this checkout
