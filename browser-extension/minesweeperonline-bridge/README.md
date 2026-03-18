# Minesweeper Online Bridge

This folder contains the first-pass Chrome-compatible extension skeleton for `minesweeperonline.com`.

What it does now:
- scans the live page for tile ids like `row_col`
- parses tile classes such as `square openX`, `square bombflagged`, `square bombdeath`, and `square bombrevealed`
- exposes a background worker that can broker extension-side messages

What it does not do yet:
- it is not connected to the Python bridge transport
- it does not yet stream snapshots into the solver loop automatically

## Load It

1. Open your Chromium-based browser, including Comet.
2. Visit the extensions page, usually `chrome://extensions`.
3. Enable developer mode.
4. Choose `Load unpacked`.
5. Select the `browser-extension/minesweeperonline-bridge` folder from this repository.

## Use It

1. Open `https://minesweeperonline.com`.
2. Start a game.
3. The content script will be present on the page and ready to scan the board DOM.

## Notes

- The extension is intentionally minimal for now.
- The Python side already has matching DOM protocol and parser code under `minesweeper/external/browser/`.
- The next integration step is wiring this extension to the local Python bridge process.
