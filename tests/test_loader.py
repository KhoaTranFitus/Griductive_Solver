# tests/test_loader.py
from game.level_loader import load_level
from game.level_validator import validate_level


def test_load_level_01():
    level = load_level("data/levels/level_01.json")

    assert level.id == "level_01"
    assert level.size == 3
    assert len(level.cells) == 9
    assert len(level.clues) == 9

    validate_level(level)