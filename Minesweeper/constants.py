import os
from config import *

# Derived configuration (calculated from config.py)
SCREEN_SIZE = (TILE_SIZE * NUM_TILES_X, TILE_SIZE * NUM_TILES_Y + UI_ROW_HEIGHT * 3)

# Game mode constants
MODE_AI_ONLY = 0
MODE_PLAYER_ONLY = 1
MODE_HYBRID = 2

# Tile states
STATE_HIDDEN = 0
STATE_REVEALED = 1
STATE_FLAGGED = 2
STATE_BOMB = 3

# AI tile values
AI_FLAGGED = -1
AI_UNKNOWN = -2

# Colors
COLOR_BACKGROUND = (222, 184, 135)
COLOR_TILE_HIDDEN = (184, 134, 77)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)

# UI Bar
UI_BAR_HEIGHT = UI_ROW_HEIGHT * 3  # Total UI bar height (3 rows)
UI_BAR_COLOR = (200, 200, 200)     # Light gray background

# Number colors for Minesweeper tiles
NUMBER_COLORS = {
    1: (2, 32, 184),
    2: (1, 133, 21),
    3: (242, 0, 0),
    4: (30, 3, 140),
    5: (99, 55, 0),
    6: (0, 181, 151),
    7: (0, 0, 0),
    8: (97, 97, 97)
}

# Resource paths
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCE_FLAG = os.path.join(_BASE_DIR, "resources", "flag.png")
RESOURCE_BOMB = os.path.join(_BASE_DIR, "resources", "bomb.png")

