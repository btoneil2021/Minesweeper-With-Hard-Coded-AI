class NeighborUtils:
    """Provides neighbor calculation utilities"""

    def get_neighbors(self, coord):
        """Get all 8 neighboring coordinates for a given tile"""
        return [
            (coord[0] - 1, coord[1] - 1),  (coord[0] - 1, coord[1]),  (coord[0] - 1, coord[1] + 1),
            (coord[0],     coord[1] - 1),                         (coord[0],     coord[1] + 1),
            (coord[0] + 1, coord[1] - 1),  (coord[0] + 1, coord[1]),  (coord[0] + 1, coord[1] + 1),
        ]

    def get_cardinal_neighbors(self, coord):
        """Get only the 4 cardinal direction neighbors"""
        return [
                        (coord[0], coord[1] - 1),
            (coord[0] - 1, coord[1]),           (coord[0] + 1, coord[1]),
                        (coord[0], coord[1] + 1),
        ]
