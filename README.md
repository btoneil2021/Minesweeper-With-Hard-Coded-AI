# Minesweeper with AI Solver

A Python implementation of Minesweeper featuring an advanced AI that uses logical deduction and probability analysis to solve boards autonomously.

## Features

### Game Engine
- Classic Minesweeper gameplay with configurable board dimensions (default: 40×40 grid with 300 mines)
- Interactive GUI built with Pygame
- Automatic game restart with performance tracking
- Win rate statistics

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
├── constants.py                # Game configuration and constants
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

The AI will automatically play the game. You can also manually interact with the board using:
- **Left Click**: Reveal a tile
- **Right Click**: Flag/unflag a tile

## Configuration

Modify game settings in [constants.py](Minesweeper/constants.py):

```python
NUM_BOMBS = 300        # Number of mines
NUM_TILES_X = 40       # Board width
NUM_TILES_Y = 40       # Board height
TILE_SIZE = 20         # Pixel size of each tile
AI_CLICK_FEEDBACK = False  # Visual feedback for AI moves
```

## How the AI Works

The AI uses a hierarchical decision-making process:

1. **Initial Random Move**: Makes a random first move to reveal the initial board state
2. **Deterministic Logic**: Applies pattern detection to find guaranteed safe tiles and mines
3. **Transitive Reasoning**: Uses relationships between adjacent tiles for complex deductions
4. **Probability Analysis (IN PROGRESS)**: When logic is insufficient, calculates mine probabilities using constraint satisfaction
5. **Move Execution**: Takes the safest action available

The AI only tracks statistics for games where it made it out of the first random guessing phase, ensuring meaningful win rate metrics.

## License

This project is open source and available for educational purposes.
