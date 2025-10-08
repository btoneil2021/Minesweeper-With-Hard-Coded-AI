import random


class ConfigurationValidator:
    # Hybrid approach thresholds
    MAX_TILES_FOR_EXACT = 20  # Use exact enumeration for ≤20 tiles (2^20 = ~1M configs)
    SAMPLE_SIZE = 100000       # Number of samples for large constraint groups

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
    def count_mine_occurrences(constraints):
        """
        Hybrid approach: Use exact enumeration for small groups, sampling for large ones.

        Returns:
            tuple: (mine_counts dict, total_valid_configs)
        """
        if not constraints:
            return {}, 0

        # Group independent constraints
        groups = ConfigurationValidator._group_constraints(constraints)

        # Process each group
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