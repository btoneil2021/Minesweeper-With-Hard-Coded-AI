# Minesweeper with AI Solver

A Python implementation of Minesweeper featuring an advanced AI that uses logical deduction and probability analysis to solve boards autonomously.

## Features

### Game Modes
The game supports three different play modes:

1. **AI Only Mode** - Watch the AI play automatically using advanced solving techniques
2. **Player Only Mode** - Classic manual Minesweeper gameplay
3. **Hybrid Mode** - Play manually with AI assistance available at the press of a button

### Game Engine
- Classic Minesweeper gameplay with configurable board dimensions (default: 40×40 grid with 300 mines)
- Interactive GUI built with Pygame
- Automatic game restart with performance tracking
- Win rate statistics
- On-screen mode and AI status display

### AI Solver
The AI employs multiple sophisticated strategies to solve Minesweeper boards:

1. **Pattern Detection** ([pattern_detector.py](Minesweeper/ai/pattern_detector.py))
   - Identifies obvious mines (when unrevealed tiles equal the tile number)
   - Detects safe tiles (when all mines around a tile are flagged)

2. **Transitive Pattern Matching** ([transitive_pattern_matcher.py](Minesweeper/ai/transitive_pattern_matcher.py))
   - Advanced logical deduction using relationships between adjacent tiles
   - Analyzes directional patterns to identify safe tiles and mines
   - Handles complex scenarios like shared constraints between tiles

3. **Constraint Satisfaction Probability (NOT FINISHED)** ([probability_calculator.py](Minesweeper/ai/probability/probability_calculator.py))
   - Calculates mine probabilities using constraint satisfaction
   - Enumerates valid configurations to determine optimal moves
   - Falls back to global probability when local constraints are insufficient

## Project Structure

```
Minesweeper/
├── game_runner.py              # Main game loop orchestration
├── config.py                   # User-configurable settings
├── constants.py                # Internal constants
├── game/
│   ├── board.py               # Board state and tile management
│   ├── game_logic.py          # Game rules and interactions
│   ├── tile.py                # Tile representation
│   ├── render_manager.py     # Display rendering
│   ├── statistics_tracker.py # Win rate tracking
│   └── neighbor_utils.py     # Neighbor calculation utilities
└── ai/
    ├── ai_strategy.py         # High-level AI decision engine
    ├── ai_controller.py       # AI move execution
    ├── board_analyzer.py      # Board state analysis
    ├── pattern_detector.py    # Pattern recognition
    ├── transitive_pattern_matcher.py  # Advanced pattern logic
    └── probability/
        ├── probability_calculator.py  # Probability computation
        ├── constraint_collector.py    # Constraint gathering
        ├── constraint.py              # Constraint representation
        └── configuration_emulator.py  # Configuration enumeration
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Minesweeper-With-Hard-Coded-AI.git
cd Minesweeper-With-Hard-Coded-AI
```

2. Install dependencies:
```bash
pip install pygame
```

## Usage

Run the game:
```bash
python Minesweeper/game_runner.py
```

You'll be prompted to select a game mode:
- **0** - AI Only Mode: AI plays automatically
- **1** - Player Only Mode: Manual play only
- **2** - Hybrid Mode: Manual play with AI assistance

Press Enter to use the default mode configured in [config.py](Minesweeper/config.py).

### Controls

**Player Only Mode:**
- **Left Click**: Reveal a tile
- **Right Click**: Flag/unflag a tile

**Hybrid Mode:**
- **Left Click**: Reveal a tile
- **Right Click**: Flag/unflag a tile
- **SPACE**: Toggle AI automation on/off
- **S**: Execute a single AI step

**AI Only Mode:**
- No controls needed - watch the AI solve!

## Configuration

Modify game settings in [config.py](Minesweeper/config.py):

```python
# Board configuration
NUM_BOMBS = 300        # Number of mines on the board
NUM_TILES_X = 40       # Board width (number of tiles)
NUM_TILES_Y = 40       # Board height (number of tiles)

# Display settings
TILE_SIZE = 20         # Size of each tile in pixels
FONT_SIZE = 30         # Font size for UI text

# Game mode (0 = AI Only, 1 = Player Only, 2 = Hybrid)
GAME_MODE = 0          # Default game mode

# Game timing
GAME_RESTART_DELAY = 1000  # Delay in milliseconds before restarting

# AI configuration
AI_CLICK_FEEDBACK = False  # Show visual mouse cursor for AI moves
```

## How the AI Works

The AI uses a hierarchical decision-making process:

1. **Initial Random Move**: Makes a random first move to reveal the initial board state
2. **Deterministic Logic**: Applies pattern detection to find guaranteed safe tiles and mines
3. **Transitive Reasoning**: Uses relationships between adjacent tiles for complex deductions
4. **Probability Analysis (IN PROGRESS)**: When logic is insufficient, calculates mine probabilities using constraint satisfaction
5. **Move Execution**: Takes the safest action available

The AI only tracks statistics for games where it made it out of the first random guessing phase, ensuring meaningful win rate metrics.

## Game Modes in Detail

### AI Only Mode
Perfect for:
- Watching the AI solve complex board configurations
- Analyzing AI performance and win rates
- Understanding advanced Minesweeper solving techniques

### Player Only Mode
Perfect for:
- Traditional Minesweeper gameplay
- Practicing your own solving skills
- Competing against the AI's win rate

### Hybrid Mode
Perfect for:
- Learning from the AI while playing
- Getting help when stuck on difficult patterns
- Training yourself to recognize patterns the AI uses
- Using the AI as a "hint" system (single step with 'S' key)

## License

This project is open source and available for educational purposes.
