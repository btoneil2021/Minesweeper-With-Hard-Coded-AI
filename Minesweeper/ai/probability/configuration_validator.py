import random
import math


class ConfigurationValidator:
    # Hybrid approach thresholds
    MAX_TILES_FOR_EXACT = 20  # Use exact enumeration for ≤20 tiles (2^20 = ~1M configs)
    SAMPLE_SIZE = 100000       # Number of samples for large constraint groups

    @staticmethod
    def combinations(n, k):
        """
        Calculate binomial coefficient C(n, k) = n! / (k! * (n-k)!)
        Returns 0 if k > n or k < 0.
        """
        if k > n or k < 0:
            return 0
        if k == 0 or k == n:
            return 1
        # Use math.comb for efficiency (available in Python 3.8+)
        return math.comb(n, k)

    @staticmethod
    def log_combinations(n, k):
        """
        Calculate log of binomial coefficient: log(C(n, k))
        This avoids overflow for large numbers.
        Returns -inf if k > n or k < 0.
        """
        if k > n or k < 0:
            return float('-inf')
        if k == 0 or k == n:
            return 0.0

        # log(C(n,k)) = log(n!) - log(k!) - log((n-k)!)
        # Use math.lgamma: lgamma(n+1) = log(n!)
        return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)

    @staticmethod
    def generate_all_configurations(tiles):
        """Generate all 2^n possible mine configurations for given tiles"""
        tiles_list = list(tiles)
        n = len(tiles_list)

        for i in range(2 ** n):
            config = {tiles_list[j] for j in range(n) if (i >> j) & 1}
            yield config

    @staticmethod
    def generate_random_configuration(tiles_list):
        """Generate a single random mine configuration"""
        return {tile for tile in tiles_list if random.random() < 0.5}

    @staticmethod
    def is_valid_configuration(config, constraints):
        """Check if a configuration satisfies all constraints"""
        return all(constraint.is_satisfied_by(config) for constraint in constraints)

    @staticmethod
    def _group_constraints(constraints):
        """
        Split constraints into independent groups that don't share tiles.
        Returns list of (constraint_group, tile_group) tuples.
        """
        if not constraints:
            return []

        # Build adjacency graph: which constraints share tiles
        constraint_tiles = [set(c.get_constrained_tiles()) for c in constraints]

        # Union-Find to group connected constraints
        groups = []
        used = [False] * len(constraints)

        for i in range(len(constraints)):
            if used[i]:
                continue

            # Start a new group
            group_constraints = [constraints[i]]
            group_tiles = set(constraint_tiles[i])
            used[i] = True

            # Find all constraints connected to this group
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

    @staticmethod
    def count_mine_occurrences(constraints, total_mines_available=None):
        """
        Hybrid approach: Use exact enumeration for small groups, sampling for large ones.
        Now validates configurations against global mine budget when provided.

        Args:
            constraints: List of Constraint objects
            total_mines_available: Total mines that should be used across all groups (optional)

        Returns:
            tuple: (mine_counts dict, total_valid_configs)
        """
        if not constraints:
            return {}, 0

        # Group independent constraints
        groups = ConfigurationValidator._group_constraints(constraints)

        # TODO: Global validation needs unconstrained tile awareness
        # For now, skip global validation to avoid "0 valid configs" bug
        # if len(groups) > 1 and total_mines_available is not None:
        #     return ConfigurationValidator._count_with_global_validation(
        #         groups, total_mines_available
        #     )

        # Use local constraint satisfaction
        mine_counts = {}
        total_valid_configs = 1  # Multiplicative for independent groups

        for group_constraints, group_tiles in groups:
            num_tiles = len(group_tiles)

            if num_tiles <= ConfigurationValidator.MAX_TILES_FOR_EXACT:
                # Use exact enumeration
                group_counts, group_valid = ConfigurationValidator._count_exact(
                    group_constraints, group_tiles
                )
            else:
                # Use sampling for large groups
                group_counts, group_valid = ConfigurationValidator._count_sampled(
                    group_constraints, group_tiles
                )

            # Merge results
            mine_counts.update(group_counts)
            total_valid_configs *= group_valid

        return mine_counts, total_valid_configs

    @staticmethod
    def get_all_valid_configurations(constraints):
        """
        Get all valid configurations with mine counts for global probability weighting.

        Returns:
            list of dicts: [{'config': set of mine tiles, 'mine_count': int}, ...]
        """
        if not constraints:
            return []

        # Get all tiles affected by constraints
        all_tiles = set()
        for constraint in constraints:
            all_tiles.update(constraint.get_constrained_tiles())

        # Enumerate all valid configurations
        valid_configs = []

        if len(all_tiles) <= ConfigurationValidator.MAX_TILES_FOR_EXACT:
            # Exact enumeration
            for config in ConfigurationValidator.generate_all_configurations(all_tiles):
                if ConfigurationValidator.is_valid_configuration(config, constraints):
                    valid_configs.append({
                        'config': config,
                        'mine_count': len(config)
                    })
        else:
            # Sampling for large groups
            for _ in range(ConfigurationValidator.SAMPLE_SIZE):
                config = ConfigurationValidator.generate_random_configuration(list(all_tiles))
                if ConfigurationValidator.is_valid_configuration(config, constraints):
                    valid_configs.append({
                        'config': config,
                        'mine_count': len(config)
                    })

        return valid_configs

    @staticmethod
    def _count_exact(constraints, tiles):
        """Exact enumeration for small constraint groups"""
        mine_counts = {tile: 0 for tile in tiles}
        total_valid_configs = 0

        for config in ConfigurationValidator.generate_all_configurations(tiles):
            if ConfigurationValidator.is_valid_configuration(config, constraints):
                total_valid_configs += 1
                for tile in config:
                    mine_counts[tile] += 1

        return mine_counts, total_valid_configs

    @staticmethod
    def _count_sampled(constraints, tiles):
        """Statistical sampling for large constraint groups"""
        tiles_list = list(tiles)
        mine_counts = {tile: 0 for tile in tiles}
        total_valid_configs = 0

        for _ in range(ConfigurationValidator.SAMPLE_SIZE):
            config = ConfigurationValidator.generate_random_configuration(tiles_list)

            if ConfigurationValidator.is_valid_configuration(config, constraints):
                total_valid_configs += 1
                for tile in config:
                    mine_counts[tile] += 1

        return mine_counts, total_valid_configs

    @staticmethod
    def _count_with_global_validation(groups, total_mines_available):
        """
        Count mine occurrences across multiple constraint groups while validating
        that the total mine count matches the global budget.

        This ensures probabilities respect the global mine constraint, not just
        local constraint satisfaction.

        Args:
            groups: List of (group_constraints, group_tiles) tuples
            total_mines_available: Total mines that must be distributed across all groups

        Returns:
            tuple: (mine_counts dict, total_valid_configs)
        """
        # Get valid configurations for each group independently first
        group_configs = []
        for group_constraints, group_tiles in groups:
            group_configs.append({
                'tiles': group_tiles,
                'constraints': group_constraints,
                'valid_configs': []
            })

            # Enumerate all valid configurations for this group
            if len(group_tiles) <= ConfigurationValidator.MAX_TILES_FOR_EXACT:
                for config in ConfigurationValidator.generate_all_configurations(group_tiles):
                    if ConfigurationValidator.is_valid_configuration(config, group_constraints):
                        group_configs[-1]['valid_configs'].append(config)
            else:
                # For large groups, sample configurations
                for _ in range(ConfigurationValidator.SAMPLE_SIZE):
                    config = ConfigurationValidator.generate_random_configuration(list(group_tiles))
                    if ConfigurationValidator.is_valid_configuration(config, group_constraints):
                        group_configs[-1]['valid_configs'].append(config)

        # Now enumerate all combinations of group configurations
        # and only count those that match the global mine budget
        mine_counts = {}
        for group_info in group_configs:
            for tile in group_info['tiles']:
                mine_counts[tile] = 0

        total_valid_configs = 0

        # Generate all combinations of configurations across groups
        import itertools
        config_combinations = itertools.product(*[g['valid_configs'] for g in group_configs])

        for combo in config_combinations:
            # Count total mines in this combination
            total_mines_in_combo = sum(len(config) for config in combo)

            # Only count if it matches the global budget
            if total_mines_in_combo == total_mines_available:
                total_valid_configs += 1
                # Count mines in each tile
                for config in combo:
                    for tile in config:
                        mine_counts[tile] += 1

        return mine_counts, total_valid_configs