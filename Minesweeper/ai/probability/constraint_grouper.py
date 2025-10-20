class ConstraintGrouper:
    """
    Groups constraints into independent sets that don't share tiles.

    Constraints that share tiles must be solved together. Independent groups
    can be solved separately and their results multiplied together.
    """

    @staticmethod
    def group_constraints(constraints):
        """
        Split constraints into independent groups using Union-Find approach.

        Args:
            constraints: List of Constraint objects

        Returns:
            List of tuples: [(group_constraints, group_tiles), ...]
            where group_constraints is a list of Constraint objects and
            group_tiles is a set of all tiles in that group
        """
        if not constraints:
            return []

        # Build list of constraint tiles for quick lookup
        constraint_tiles = [set(c.get_constrained_tiles()) for c in constraints]

        # Track which constraints have been assigned to groups
        used = [False] * len(constraints)
        groups = []

        for i in range(len(constraints)):
            if used[i]:
                continue

            # Start a new group with constraint i
            group_constraints = [constraints[i]]
            group_tiles = set(constraint_tiles[i])
            used[i] = True

            # Find all constraints that share tiles with this group
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
