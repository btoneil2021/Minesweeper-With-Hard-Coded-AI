# Probability System Refactoring Design

**Date:** 2025-10-20
**Status:** Approved for Implementation
**Goal:** Refactor probability calculation system for clarity, maintainability, and single-responsibility principle

## Problem Statement

The current probability calculation code has organizational issues that make it hard to understand and maintain:

1. **ConfigurationValidator** does too many things: grouping, enumeration, counting, and sampling
2. **Log-space arithmetic** is duplicated across multiple methods in ProbabilityCalculator
3. **Flow is unclear**: Hard to trace from board state → constraints → configurations → probabilities
4. **Classes lack single responsibility**: Mixed concerns throughout

## Goals

1. **Easy traceability**: Follow the flow from board state → constraints → configurations → probabilities
2. **Single responsibility**: Each class has one clear purpose
3. **Maintainability**: Easy to test, modify, and extend each component independently

## Solution: Three-Layer Architecture

The refactored system will have three distinct layers:

### Layer 1: Constraint Layer
**Purpose:** Extract and organize constraints from board state

**Components:**
- `constraint.py` - Simple data class (keep as-is, already clean)
  - Holds tiles and required_mines
  - Methods: `is_satisfied_by(config)`, `get_constrained_tiles()`

- `constraint_collector.py` - Extract constraints from board (minimal changes)
  - Single responsibility: Convert numbered tiles into Constraint objects
  - Method: `collect_all_constraints()` → list of Constraint objects

- `constraint_grouper.py` - NEW (extracted from ConfigurationValidator)
  - Single responsibility: Partition constraints into independent groups
  - Method: `group_constraints(constraints)` → list of (constraint_list, tile_set) tuples
  - Groups constraints that share tiles together
  - Independent groups can be solved separately

**Data Flow:**
```
BoardAnalyzer → ConstraintCollector.collect_all_constraints()
             → ConstraintGrouper.group_constraints()
             → List of (constraints, tiles) groups
```

### Layer 2: Configuration Layer
**Purpose:** Generate valid mine configurations that satisfy constraints

**Components:**
- `configuration_generator.py` - NEW (orchestrator)
  - Single responsibility: Generate valid mine configurations
  - Method: `generate_valid_configurations(constraints, tiles)` → list of `{'config': set, 'mine_count': int}`
  - Delegates to appropriate strategy based on problem size

- `exact_enumeration_strategy.py` - NEW (extracted logic)
  - Strategy for small constraint groups (≤20 tiles)
  - Enumerates all 2^n configurations, filters valid ones
  - Pure function style, no state
  - Returns complete list of valid configurations

- `sampling_strategy.py` - NEW (extracted logic)
  - Strategy for large constraint groups (>20 tiles)
  - Randomly samples configurations, keeps valid ones
  - Contains SAMPLE_SIZE constant (100,000)
  - Returns sampled valid configurations

**Decision Logic:**
```python
if len(tiles) <= 20:
    use ExactEnumerationStrategy
else:
    use SamplingStrategy
```

**Data Flow:**
```
(constraints, tiles) → ConfigurationGenerator.generate()
                    → [strategy based on size]
                    → List of valid configurations
```

### Layer 3: Probability Layer
**Purpose:** Calculate weighted probabilities using configurations

**Components:**
- `math_utilities.py` - NEW (extracted from multiple places)
  - Single responsibility: Log-space arithmetic and combinatorics
  - Pure functions, no state, highly testable
  - Functions:
    - `log_combinations(n, k)` → log(C(n,k)) to avoid overflow
    - `logsumexp(log_values)` → safely compute log(sum(exp(values)))
    - `weighted_probability(log_weights, tile_occurrences)` → convert weighted counts to probabilities
  - Centralizes duplicated log-space math

- `probability_calculator.py` - REFACTOR (becomes orchestrator)
  - Single responsibility: Orchestrate the probability calculation pipeline
  - Holds references to: ConstraintCollector, ConstraintGrouper, ConfigurationGenerator
  - Main method: `calculate_probabilities(target_tile=None)` - SAME PUBLIC API
  - Delegates work to layers 1, 2, 3 and utilities
  - Much shorter (~200 lines instead of 400)

**Data Flow:**
```
Configurations → Weight each by unconstrained tile possibilities
              → Aggregate using log-space math (MathUtilities)
              → Convert to probabilities per tile
              → Return probability map
```

