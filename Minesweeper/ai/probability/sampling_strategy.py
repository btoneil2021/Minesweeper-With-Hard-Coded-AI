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
