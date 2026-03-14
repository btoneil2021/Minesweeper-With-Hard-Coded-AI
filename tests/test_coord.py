from minesweeper.domain.types import Coord


def test_neighbors_center() -> None:
    neighbors = Coord(5, 5).neighbors()

    assert len(neighbors) == 8
    assert Coord(5, 5) not in neighbors
    assert {(neighbor.x - 5, neighbor.y - 5) for neighbor in neighbors} == {
        (-1, -1),
        (-1, 0),
        (-1, 1),
        (0, -1),
        (0, 1),
        (1, -1),
        (1, 0),
        (1, 1),
    }


def test_neighbors_origin() -> None:
    neighbors = Coord(0, 0).neighbors()

    assert len(neighbors) == 8
    assert Coord(-1, -1) in neighbors
    assert Coord(-1, 0) in neighbors
    assert Coord(0, -1) in neighbors


def test_neighbors_deterministic() -> None:
    coord = Coord(7, 2)

    assert coord.neighbors() == coord.neighbors()


def test_coord_hashable() -> None:
    coords = {Coord(3, 4)}
    mapping = {Coord(3, 4): "target"}

    assert Coord(3, 4) in coords
    assert mapping[Coord(3, 4)] == "target"
    assert Coord(3, 4) == Coord(3, 4)
    assert Coord(3, 4) != Coord(4, 3)


def test_coord_unpacks() -> None:
    x, y = Coord(3, 4)

    assert x == 3
    assert y == 4
