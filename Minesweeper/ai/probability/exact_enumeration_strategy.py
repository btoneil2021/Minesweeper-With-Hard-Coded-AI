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
