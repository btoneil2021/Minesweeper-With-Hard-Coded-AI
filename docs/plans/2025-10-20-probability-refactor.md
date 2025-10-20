# Probability System Refactoring Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor probability calculation system into three clear layers with single responsibilities for improved maintainability and traceability.

**Architecture:** Three-layer architecture: (1) Constraint Layer extracts and groups constraints, (2) Configuration Layer generates valid mine configurations using strategies, (3) Probability Layer calculates weighted probabilities. Each layer has focused components with single responsibilities.

**Tech Stack:** Python 3, pygame (existing), no new dependencies

---

## Phase 1: Create New Components

### Task 1: Create math_utilities.py with log-space functions

**Files:**
- Create: `Minesweeper/ai/probability/math_utilities.py`

**Step 1: Create math_utilities.py with log_combinations**

Create file `Minesweeper/ai/probability/math_utilities.py`:

```python
import math


def log_combinations(n, k):
    """
    Calculate log of binomial coefficient: log(C(n, k))

    This avoids overflow for large numbers by working in log-space.

    Args:
        n: Total items
        k: Items to choose

    Returns:
        float: log(C(n, k)), or -inf if k > n or k < 0
    """
    if k > n or k < 0:
        return float('-inf')
    if k == 0 or k == n:
        return 0.0

    # log(C(n,k)) = log(n!) - log(k!) - log((n-k)!)
    # Use math.lgamma: lgamma(n+1) = log(n!)
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def logsumexp(log_values):
    """
    Safely compute log(sum(exp(log_values))) avoiding overflow.

    Uses the logsumexp trick: log(sum(exp(x_i))) = max(x) + log(sum(exp(x_i - max(x))))

    Args:
        log_values: List of log-space values

    Returns:
        float: log(sum(exp(log_values)))
    """
    if not log_values:
        return float('-inf')

    max_log = max(log_values)
    if max_log == float('-inf'):
        return float('-inf')

    return max_log + math.log(sum(math.exp(lv - max_log) for lv in log_values))


def weighted_average_in_log_space(log_weights, values):
    """
    Calculate weighted average: sum(weight * value) / sum(weight)

    Works in log-space to avoid overflow with large weights.

    Args:
        log_weights: List of log(weight) values
        values: List of corresponding values (in normal space)

    Returns:
        float: Weighted average in normal space
    """
    if not log_weights or not values or len(log_weights) != len(values):
        return 0.0

    max_log_weight = max(log_weights)

    # Calculate sum(weight * value) in normal space after adjusting weights
    numerator = sum(math.exp(log_weights[i] - max_log_weight) * values[i]
                   for i in range(len(log_weights)))

    # Calculate sum(weight)
    denominator = sum(math.exp(lw - max_log_weight) for lw in log_weights)

    if denominator == 0:
        return 0.0

    return numerator / denominator
```

**Step 2: Commit math utilities**

```bash
git add Minesweeper/ai/probability/math_utilities.py
git commit -m "Add math_utilities with log-space arithmetic functions"
```

---

### Task 2: Create constraint_grouper.py

**Files:**
- Create: `Minesweeper/ai/probability/constraint_grouper.py`

**Step 1: Create constraint_grouper.py**

Create file `Minesweeper/ai/probability/constraint_grouper.py`:

```python
class ConstraintGrouper:
    """
    Groups constraints into independent sets that don't share tiles.

    Constraints that share tiles must be solved together. Independent groups
    can be solved separately and their results multiplied together.
    """

    @staticmethod
    def group_constraints(constraints):
        """
        Split constraints into independent groups using Union-Find approach.

        Args:
            constraints: List of Constraint objects

        Returns:
            List of tuples: [(group_constraints, group_tiles), ...]
            where group_constraints is a list of Constraint objects and
            group_tiles is a set of all tiles in that group
        """
        if not constraints:
            return []

        # Build list of constraint tiles for quick lookup
        constraint_tiles = [set(c.get_constrained_tiles()) for c in constraints]

        # Track which constraints have been assigned to groups
        used = [False] * len(constraints)
        groups = []

        for i in range(len(constraints)):
            if used[i]:
                continue

            # Start a new group with constraint i
            group_constraints = [constraints[i]]
            group_tiles = set(constraint_tiles[i])
            used[i] = True

            # Find all constraints that share tiles with this group
            changed = True
            while changed:
                changed = False
                for j in range(len(constraints)):
                    if used[j]:
                        continue

                    # Check if constraint j shares tiles with current group
                    if group_tiles & constraint_tiles[j]:
                        group_constraints.append(constraints[j])
                        group_tiles.update(constraint_tiles[j])
                        used[j] = True
                        changed = True

            groups.append((group_constraints, group_tiles))

        return groups
```

