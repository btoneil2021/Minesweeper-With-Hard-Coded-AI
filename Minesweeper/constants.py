import os

# Game configuration
NUM_BOMBS = 300
NUM_TILES_X = 40
NUM_TILES_Y = 40
TILE_SIZE = 20
FONT_SIZE = 30
SCREEN_SIZE = (TILE_SIZE * NUM_TILES_X, TILE_SIZE * NUM_TILES_Y)

# AI states
AI_CLICK_FEEDBACK = False

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

# Game timing
GAME_RESTART_DELAY = 1000  # milliseconds

# AI configuration
AI_RANDOM_MOVE_PROBABILITY = 27
AI_RANDOM_MOVE_RANGE = NUM_TILES_X * 1000
