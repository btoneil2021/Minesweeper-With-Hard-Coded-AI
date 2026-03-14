from minesweeper.domain.types import GameConfig

import pytest


def test_default_config() -> None:
    config = GameConfig()

    assert config.width == 30
    assert config.height == 16
    assert config.num_mines == 99


def test_mines_exceed_tiles() -> None:
    with pytest.raises(ValueError):
        GameConfig(width=3, height=3, num_mines=9)

    with pytest.raises(ValueError):
        GameConfig(width=3, height=3, num_mines=10)


def test_mines_at_limit() -> None:
    config = GameConfig(width=3, height=3, num_mines=8)

    assert config.num_mines == 8


def test_config_frozen() -> None:
    config = GameConfig()

    with pytest.raises(AttributeError):
        config.width = 50