**Step 2: Commit constraint grouper**

```bash
git add Minesweeper/ai/probability/constraint_grouper.py
git commit -m "Add constraint_grouper to partition independent constraint groups"
```

---

### Task 3: Create exact_enumeration_strategy.py

**Files:**
- Create: `Minesweeper/ai/probability/exact_enumeration_strategy.py`

**Step 1: Create exact_enumeration_strategy.py**

Create file `Minesweeper/ai/probability/exact_enumeration_strategy.py`:

```python
class ExactEnumerationStrategy:
    """
    Strategy for small constraint groups: enumerate all 2^n configurations.

    Use when number of tiles <= 20 (2^20 = ~1M configurations is manageable).
    """

    @staticmethod
    def generate_configurations(constraints, tiles):
        """
        Generate all valid mine configurations by exhaustive enumeration.

        Args:
            constraints: List of Constraint objects
            tiles: Set of tile coordinates affected by these constraints

        Returns:
            List of dicts: [{'config': set of mine tiles, 'mine_count': int}, ...]
        """
        tiles_list = list(tiles)
        n = len(tiles_list)
        valid_configs = []

        # Enumerate all 2^n possible configurations
        for i in range(2 ** n):
            # Convert bit pattern to mine configuration
            config = {tiles_list[j] for j in range(n) if (i >> j) & 1}

            # Check if this configuration satisfies all constraints
            if ExactEnumerationStrategy._is_valid(config, constraints):
                valid_configs.append({
                    'config': config,
                    'mine_count': len(config)
                })

        return valid_configs

    @staticmethod
    def _is_valid(config, constraints):
        """Check if configuration satisfies all constraints"""
        return all(constraint.is_satisfied_by(config) for constraint in constraints)
```

**Step 2: Commit exact enumeration strategy**

```bash
git add Minesweeper/ai/probability/exact_enumeration_strategy.py
git commit -m "Add exact_enumeration_strategy for small constraint groups"
```

---

### Task 4: Create sampling_strategy.py

**Files:**
- Create: `Minesweeper/ai/probability/sampling_strategy.py`

**Step 1: Create sampling_strategy.py**

Create file `Minesweeper/ai/probability/sampling_strategy.py`:

```python
import random


class SamplingStrategy:
    """
    Strategy for large constraint groups: random sampling.

    Use when number of tiles > 20 (exhaustive enumeration becomes too slow).
    """

    # Number of random configurations to sample
    SAMPLE_SIZE = 100000

    @staticmethod
    def generate_configurations(constraints, tiles):
        """
        Generate valid mine configurations by random sampling.

        Args:
            constraints: List of Constraint objects
            tiles: Set of tile coordinates affected by these constraints

        Returns:
            List of dicts: [{'config': set of mine tiles, 'mine_count': int}, ...]
        """
        tiles_list = list(tiles)
        valid_configs = []

        # Sample random configurations
        for _ in range(SamplingStrategy.SAMPLE_SIZE):
            # Generate random configuration (each tile has 50% chance of being a mine)
            config = {tile for tile in tiles_list if random.random() < 0.5}

            # Check if valid
            if SamplingStrategy._is_valid(config, constraints):
                valid_configs.append({
                    'config': config,
                    'mine_count': len(config)
                })

        return valid_configs

    @staticmethod
    def _is_valid(config, constraints):
        """Check if configuration satisfies all constraints"""
        return all(constraint.is_satisfied_by(config) for constraint in constraints)
```

**Step 2: Commit sampling strategy**

```bash
git add Minesweeper/ai/probability/sampling_strategy.py
git commit -m "Add sampling_strategy for large constraint groups"
```

---

### Task 5: Create configuration_generator.py

**Files:**
- Create: `Minesweeper/ai/probability/configuration_generator.py`

**Step 1: Create configuration_generator.py**

Create file `Minesweeper/ai/probability/configuration_generator.py`:

