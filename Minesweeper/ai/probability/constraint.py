class Constraint:
    def __init__(self, tiles, required_mines):
        self.tiles = tuple(tiles)
        self.required_mines = required_mines

    def is_satisfied_by(self, mine_configuration):
        actual_mines = sum(1 for tile in self.tiles if tile in mine_configuration)
        return actual_mines == self.required_mines

    def get_constrained_tiles(self):
        return set(self.tiles)