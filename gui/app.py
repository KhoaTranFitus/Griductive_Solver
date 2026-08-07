# gui/app.py
"""GUI application boundary.

This module owns the UI lifecycle. It receives an already configured engine;
it must not load levels or inspect the engine's private level and state.
"""

from collections.abc import Mapping

import customtkinter as ctk

from core.models import Character
from game.game_engine import GameEngine
from gui.game_screen import GameScreen


def run_app(
    engine: GameEngine,
    characters: Mapping[str, Character],
) -> None:
    """Run the UI using only the GameEngine public interface.

    Launches a CustomTkinter window with the full game screen.
    The function signature is final.
    """
    # Validate that all characters referenced by the level exist
    public_state = engine.get_public_state()
    missing_ids = {
        cell.character_id
        for cell in public_state.cells
        if cell.character_id not in characters
    }
    if missing_ids:
        raise ValueError(f"Missing character metadata: {sorted(missing_ids)}")

    # ── Configure CustomTkinter ──
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    # ── Create main window ──
    root = ctk.CTk()
    root.title(f"Griductive — {public_state.level_id}")
    root.geometry("1100x700")
    root.minsize(900, 600)

    # ── Icon (if available) ──
    try:
        root.iconbitmap("assets/icons/app.ico")
    except Exception:
        pass  # No icon available

    # ── Game screen ──
    def on_level_loaded(new_engine: GameEngine) -> None:
        """Callback when a new level is loaded via the LOAD button."""
        new_state = new_engine.get_public_state()
        root.title(f"Griductive — {new_state.level_id}")

    game_screen = GameScreen(
        root,
        engine=engine,
        characters=characters,
        on_level_loaded=on_level_loaded,
    )
    game_screen.pack(fill="both", expand=True)

    # ── Start event loop ──
    root.mainloop()
