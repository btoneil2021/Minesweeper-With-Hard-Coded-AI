# Minesweeper Probability System

This document explains how the probability calculation system works in the Minesweeper AI.

## Overview

The probability system uses **Constraint Satisfaction Problem (CSP)** solving to calculate the likelihood that each unknown tile contains a mine. This allows the AI to make educated guesses when no 100% safe moves are available through pattern detection.

## Core Concepts

### 1. Constraints

A **constraint** represents a rule that must be satisfied: "Exactly N of these tiles must contain mines."

**Example:**
```
┌───┬───┬───┐
│ ? │ ? │ ? │  A tile showing "3" with 3 unknown neighbors
├───┼───┼───┤  creates the constraint: "Exactly 3 of {(0,0), (0,1), (1,0)} are mines"
│ ? │ 3 │   │
├───┼───┼───┤
│ ? │   │   │
└───┴───┴───┘
```

Constraints are created from **numbered tiles** (tiles showing 1-8) by:
1. Finding all unknown neighbors
2. Subtracting already-flagged neighbors from the tile's number
3. The result is how many mines remain among the unknowns

### 2. Configuration Enumeration

A **configuration** is one possible arrangement of mines across all constrained tiles.

**Example:** For 3 tiles {A, B, C}, there are 2³ = 8 possible configurations:
- {} - no mines
- {A} - mine at A
- {B} - mine at B
- {C} - mine at C
- {A, B} - mines at A and B
- {A, C} - mines at A and C
- {B, C} - mines at B and C
- {A, B, C} - all mines

### 3. Configuration Validation

Not all configurations are valid - they must satisfy **all constraints simultaneously**.

**Example:**
```
┌───┬───┬───┐
│ A │ B │   │  Constraint 1: "1 mine in {A, B}" (from the "1" tile)
├───┼───┼───┤  Constraint 2: "1 mine in {A, C}" (from the "1" tile)
│ C │ 1 │ 1 │
└───┴───┴───┘

Valid configurations:    Invalid configurations:
- {A} ✓                  - {} ✗ (violates both constraints)
                         - {B} ✗ (violates constraint 2)
                         - {C} ✗ (violates constraint 1)
                         - {A, B} ✗ (violates constraint 1)
                         - {A, C} ✗ (violates constraint 2)
                         - {B, C} ✗ (violates both constraints)
                         - {A, B, C} ✗ (violates both constraints)

Only 1 valid configuration: {A}
Probabilities: A=100%, B=0%, C=0%
```

### 4. Probability Calculation

The probability that a tile contains a mine is:
```
P(tile has mine) = (# of valid configurations containing that tile) / (total # of valid configurations)
```

**Example:**
```
┌───┬───┬───┐
│ A │ B │   │  Constraint: "1 mine in {A, B}"
├───┼───┼───┤
│   │ 1 │   │  Valid configurations: {A}, {B}
└───┴───┴───┘  Total valid: 2

A appears in 1 valid configuration → P(A) = 1/2 = 50%
B appears in 1 valid configuration → P(B) = 1/2 = 50%
```

### 5. Global Probability (Fallback)

For tiles with no constraints (far from revealed tiles), we use **global probability**:
```
P(unconstrained tile) = (remaining mines) / (total unknown tiles)
```

If there are 10 mines left and 50 unknown tiles, each unconstrained tile has a 20% mine probability.

## System Architecture

### Classes

1. **Constraint** ([constraint.py](Minesweeper/ai/probability/constraint.py))
   - Stores tiles and required mine count
   - Validates if a configuration satisfies the constraint

2. **ConstraintCollector** ([constraint_collector.py](Minesweeper/ai/probability/constraint_collector.py))
   - Scans the board for numbered tiles
   - Creates constraints from each numbered tile's unknown neighbors

3. **ConfigurationValidator** ([configuration_validator.py](Minesweeper/ai/probability/configuration_validator.py))
   - Implements hybrid approach: exact enumeration + statistical sampling
   - Groups independent constraints to reduce problem size
   - Validates configurations against all constraints
   - Counts how often each tile appears as a mine in valid configurations

4. **ProbabilityCalculator** ([probability_calculator.py](Minesweeper/ai/probability/probability_calculator.py))
   - Orchestrates the probability calculation
   - Returns per-tile probabilities or single-tile probability
   - Falls back to global probability when no constraints exist