## Complete System Flow

```
Board State (BoardAnalyzer)
    ↓
Layer 1: Constraint Extraction & Grouping
    → ConstraintCollector.collect_all_constraints()
    → ConstraintGrouper.group_constraints()
    ↓
Independent constraint groups
    ↓
Layer 2: Configuration Generation (per group)
    → ConfigurationGenerator.generate_valid_configurations()
    → [ExactEnumerationStrategy OR SamplingStrategy]
    ↓
Valid configurations with mine counts
    ↓
Layer 3: Probability Calculation
    → Weight configurations (MathUtilities.log_combinations)
    → Aggregate weighted counts (MathUtilities.logsumexp)
    → Convert to probabilities (MathUtilities.weighted_probability)
    ↓
Probability map {(x,y): probability}
```

## File Organization

### New Structure
```
ai/
├── pattern_detector.py              # KEEP (logic-based)
├── transitive_pattern_matcher.py   # KEEP (logic-based)
├── constraint_subtractor.py        # KEEP (logic-based, stays in place)
└── probability/                     # probability-based only
    ├── __init__.py                  # Exports ProbabilityCalculator, Constraint
    ├── constraint.py                # KEEP (already clean)
    ├── constraint_collector.py      # KEEP (minimal changes)
    ├── constraint_grouper.py        # NEW
    ├── configuration_generator.py   # NEW
    ├── exact_enumeration_strategy.py # NEW
    ├── sampling_strategy.py         # NEW
    ├── math_utilities.py            # NEW
    └── probability_calculator.py    # REFACTOR (simplified)
```

### Files to Delete
- `configuration_validator.py` - logic distributed to generator, strategies, and math_utilities

### Files to Keep Unchanged
- `constraint_subtractor.py` - stays in `ai/` (no move needed)
- All other AI strategy files remain untouched

## Migration Strategy

### Phase 1: Create New Components
- Create all new files: constraint_grouper, configuration_generator, strategies, math_utilities
- Extract and implement logic from existing files
- Old code continues to run unchanged
- **Outcome:** New components exist but aren't wired up yet

### Phase 2: Refactor ProbabilityCalculator
- Update ProbabilityCalculator to use new Layer 1, 2, 3 components
- Keep same public API: `calculate_probabilities(target_tile=None)`
- External code (ai_strategy.py) requires no changes
- **Outcome:** System uses new architecture

### Phase 3: Test and Verify
- Run AI games to verify win rate (~70%)
- Compare old vs new probability outputs (should be identical)
- Validate behavior matches original implementation
- **Outcome:** Confidence that refactor is correct

### Phase 4: Clean Up
- Delete `configuration_validator.py`
- Update any stale imports
- **Outcome:** Clean codebase with only new structure

## Testing Approach

### Unit Tests (Pure Functions)
- `math_utilities.py` - Test with known inputs/outputs
- `exact_enumeration_strategy.py` - Deterministic, easily testable
- `constraint_grouper.py` - Pure logic, testable
- Easy to verify correctness in isolation

### Integration Tests
- Compare old vs new ProbabilityCalculator output on same board states
- Verify probabilities are identical (or within epsilon for floating point)
- Ensures refactor didn't change behavior

### End-to-End Validation
- Run 100+ AI games before and after refactor
- Compare win rates (should be ~70% in both cases)
- Final confirmation system works correctly

## Benefits

1. **Clear Traceability:** Can easily follow: board → constraints → groups → configurations → probabilities
2. **Single Responsibility:** Each class has one clear job
3. **Testability:** Pure functions and focused classes are easy to test
4. **Maintainability:** Logic is organized and findable
5. **Extensibility:** Easy to add new strategies or utilities
6. **No Behavioral Changes:** Same public API, same results

## What Gets Removed

1. Commented-out `_count_with_global_validation` code (old relic)
2. Duplicated log-space arithmetic across methods
3. Mixed concerns in ConfigurationValidator
4. Unclear flow between components

## Success Criteria

- [ ] All new components created with single responsibilities
- [ ] ProbabilityCalculator orchestrates layers cleanly
- [ ] Public API unchanged (`calculate_probabilities()` works identically)
- [ ] AI win rate remains ~70%
- [ ] Code is easier to understand and trace
- [ ] Each component can be tested independently
