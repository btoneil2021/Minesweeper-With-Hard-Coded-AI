class ConfigurationEnumerator:
    @staticmethod
    def generate_all_configurations(tiles):
        tiles_list = list(tiles)
        n = len(tiles_list)

        for i in range(2 ** n):
            config = {tiles_list[j] for j in range(n) if (i >> j) & 1}
            yield config

    @staticmethod
    def is_valid_configuration(config, constraints):
        return all(constraint.is_satisfied_by(config) for constraint in constraints)

    @staticmethod
    def count_mine_occurrences(constraints):
        constrained_tiles = set()
        for constraint in constraints:
            constrained_tiles.update(constraint.get_constrained_tiles())

        mine_counts = {tile: 0 for tile in constrained_tiles}
        total_valid_configs = 0

        for config in ConfigurationEnumerator.generate_all_configurations(constrained_tiles):
            if ConfigurationEnumerator.is_valid_configuration(config, constraints):
                total_valid_configs += 1
                for tile in config:
                    mine_counts[tile] += 1

        return mine_counts, total_valid_configs