### Data Flow

```
BoardAnalyzer → ConstraintCollector → Constraints
                                          ↓
                                   ConfigurationValidator
                                          ↓
                                   (mine counts, valid configs)
                                          ↓
                                   ProbabilityCalculator
                                          ↓
                                   {tile: probability}
```

## Performance Characteristics

The system uses a **hybrid approach** combining exact enumeration with statistical sampling:

### Constraint Grouping
Constraints are automatically split into **independent groups** - sets of tiles that don't share any constraints with other groups. Each group is processed separately, dramatically improving performance.

**Example:**
```
Board has 40 constrained tiles total
→ Group A: 12 tiles (region 1)
→ Group B: 15 tiles (region 2)
→ Group C: 13 tiles (region 3)

Without grouping: 2^40 = 1 trillion configs ❌ (impossible)
With grouping: 2^12 + 2^15 + 2^13 = 45K configs ✓ (instant)
```

### Exact Enumeration (≤20 tiles per group)
- **Method:** Exhaustively checks all 2^n configurations
- **Time Complexity:** O(2^n × m) where n = tiles in group, m = constraints
- **Max Tiles:** 20 (2^20 = ~1 million configs, takes ~100ms)
- **Accuracy:** 100% exact probabilities
- **When Used:** Small/medium constraint groups (most cases)

### Statistical Sampling (>20 tiles per group)
- **Method:** Randomly samples 100,000 configurations instead of checking all
- **Time Complexity:** O(k × m) where k = sample size (100K), m = constraints
- **Max Tiles:** No limit (works for any size)
- **Accuracy:** ~99% accurate (probabilities typically within ±2%)
- **When Used:** Large constraint groups (rare, but scales to any board size)

### Performance Summary

| Constraint Group Size | Method | Configurations Checked | Time |
|----------------------|---------|----------------------|------|
| 10 tiles | Exact | 1,024 | <1ms |
| 15 tiles | Exact | 32,768 | ~10ms |
| 20 tiles | Exact | 1,048,576 | ~100ms |
| 25 tiles | **Sampling** | 100,000 samples | ~50ms |
| 50 tiles | **Sampling** | 100,000 samples | ~50ms |
| 100 tiles | **Sampling** | 100,000 samples | ~50ms |

**Key Insight:** The hybrid approach provides exact probabilities when possible and approximate probabilities when needed, ensuring the AI **never hangs** regardless of board size or constraint density.

## Usage

### Calculate All Probabilities
```python
probabilities = probability_calculator.calculate_probabilities()
# Returns: {(x, y): 0.35, (x2, y2): 0.67, ...}
```

### Calculate Single Tile Probability
```python
prob = probability_calculator.calculate_probabilities(target_tile=(5, 5))
# Returns: 0.42 (42% chance of mine)
```

### Find Best Move (Lowest Probability)
```python
best_tile, prob = probability_calculator.find_lowest_probability_tile()
# Returns: ((3, 4), 0.15) - tile (3,4) has 15% mine probability
```

### Find Best Flag (Highest Probability)
```python
flag_tile, prob = probability_calculator.find_highest_probability_tile()
# Returns: ((7, 2), 0.95) - tile (7,2) has 95% mine probability
```

## Integration with AI Strategy

The probability system integrates into [ai_strategy.py](Minesweeper/ai/ai_strategy.py) as a **fallback** when pattern detection finds no certain moves:

1. Try pattern detection (100% certain moves)
2. If no certain moves → use probability calculator
3. Flag tiles with very high mine probability (≥90%)
4. Click tile with lowest mine probability

This allows the AI to continue making intelligent moves even when the board state is ambiguous.

## Scalability

The hybrid system is designed to scale to **any board size** configured by the user:

- **Small boards (10x10):** Uses exact enumeration, instant results
- **Medium boards (20x20):** Uses exact for most groups, very fast
- **Large boards (40x40, 100x100):** Automatically switches to sampling for dense regions
- **Extreme boards (200x200+):** Still works, with approximate probabilities for complex areas

The constraint grouping algorithm ensures that even on massive boards, most regions are solved exactly because they form independent groups small enough for enumeration.
