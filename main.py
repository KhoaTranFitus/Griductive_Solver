"""Griductive composition root.

Only this module loads and validates the selected level and wires application
dependencies. UI behavior belongs to ``gui.app``.
"""

from pathlib import Path

from game.game_engine import GameEngine
from game.level_loader import load_level
from game.level_validator import validate_level
from gui.app import run_app
from gui.character_loader import load_characters
from logic.deductive_agent import DeductiveAgent

DEFAULT_LEVEL_PATH = Path("data/levels/level_01.json")
DEFAULT_CHARACTER_PATH = Path("data/characters.json")


def create_engine(
    level_path: str | Path = DEFAULT_LEVEL_PATH,
    agent: DeductiveAgent | None = None,
) -> GameEngine:
    """Load a valid level and return a fully wired game engine."""
    level = load_level(level_path)
    validate_level(level)
    return GameEngine(level, agent=agent)


def main() -> None:
    """Create the application dependencies and hand control to the GUI."""
    engine = create_engine()
    characters = load_characters(DEFAULT_CHARACTER_PATH)
    run_app(engine, characters)


if __name__ == "__main__":
    main()