```python
from .exact_enumeration_strategy import ExactEnumerationStrategy
from .sampling_strategy import SamplingStrategy


class ConfigurationGenerator:
    """
    Generates valid mine configurations that satisfy constraints.

    Automatically chooses strategy based on problem size:
    - Small groups (<=20 tiles): Exact enumeration
    - Large groups (>20 tiles): Random sampling
    """

    # Threshold for switching from exact to sampling
    MAX_TILES_FOR_EXACT = 20

    @staticmethod
    def generate_valid_configurations(constraints, tiles):
        """
        Generate all valid mine configurations for given constraints.

        Args:
            constraints: List of Constraint objects
            tiles: Set of tile coordinates affected by these constraints

        Returns:
            List of dicts: [{'config': set of mine tiles, 'mine_count': int}, ...]
        """
        if not constraints or not tiles:
            return []

        # Choose strategy based on problem size
        if len(tiles) <= ConfigurationGenerator.MAX_TILES_FOR_EXACT:
            return ExactEnumerationStrategy.generate_configurations(constraints, tiles)
        else:
            return SamplingStrategy.generate_configurations(constraints, tiles)
```

**Step 2: Commit configuration generator**

```bash
git add Minesweeper/ai/probability/configuration_generator.py
git commit -m "Add configuration_generator with automatic strategy selection"
```

---

## Phase 2: Refactor ProbabilityCalculator

### Task 6: Update ProbabilityCalculator to use new components

**Files:**
- Modify: `Minesweeper/ai/probability/probability_calculator.py` (replace entire file)

**Step 1: Read old implementation for reference**

Read `Minesweeper/ai/probability/probability_calculator.py` to understand current public API.

Key methods to preserve:
- `calculate_probabilities(target_tile=None)` - main public method
- `find_lowest_probability_tile()` - used by AI
- `find_highest_probability_tile(threshold=0.9)` - used by AI
- `format_probabilities(max_results=20)` - debugging
- `get_tile_constraints(tile)` - debugging

**Step 2: Rewrite ProbabilityCalculator to use new components**

Replace entire contents of `Minesweeper/ai/probability/probability_calculator.py`:

