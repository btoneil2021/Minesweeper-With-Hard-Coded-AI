# Minesweeper Rewrite

A modern Minesweeper rewrite with a local Pygame game client, a built-in AI solver, and an additive external bot foundation for web-based boards.

The current rewrite lives under the lowercase `minesweeper/` package and separates the project into clear layers:

- `minesweeper/domain/` for shared types and protocols
- `minesweeper/engine/` for board state, rules, and stats
- `minesweeper/ai/` for analysis and solver strategies
- `minesweeper/ui/` for rendering and input translation
- `minesweeper/app.py` for top-level orchestration
- `minesweeper/external/` for screen capture, calibration, and external-board automation

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

For the external bot path, the runtime adapters are designed to use:

- `mss` for fast screen capture when available
- `Pillow` as the screenshot fallback
- `pyautogui` for live mouse control

Those external dependencies are only needed if you actually run `--mode external`.

Example setup:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install pygame pytest mypy
```

If you want to try the external bot mode too:

```bash
python -m pip install mss Pillow pyautogui
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

- `--mode {player,ai,hybrid,external}`
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

External mode:

```bash
python -m minesweeper --mode external
```

Classic intermediate-style board:

```bash
python -m minesweeper --mode player --width 16 --height 16 --mines 40
```

Large demo board:

```bash
python -m minesweeper --mode hybrid --width 40 --height 40 --mines 300 --tile-size 20 --font-size 26
```

## External Mode

`external` mode is the new additive bot foundation. Instead of owning the game state locally, it:

1. runs an interactive terminal calibration flow
2. captures a board region from the screen
3. performs one automatic first reveal during calibration
4. learns initial tile color profiles from before/after screenshots
5. classifies visible tiles into the existing domain model
6. feeds that snapshot into the existing analyzer and AI strategies
7. executes the chosen moves through mouse clicks

The current calibration flow asks you for:

- the top-left and bottom-right corners of the whole board
- the top-left and bottom-right corners of one tile
- the total mine count for the board

During calibration, the wizard now:

- captures the fully hidden board
- clicks the center tile once
- waits for the board to settle
- captures the board again
- derives initial hidden, revealed, and observed number colors from those screenshots

Important notes:

- external mode is intended for web or desktop Minesweeper boards outside the local Pygame client
- the implementation is test-first and additive, so the architecture is in place even though live desktop behavior will still benefit from manual tuning
- the launcher path for external mode lazy-loads the external automation modules, but the project still depends on `pygame` overall because the local game client ships in the same package
- calibration currently uses terminal prompts rather than a dedicated GUI wizard
- calibration now performs an automatic first reveal, so the target board should be in a fresh hidden state when you start
- if screen capture or mouse-control dependencies are missing, live external mode will fail at runtime with a clear error

## Controls

Player input:

- Left click: reveal
- Right click: flag or unflag

AI-enabled modes:

- `Space`: toggle AI on/off when the mode allows toggling
- `S`: run one AI step

External mode:

- follow the terminal calibration prompts before the solve loop begins
- move the target game window only when you intend to recalibrate
- use `pyautogui`'s built-in failsafe behavior to stop live automation if needed

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
├── external/
└── ui/

tests/
├── test_analyzer.py
├── test_app.py
├── test_board.py
├── test_constraint_subtractor.py
├── test_coord.py
├── test_domain_contracts.py
├── test_external_app.py
├── test_external_board_reader.py
├── test_external_calibration.py
├── test_external_capture.py
├── test_external_classifier.py
├── test_external_executor.py
├── test_external_imports.py
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
- The external bot implementation is intentionally additive and reuses the same analyzer and strategy chain as the local game
- The planning docs under `docs/plans/` are local working artifacts and may be git-ignored in this checkout
