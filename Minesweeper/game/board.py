import random
from constants import *
from .tile import Tile


class Board:
    """Manages the minesweeper board state and tile initialization"""

    def __init__(self):
        self.dictionary = {}
        self._initialize_tiles()
        self._initialize_values()

    def _initialize_tiles(self):
        """Initialize all tiles and place bombs randomly"""
        x = 0
        y = 0
        # Create all tiles
        for i in range(NUM_TILES_Y):
            for j in range(NUM_TILES_X):
                self.dictionary[str((j, i))] = Tile(x=x, y=y)
                x += TILE_SIZE
            y += TILE_SIZE
            x = 0

        # Place bombs randomly
        for i in range(NUM_BOMBS):
            x = random.randint(0, NUM_TILES_X - 1)
            y = random.randint(0, NUM_TILES_Y - 1)
            # Ensure no duplicate bomb placement
            while self.dictionary[str((x, y))].isBomb:
                x = random.randint(0, NUM_TILES_X - 1)
                y = random.randint(0, NUM_TILES_Y - 1)
            self.dictionary[str((x, y))].isBomb = True

    def _initialize_values(self):
        """Calculate the number values for all non-bomb tiles"""
        for i in range(NUM_TILES_Y):
            for j in range(NUM_TILES_X):
                if not self.dictionary[str((j, i))].isBomb:
                    self._calculate_tile_value((j, i))

    def _calculate_tile_value(self, key):
        """Calculate how many bombs surround a given tile"""
        val = 0
        neighbors = self._get_neighbors(key)

        for neighbor in neighbors:
            if str(neighbor) in self.dictionary:
                if self.dictionary[str(neighbor)].isBomb:
                    val += 1

        # Update the tile with calculated value
        tile = self.dictionary[str(key)]
        self.dictionary[str(key)] = Tile(x=tile.x, y=tile.y, value=val, isBomb=tile.isBomb)

    def _get_neighbors(self, key):
        """Get all 8 neighboring coordinates for a given tile"""
        return [
            (key[0] + 1, key[1]),
            (key[0], key[1] + 1),
            (key[0] + 1, key[1] + 1),
            (key[0] - 1, key[1]),
            (key[0], key[1] - 1),
            (key[0] - 1, key[1] - 1),
            (key[0] - 1, key[1] + 1),
            (key[0] + 1, key[1] - 1)
        ]

    def draw(self, screen):
        """Draw all tiles on the screen"""
        for tile in self.dictionary.values():
            tile.draw(screen)

    def get_tile(self, key):
        """Get a tile by its coordinate key"""
        return self.dictionary.get(str(key))
