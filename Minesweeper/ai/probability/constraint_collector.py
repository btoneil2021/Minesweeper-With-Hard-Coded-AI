from .constraint import Constraint
from constants import *

class ConstraintCollector:
    def __init__(self, board_analyzer):
        self.analyzer = board_analyzer

    def collect_all_constraints(self):
        constraints = []
        for coord in self.analyzer.get_all_coordinates():
            if constraint := self._extract_constraint_from_tile(coord):
                constraints.append(constraint)
        return constraints

    def _extract_constraint_from_tile(self, coord):
        tile_value = self.analyzer.get_tile_state(coord)

        if not self._is_numbered_tile(tile_value):
            return None

        unknown_neighbors, mines_remaining = self._analyze_tile_neighbors(coord, tile_value)

        if not unknown_neighbors:
            return None

        return Constraint(unknown_neighbors, mines_remaining)

    def _is_numbered_tile(self, tile_value):
        return tile_value not in [AI_FLAGGED, AI_UNKNOWN] and tile_value != 0

    def _analyze_tile_neighbors(self, coord, tile_value):
        unknown_neighbors = []
        mines_remaining = tile_value

        for neighbor in self.analyzer.get_neighbors(coord):
            if not self.analyzer.has_tile(neighbor):
                continue

            neighbor_state = self.analyzer.get_tile_state(neighbor)

            if neighbor_state == AI_UNKNOWN:
                unknown_neighbors.append(neighbor)
            elif neighbor_state == AI_FLAGGED:
                mines_remaining -= 1

        return unknown_neighbors, mines_remaining