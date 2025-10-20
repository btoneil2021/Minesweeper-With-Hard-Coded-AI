# UI Bar Design - Multi-Row Layout

**Date:** 2025-10-20
**Status:** Approved

## Overview

Redesign the UI to display game information (win rate, game mode) in a dedicated top bar above the game board, eliminating overlay issues and preparing for future UI additions.

## Requirements

- Win rate and game mode text should not overlay the game board
- Support for adding more UI elements in the future without restructuring
- Keep game board at full size (no shrinking)
- Clean visual separation between UI and game area

## Architecture

### Core Structure

- **New component:** `UIBar` class in `Minesweeper/game/ui_bar.py`
- **Updated component:** `RenderManager` class to integrate UIBar
- **Layout:** Fixed 3-row layout with uniform row heights
- **Positioning:** UIBar rendered at top (0, 0), game board below at (0, UI_BAR_HEIGHT)

### Component Responsibilities

**UIBar:**
- Owns the bar surface and row layout
- Manages rendering of UI elements to rows
- Self-contained rendering (initialized with dimensions and font)

**RenderManager:**
- Creates UIBar instance
- Populates row content via UIBar methods
- Blits UIBar surface and board to main screen at appropriate positions

**Screen size:**
- Expanded vertically to accommodate UI bar
- Game board maintains full original size

## UIBar Interface

```python
class UIBar:
    def __init__(self, width, font):
        """Creates 3-row layout with specified width."""
        # Each row initialized as empty/ready for content

    def set_row_content(self, row_index, text, alignment='left'):
        """Sets text for row 0, 1, or 2.

        Args:
            row_index: 0-2, raises ValueError if out of range
            text: String to display
            alignment: 'left', 'center', or 'right'
        """

    def render(self):
        """Returns pygame surface with all rows rendered."""
        # Background color for the bar
```

## Data Flow

1. `RenderManager.render()` receives win_rate, game_mode, ai_enabled (existing params)
2. RenderManager populates UIBar rows:
   - Row 0: Win rate text (e.g., "Win Rate: 45.23%")
   - Row 1: Mode text (e.g., "Mode: AI Only" or "Mode: Hybrid | AI: ON")
   - Row 2: Currently empty (reserved for future use)
3. RenderManager calls `UIBar.render()` to get the complete bar surface
4. RenderManager blits UIBar surface at position (0, 0)
5. RenderManager blits board at position (0, UI_BAR_HEIGHT)

### Screen Positioning Changes

**Before:**
- Board rendered at (0, 0)
- Text overlaid at (5, 5) and (5, 40)

**After:**
- UIBar at (0, 0)
- Board at (0, UI_BAR_HEIGHT)
- No overlay needed

## Implementation Details

### Visual Styling

- **UIBar background:** Light gray (200, 200, 200) to distinguish from board
- **Row dividers:** Optional thin horizontal lines between rows for visual separation
- **Text padding:** 5-10px left margin for left-aligned text
- **Text vertical centering:** Text centered vertically within each row's height
- **Text clipping:** Long text clipped naturally by pygame

### Error Handling

- `set_row_content()` validates row_index is 0-2, raises ValueError if out of range
- Empty rows render as blank space (no text, just background)

### Configuration Constants

**In config.py:**
```python
UI_ROW_HEIGHT = 30  # Height of each UI bar row
```

**In constants.py (derived):**
```python
UI_BAR_HEIGHT = UI_ROW_HEIGHT * 3  # Total UI bar height
UI_BAR_COLOR = (200, 200, 200)     # Background color for UI bar
```

**Screen size adjustment:**
```python
# Before:
SCREEN_SIZE = (TILE_SIZE * NUM_TILES_X, TILE_SIZE * NUM_TILES_Y)

# After:
SCREEN_SIZE = (TILE_SIZE * NUM_TILES_X, TILE_SIZE * NUM_TILES_Y + UI_BAR_HEIGHT)
```

With default config (40x40 tiles at 20px each):
- Old window: 800x800
- New window: 800x890 (800 + 90px for UI bar)

## Integration Changes

### RenderManager Modifications

1. Import UIBar class
2. Initialize UIBar in `__init__()` with screen width and font
3. Update `render()` method:
   - Call `set_row_content()` for win rate (row 0)
   - Call `set_row_content()` for game mode (row 1)
   - Call `ui_bar.render()` to get surface
   - Blit UIBar surface at (0, 0)
   - Call `board.draw()` with offset (0, UI_BAR_HEIGHT) instead of (0, 0)

### Board.draw() Considerations

- Check if Board.draw() currently assumes position (0, 0) or accepts offset parameter
- If needed, update Board.draw() signature to accept y_offset parameter
- Alternative: RenderManager creates a subsurface/viewport for the board area

## Future Extensibility

### Adding Content to Row 2
```python
# In RenderManager.render():
ui_bar.set_row_content(2, "New info here", alignment='center')
```

### Adding More Rows

To expand beyond 3 rows:
1. Update UIBar initialization to accept row count parameter
2. Or: Change hardcoded `3` to desired number in UIBar class
3. UI_BAR_HEIGHT will automatically scale (ROW_HEIGHT * num_rows)

### Adding Different Content Types

Current design supports text only. For future UI widgets (buttons, icons, etc.):
- Option 1: Extend UIBar with `set_row_widget()` method
- Option 2: Refactor to component-based system if complexity grows
- Keep YAGNI principle: Only add when actually needed

## Testing Considerations

### Visual Verification
- Confirm no overlay between UI bar and game board
- Verify text is readable with proper contrast
- Check text vertical centering in rows
- Confirm row 2 appears empty but allocated

### Backwards Compatibility
- Window size increases from 800x800 to 800x890
- Users may need to reposition their windows
- Functionality otherwise unchanged

### Edge Cases
- Very long text (e.g., lengthy mode descriptions) clips gracefully
- Invalid row indices raise clear errors
- Empty/None text handled without crashes

## Decision Log

| Decision | Rationale |
|----------|-----------|
| Top bar vs bottom bar | Top bar is more conventional for status information |
| Multi-row (3 rows) vs single row | Explicit control, no restructuring needed when adding elements |
| Uniform row height | Simpler, more visually consistent, predictable layout |
| Dedicated UIBar class vs extending RenderManager | Clean separation of concerns, easier to extend |
| Fixed 3 rows vs configurable | YAGNI - can make configurable later if needed |