```python
from constants import *
from .constraint_collector import ConstraintCollector
from .constraint_grouper import ConstraintGrouper
from .configuration_generator import ConfigurationGenerator
from .math_utilities import log_combinations, logsumexp, weighted_average_in_log_space
import math
import random


class ProbabilityCalculator:
    """
    Orchestrates probability calculation using three-layer architecture.

    Layer 1: Constraint extraction and grouping
    Layer 2: Configuration generation
    Layer 3: Probability calculation with log-space weighting
    """

    def __init__(self, board_analyzer):
        self.analyzer = board_analyzer
        self.constraint_collector = ConstraintCollector(board_analyzer)

    def calculate_probabilities(self, target_tile=None):
        """
        Calculate mine probabilities for tiles.

        Args:
            target_tile: Optional specific tile coordinate. If provided, returns float.
                        If None, returns dict of all probabilities.

        Returns:
            If target_tile provided: float probability (0.0 to 1.0)
            If target_tile is None: dict mapping {(x, y): probability} for ALL unknown tiles
        """
        # Layer 1: Extract and group constraints
        constraints = self.constraint_collector.collect_all_constraints()

        # No constraints: use global probability
        if not constraints:
            return self._calculate_global_probability(target_tile)

        # Layer 2 & 3: Generate configurations and calculate probabilities
        constrained_probs = self._calculate_constrained_probabilities(constraints)

        # Fallback to global if calculation failed
        if not constrained_probs:
            return self._calculate_global_probability(target_tile)

        # If requesting specific tile
        if target_tile:
            if target_tile in constrained_probs:
                return constrained_probs[target_tile]
            else:
                # Unconstrained tile: use global probability
                return self._calculate_global_probability(target_tile)

        # Return all tiles: merge constrained + unconstrained
        all_probabilities = dict(constrained_probs)

        # Calculate weighted probability for unconstrained tiles
        unconstrained_prob = self._calculate_unconstrained_probability(constraints, constrained_probs)

        # Add unconstrained tiles
        for coord in self.analyzer.get_all_coordinates():
            if (self.analyzer.get_tile_state(coord) == AI_UNKNOWN and
                coord not in all_probabilities):
                all_probabilities[coord] = unconstrained_prob

        return all_probabilities

    def _calculate_constrained_probabilities(self, constraints):
        """
        Calculate probabilities using constraint satisfaction with global weighting.

        Uses the three-layer architecture:
        1. Group constraints (Layer 1)
        2. Generate valid configurations (Layer 2)
        3. Weight and calculate probabilities (Layer 3)

        Returns:
            dict: {(x, y): probability} for all constrained tiles
        """
        # Layer 1: Group constraints
        groups = ConstraintGrouper.group_constraints(constraints)

        if not groups:
            return {}

        # For simplicity, merge all groups into one for now
        # (Independent groups could be optimized separately)
        all_constrained_tiles = set()
        for _, tiles in groups:
            all_constrained_tiles.update(tiles)

        # Layer 2: Generate valid configurations
        valid_configs = ConfigurationGenerator.generate_valid_configurations(
            constraints, all_constrained_tiles
        )

        if not valid_configs:
            return {}

        # Layer 3: Calculate probabilities with global weighting
        return self._weight_and_calculate_probabilities(
            valid_configs, all_constrained_tiles
        )

    def _weight_and_calculate_probabilities(self, valid_configs, constrained_tiles):
        """
        Weight configurations by unconstrained possibilities and calculate probabilities.

        Uses log-space arithmetic from math_utilities to avoid overflow.
        """
        # Get global mine budget
        total_unknown = sum(1 for state in self.analyzer.get_all_values()
                          if state == AI_UNKNOWN)
        total_flagged = sum(1 for state in self.analyzer.get_all_values()
                          if state == AI_FLAGGED)
        remaining_mines = NUM_BOMBS - total_flagged
        unconstrained_count = total_unknown - len(constrained_tiles)

        # Calculate log-weights for each configuration
        log_weights = []
        config_data = []

        for config_info in valid_configs:
            mines_in_config = config_info['mine_count']
            mines_for_unconstrained = remaining_mines - mines_in_config

            # Weight = C(unconstrained_count, mines_for_unconstrained)
            log_weight = log_combinations(unconstrained_count, mines_for_unconstrained)

            if log_weight != float('-inf'):
                log_weights.append(log_weight)
                config_data.append(config_info)

        if not log_weights:
            return {}

        # Calculate total weight using logsumexp
        total_weight_log = logsumexp(log_weights)

        # Calculate weighted mine counts for each tile
        tile_log_weights = {tile: [] for tile in constrained_tiles}

        for i, config_info in enumerate(config_data):
            log_weight = log_weights[i]
            for tile in config_info['config']:
                if tile in tile_log_weights:
                    tile_log_weights[tile].append(log_weight)

        # Convert to probabilities
        probabilities = {}
        for tile in constrained_tiles:
            if tile_log_weights[tile]:
                # Sum of weights where tile is mine
                mine_weight_log = logsumexp(tile_log_weights[tile])
                # Probability = mine_weight / total_weight
                probabilities[tile] = math.exp(mine_weight_log - total_weight_log)
            else:
                probabilities[tile] = 0.0

        return probabilities

    def _calculate_unconstrained_probability(self, constraints, constrained_probs):
        """
        Calculate weighted probability for unconstrained tiles.

        Args:
            constraints: List of constraints
            constrained_probs: Dict of probabilities for constrained tiles

        Returns:
            float: Weighted probability for an unconstrained tile
        """
        # Get all constrained tiles
        constrained_tiles = set()
        for constraint in constraints:
            constrained_tiles.update(constraint.get_constrained_tiles())

        # Generate configurations
        valid_configs = ConfigurationGenerator.generate_valid_configurations(
            constraints, constrained_tiles
        )

        if not valid_configs:
            return self._calculate_global_probability_value()

        # Get global counts
        total_unknown = sum(1 for state in self.analyzer.get_all_values()
                          if state == AI_UNKNOWN)
        total_flagged = sum(1 for state in self.analyzer.get_all_values()
                          if state == AI_FLAGGED)
        remaining_mines = NUM_BOMBS - total_flagged
        unconstrained_count = total_unknown - len(constrained_tiles)

        if unconstrained_count == 0:
            return 0.0

        # Calculate weighted average probability
        log_weights = []
        probs = []

        for config_info in valid_configs:
            mines_in_config = config_info['mine_count']
            mines_for_unconstrained = remaining_mines - mines_in_config

            log_weight = log_combinations(unconstrained_count, mines_for_unconstrained)

            if log_weight != float('-inf'):
                prob = mines_for_unconstrained / unconstrained_count
                log_weights.append(log_weight)
                probs.append(prob)

        if not log_weights:
            return self._calculate_global_probability_value()

        return weighted_average_in_log_space(log_weights, probs)

    def _calculate_global_probability_value(self):
        """Calculate simple global probability as a float value."""
        total_unknown = sum(1 for state in self.analyzer.get_all_values()
                          if state == AI_UNKNOWN)
        total_flagged = sum(1 for state in self.analyzer.get_all_values()
                          if state == AI_FLAGGED)

        if total_unknown == 0:
            return 0.0

        remaining_mines = NUM_BOMBS - total_flagged
        return remaining_mines / total_unknown

    def _calculate_global_probability(self, target_tile=None):
        """
        Calculate probability based on remaining mines / unknown tiles.

        Returns:
            float if target_tile provided, dict otherwise
        """
        total_unknown = sum(1 for state in self.analyzer.get_all_values()
                          if state == AI_UNKNOWN)
        total_flagged = sum(1 for state in self.analyzer.get_all_values()
                          if state == AI_FLAGGED)

        if total_unknown == 0:
            return 0.0

        remaining_mines = NUM_BOMBS - total_flagged
        global_prob = remaining_mines / total_unknown

        if target_tile:
            return global_prob

        # Return probability for all unknown tiles
        return {coord: global_prob for coord in self.analyzer.get_all_coordinates()
                if self.analyzer.get_tile_state(coord) == AI_UNKNOWN}

    def _get_distance_to_frontier(self, tile):
        """
        Calculate minimum distance from tile to any revealed tile.

        Args:
            tile: Coordinate tuple (x, y)

        Returns:
            int: Minimum Manhattan distance to frontier
        """
        min_distance = float('inf')

        for coord in self.analyzer.get_all_coordinates():
            state = self.analyzer.get_tile_state(coord)
            if state not in [AI_UNKNOWN, AI_FLAGGED]:
                distance = abs(tile[0] - coord[0]) + abs(tile[1] - coord[1])
                min_distance = min(min_distance, distance)

        return min_distance if min_distance != float('inf') else 1000

    def get_tile_constraints(self, tile):
        """
        Get all constraints affecting a specific tile (for debugging).

        Args:
            tile: Coordinate tuple (x, y)

        Returns:
            list of Constraint objects that include this tile
        """
        all_constraints = self.constraint_collector.collect_all_constraints()
        return [c for c in all_constraints if tile in c.get_constrained_tiles()]

    def format_probabilities(self, max_results=20):
        """
        Format probabilities in a human-readable way (for debugging).

        Args:
            max_results: Maximum number of tiles to show

        Returns:
            str: Formatted probability string
        """
        probabilities = self.calculate_probabilities()

        if not probabilities:
            return "No probabilities available (no unknown tiles or calculation failed)"

        # Sort by probability (lowest first - safest moves)
        sorted_probs = sorted(probabilities.items(), key=lambda x: x[1])

        lines = ["Mine Probabilities (lowest = safest):"]
        lines.append("-" * 40)

        for i, (tile, prob) in enumerate(sorted_probs[:max_results]):
            percentage = prob * 100
            bar_length = int(prob * 20)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            lines.append(f"{tile}: {percentage:5.1f}% {bar}")

        if len(sorted_probs) > max_results:
            lines.append(f"... and {len(sorted_probs) - max_results} more tiles")

        return "\n".join(lines)

    def find_lowest_probability_tile(self):
        """
        Find the tile with the lowest mine probability (safest tile to click).

        Uses smart tie-breaking:
        1. Primary: Lowest probability
        2. Secondary: Closest to frontier (more information gain)
        3. Tertiary: Random selection

        Returns:
            tuple: ((x, y), probability) or (None, 1.0) if no tiles available
        """
        probabilities = self.calculate_probabilities()

        if not probabilities or not isinstance(probabilities, dict):
            return (None, 1.0)

        # Find minimum probability
        min_prob = min(probabilities.values())

        # Get all tiles with minimum probability
        candidates = [(tile, prob) for tile, prob in probabilities.items()
                     if prob == min_prob]

        if len(candidates) == 1:
            return candidates[0]

        # Tie-breaking: prefer frontier tiles
        candidates_with_distance = [
            (tile, prob, self._get_distance_to_frontier(tile))
            for tile, prob in candidates
        ]
        candidates_with_distance.sort(key=lambda x: x[2])

        # Get all tiles with minimum distance
        min_distance = candidates_with_distance[0][2]
        best_candidates = [(tile, prob) for tile, prob, dist in candidates_with_distance
                          if dist == min_distance]

        # Random selection among remaining ties
        return random.choice(best_candidates)

    def find_highest_probability_tile(self, threshold=0.9):
        """
        Find the tile with the highest mine probability (best tile to flag).

        Args:
            threshold: Only return tiles with probability >= threshold

        Returns:
            tuple: ((x, y), probability) or (None, 0.0) if no good candidates
        """
        probabilities = self.calculate_probabilities()

        if not probabilities or not isinstance(probabilities, dict):
            return (None, 0.0)

        # Find tile with maximum probability
        best_tile, best_prob = max(probabilities.items(), key=lambda x: x[1])

        # Only return if above threshold
        if best_prob >= threshold:
            return (best_tile, best_prob)

        return (None, 0.0)
```

