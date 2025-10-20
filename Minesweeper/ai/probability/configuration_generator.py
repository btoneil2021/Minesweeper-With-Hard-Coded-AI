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
