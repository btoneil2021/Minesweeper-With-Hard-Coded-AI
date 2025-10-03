"""
User-configurable game settings.
Modify these values to customize your game experience.
"""

# Board configuration
NUM_BOMBS = 300        # Number of mines on the board
NUM_TILES_X = 40       # Board width (number of tiles)
NUM_TILES_Y = 40       # Board height (number of tiles)

# Display settings
TILE_SIZE = 20         # Size of each tile in pixels
FONT_SIZE = 30         # Font size for UI text

# Game modes
# MODE_AI_ONLY = 0      : AI plays automatically
# MODE_PLAYER_ONLY = 1  : Only manual player controls
# MODE_HYBRID = 2       : Player controls with AI assistance (use SPACE to toggle AI, S for single step)
GAME_MODE = 0          # Default game mode

# Game timing
GAME_RESTART_DELAY = 1000  # Delay in milliseconds before restarting after win/loss

# AI configuration
AI_CLICK_FEEDBACK = False  # Show visual mouse cursor feedback for AI moves