**Step 3: Commit refactored ProbabilityCalculator**

```bash
git add Minesweeper/ai/probability/probability_calculator.py
git commit -m "Refactor ProbabilityCalculator to use three-layer architecture"
```

---

## Phase 3: Test and Verify

### Task 7: Integration testing - Compare outputs

**Files:**
- Read: `Minesweeper/ai/probability/probability_calculator.py`
- Test: Run AI games

**Step 1: Test basic probability calculation**

Run a simple test by starting the game in AI mode:

```bash
cd Minesweeper
python game_runner.py
```

Select mode 0 (AI Only Mode). Let it run for 5-10 games.

Expected: AI should play without errors. Win rate should be similar to before (~70%).

**Step 2: Monitor for errors**

Watch console for any Python errors or exceptions. Common issues to check:
- Import errors (missing modules)
- AttributeError (method name mismatches)
- Logic errors (incorrect probability calculations)

If errors occur, fix them and commit the fixes.

**Step 3: Verify probabilities are reasonable**

While AI is playing, probabilities should:
- Be between 0.0 and 1.0
- Tiles next to revealed numbers should have lower probabilities than random tiles
- Known mines should have probability ~1.0
- Known safe tiles should not be in the probability map

---

### Task 8: End-to-end validation with statistics

**Files:**
- Test: Run extended AI games

