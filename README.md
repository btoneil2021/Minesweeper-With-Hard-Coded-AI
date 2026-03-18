# Minesweeper Rewrite

A modern Minesweeper rewrite with a local Pygame game client, a built-in AI solver, and an additive external bot foundation for web-based boards.

The current rewrite lives under the lowercase `minesweeper/` package and separates the project into clear layers:

- `minesweeper/domain/` for shared types and protocols
- `minesweeper/engine/` for board state, rules, and stats
- `minesweeper/ai/` for analysis and solver strategies
- `minesweeper/ui/` for rendering and input translation
- `minesweeper/app.py` for top-level orchestration
- `minesweeper/external/` for screen capture, calibration, and external-board automation
- `minesweeper/external/browser/` for the `minesweeperonline.com` DOM bridge path

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
- `pynput` for guarded live calibration point capture

Those external dependencies are only needed if you actually run `--mode external`.

Example setup:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install pygame pytest mypy
```

If you want to try the external bot mode too:

```bash
python -m pip install mss Pillow pyautogui pynput
```

If you want to try the browser DOM path too, use a Chromium-based browser such as Comet. The repo includes a minimal extension skeleton for `minesweeperonline.com`, but the real live bridge is still a work in progress.

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

- `--mode {player,ai,hybrid,external,browser-dom}`
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

Browser DOM mode:

```bash
python -m minesweeper --mode browser-dom
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

Use `--verbose` with external mode if you want runtime progress and explicit stop reasons printed to the terminal.

For temporary live debugging of the capture layer, you can also use:

```bash
python -m minesweeper --mode external --debug-captures debug-captures
```

That writes:

- `debug-captures/calibration/board_before_open.png`
- `debug-captures/calibration/board_after_open.png`
- `debug-captures/runtime/refresh_000.png`, `refresh_001.png`, ...
- `debug-captures/runtime/move_000.png`, `move_001.png`, ...

Use that flag only when you want to inspect what raw board region the external runtime actually captured during calibration and refresh.
The `move_*.png` overlays mark the chosen tile bounds and the exact click pixel for each executed move.

## Browser DOM Mode

`browser-dom` is the new `minesweeperonline.com`-specific path. It uses the page DOM instead of screenshots, which is a much better fit for the site than the screen-scraping fallback.

What is available now:

1. A Python-side DOM protocol, reader, executor, bridge, and app loop under `minesweeper/external/browser/`
2. A minimal MV3 extension skeleton under `browser-extension/minesweeperonline-bridge/`
3. Launcher support for `python -m minesweeper --mode browser-dom`

What is not available yet:

1. A real extension-to-Python bridge connection
2. Automatic live board streaming from the browser into the solver loop

To load the extension skeleton:

1. Open Comet or another Chromium-based browser.
2. Visit `chrome://extensions`.
3. Enable developer mode.
4. Choose `Load unpacked`.
5. Select `browser-extension/minesweeperonline-bridge/` from this repository.

Troubleshooting:

1. If `browser-dom` exits with `browser-dom mode requires a connected extension session`, the extension has not yet produced a board snapshot.
2. If the mode appears idle, make sure `https://minesweeperonline.com` is open and an actual game has been started.
3. `--debug-captures` only applies to screenshot-based `external` mode, not `browser-dom`.

The current calibration flow gathers:

- the top-left and bottom-right corners of the whole board
- the total mine count for the board

During calibration, the wizard now:

- asks you to hold `Shift` and left-click each requested board corner
- falls back to manual `(x,y)` entry if guarded live capture is unavailable, cancelled, or times out
- captures a rough hidden-board screenshot from the clicked board region
- detects the board's actual row and column boundaries from that hidden screenshot
- realigns the runtime board region to the detected tile grid instead of trusting the clicked corners exactly
- derives a compatibility tile size from the detected grid instead of asking for a separate sample tile
- may warn when the rough board bounds look slightly off relative to the detected grid
- clicks the center tile once
- waits for the board to settle
- captures the board again
- derives initial hidden, revealed, and observed number colors from those screenshots
- reuses the same detected tile grid for both screen cropping and click targeting during the solve loop

Important notes:

- external mode is intended for web or desktop Minesweeper boards outside the local Pygame client
- the implementation is test-first and additive, so the architecture is in place even though live desktop behavior will still benefit from manual tuning
- the launcher path for external mode now delegates to the public `minesweeper.external.run(...)` facade, while the project still depends on `pygame` overall because the local game client ships in the same package
- calibration still runs from terminal prompts rather than a dedicated GUI wizard, but point selection now prefers guarded live clicks
- the clicked board corners are treated as coarse calibration hints; the hidden-board scan is the source of truth for runtime tile boundaries
- clearly incorrect calibration bounds still fail and should be recalibrated
- calibration now performs an automatic first reveal, so the target board should be in a fresh hidden state when you start
- runtime clicks now target the detected tile rectangles with a small inset instead of naive uniform-tile midpoints
- external runtime preserves solver move order and prefers retry-then-stop over silently guessing when board reads fail
- if screen capture or mouse-control dependencies are missing, live external mode will fail at runtime with a clear error
- external runtime progress and stop reasons stay quiet unless you pass `--verbose`

## Controls

Player input:

- Left click: reveal
- Right click: flag or unflag

AI-enabled modes:

- `Space`: toggle AI on/off when the mode allows toggling
- `S`: run one AI step

External mode:

- follow the terminal calibration prompts before the solve loop begins
- hold `Shift` while left-clicking the requested calibration corners
- move the target game window only when you intend to recalibrate
- use `pyautogui`'s built-in failsafe behavior to stop live automation if needed

Browser DOM mode:

- open a live `minesweeperonline.com` game tab before launching
- load the browser extension skeleton first
- expect the current `browser-dom` path to require the future live bridge wiring before it can actually play a game

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
