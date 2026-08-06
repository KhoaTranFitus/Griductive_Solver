"""GUI application boundary.

This module owns the UI lifecycle. It receives an already configured engine;
it must not load levels or inspect the engine's private level and state.
"""

from collections.abc import Mapping

from core.models import Character
from game.game_engine import GameEngine


def run_app(
    engine: GameEngine,
    characters: Mapping[str, Character],
) -> None:
    """Run the UI using only the GameEngine public interface.

    The temporary console output keeps the application runnable until Member 3
    installs the selected GUI framework. The function signature is final.
    """
    public_state = engine.get_public_state()
    missing_ids = {
        cell.character_id
        for cell in public_state.cells
        if cell.character_id not in characters
    }
    if missing_ids:
        raise ValueError(f"Missing character metadata: {sorted(missing_ids)}")

    print(f"Griductive: {public_state.level_id}")
    print(f"Board: {public_state.size}x{public_state.size}")
    print("Unresolved:", ", ".join(public_state.unresolved_cells))
