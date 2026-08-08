"""Load the authored JSON levels shown by the level-select screen."""

from pathlib import Path

from core.models import Level
from game.level_loader import load_level
from game.level_validator import validate_level


LEVEL_LAYOUT = (
    ("level_01.json", "level_01", 3),
    ("level_02.json", "level_02", 3),
    ("level_03.json", "level_03", 4),
    ("level_04.json", "level_04", 4),
    ("level_05.json", "level_05", 5),
    ("level_06.json", "level_06", 5),
)


def build_level_catalog(
    levels_directory: str | Path = "data/levels",
) -> list[Level]:
    """Load and validate Level 1 through Level 6 in navigation order."""
    directory = Path(levels_directory)
    levels: list[Level] = []

    for filename, expected_id, expected_size in LEVEL_LAYOUT:
        level = load_level(directory / filename)
        validate_level(level)

        if level.id != expected_id:
            raise ValueError(
                f"{filename} must have id {expected_id!r}, got {level.id!r}."
            )
        if level.size != expected_size:
            raise ValueError(
                f"{filename} must be {expected_size}x{expected_size}, "
                f"got {level.size}x{level.size}."
            )

        levels.append(level)

    return levels