**Step 1: Run 50+ games and collect win rate**

Let the AI play 50-100 games in AI Only Mode. Track the win rate displayed on screen.

Expected: Win rate should stabilize around 65-75% (similar to before refactoring).

**Step 2: Compare to baseline**

If win rate is significantly different (>10% difference):
- Check for logic errors in new components
- Verify configuration generation is producing same results
- Check log-space arithmetic is correct

**Step 3: Document results**

Note down the results. If win rate is acceptable, proceed to cleanup.

---

## Phase 4: Clean Up

### Task 9: Delete old files and update imports

**Files:**
- Delete: `Minesweeper/ai/probability/configuration_validator.py`
- Modify: `Minesweeper/ai/probability/__init__.py`

**Step 1: Verify configuration_validator.py is no longer used**

Search for any remaining imports:

```bash
cd Minesweeper
grep -r "configuration_validator" . --include="*.py"
```

Expected: Should only find the file itself, no imports.

**Step 2: Delete configuration_validator.py**

```bash
git rm Minesweeper/ai/probability/configuration_validator.py
```

**Step 3: Update __init__.py to export only public interfaces**

Edit `Minesweeper/ai/probability/__init__.py`:

```python
from .probability_calculator import ProbabilityCalculator
from .constraint import Constraint

__all__ = ['ProbabilityCalculator', 'Constraint']
```

**Step 4: Final commit**

```bash
git add Minesweeper/ai/probability/__init__.py
git commit -m "Remove old configuration_validator and clean up exports"
```

**Step 5: Push branch**

```bash
git push -u origin refactor/probability-three-layer
```

---

## Success Criteria Checklist

- [ ] All new components created (math_utilities, grouper, strategies, generator)
- [ ] ProbabilityCalculator refactored to orchestrate three layers
- [ ] Public API unchanged (calculate_probabilities works identically)
- [ ] AI runs without errors
- [ ] Win rate remains ~70% (65-75% acceptable)
- [ ] Old configuration_validator.py deleted
- [ ] Code is clearer and easier to trace through layers
- [ ] Each component has single responsibility

---

## Notes for Implementation

**Key Principles:**
- **DRY:** Math utilities eliminate duplication
- **YAGNI:** No speculative features, just refactoring existing behavior
- **SRP:** Each class has one clear responsibility
- **Traceability:** Can easily follow: constraints → groups → configs → probabilities

**Testing Strategy:**
- No unit tests needed (refactoring, behavior should be identical)
- Integration testing via running the AI
- End-to-end validation via win rate statistics

**Rollback Plan:**
If something goes wrong, the worktree makes it easy to compare old vs new or abandon the refactor.
