"""Application window and navigation between menu, selector, and game."""

from collections.abc import Mapping

import customtkinter as ctk

from core.models import Character
from game.game_engine import GameEngine
from game.level_catalog import build_level_catalog
from gui.game_screen import GameScreen


def run_app(engine: GameEngine, characters: Mapping[str, Character]) -> None:
    public_state = engine.get_public_state()
    missing_ids = {c.character_id for c in public_state.cells if c.character_id not in characters}
    if missing_ids:
        raise ValueError(f"Missing character metadata: {sorted(missing_ids)}")

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    root = ctk.CTk()
    root.geometry("1100x700")
    root.minsize(900, 600)
    try:
        root.iconbitmap("assets/icons/app.ico")
    except Exception:
        pass

    levels = build_level_catalog()
    level_sizes = [level.size for level in levels]
    missing_ids = {
        cell.character_id
        for level in levels
        for cell in level.cells
        if cell.character_id not in characters
    }
    if missing_ids:
        raise ValueError(f"Missing character metadata: {sorted(missing_ids)}")
    current_screen: ctk.CTkFrame | None = None

    def display(screen: ctk.CTkFrame) -> None:
        nonlocal current_screen
        if current_screen is not None:
            current_screen.destroy()
        current_screen = screen
        screen.pack(fill="both", expand=True)

    def show_main_menu() -> None:
        root.title("Griductive")
        frame = ctk.CTkFrame(root, fg_color="#221e1d")
        center = ctk.CTkFrame(frame, fg_color="transparent")
        center.place(relx=0.5, rely=0.45, anchor="center")
        ctk.CTkLabel(center, text="GRIDUCTIVE", text_color="#ece5dd",
                     font=ctk.CTkFont(size=54, weight="bold")).pack(pady=(0, 8))
        ctk.CTkLabel(center, text="Solve the grid. Expose the truth.",
                     text_color="#8c8279", font=ctk.CTkFont(size=18)).pack(pady=(0, 36))
        ctk.CTkButton(center, text="START", width=240, height=54,
                      fg_color="#d4a574", hover_color="#bd8e5d", text_color="#221e1d",
                      font=ctk.CTkFont(size=18, weight="bold"),
                      command=show_level_select).pack()
        display(frame)

    def show_level_select() -> None:
        root.title("Griductive - Select Level")
        frame = ctk.CTkFrame(root, fg_color="#221e1d")
        ctk.CTkButton(frame, text="← BACK", width=110, command=show_main_menu,
                      fg_color="#3d3632", hover_color="#4a433e").pack(
                          anchor="nw", padx=24, pady=20)
        ctk.CTkLabel(frame, text="SELECT LEVEL", text_color="#ece5dd",
                     font=ctk.CTkFont(size=34, weight="bold")).pack(pady=(4, 24))
        sections = ctk.CTkFrame(frame, fg_color="transparent")
        sections.pack(fill="both", expand=True, padx=45, pady=(0, 40))
        for column, size in enumerate((3, 4, 5)):
            sections.grid_columnconfigure(column, weight=1)
            section = ctk.CTkFrame(sections, fg_color="#2d2926", corner_radius=14)
            section.grid(row=0, column=column, sticky="nsew", padx=10)
            ctk.CTkLabel(section, text=f"{size} × {size}", text_color="#d4a574",
                         font=ctk.CTkFont(size=26, weight="bold")).pack(pady=(28, 22))
            matching = [i for i, level_size in enumerate(level_sizes) if level_size == size]
            for index in matching:
                level_number = index + 1
                ctk.CTkButton(section, text=f"LEVEL {level_number}", width=190, height=48,
                              fg_color="#3d3632", hover_color="#d4a574",
                              font=ctk.CTkFont(size=15, weight="bold"),
                              command=lambda i=index: show_game(i)).pack(pady=9)
        display(frame)

    def show_game(index: int) -> None:
        selected_engine = GameEngine(levels[index])
        root.title(f"Griductive - {selected_engine.get_level_id()}")
        screen = GameScreen(
            root, engine=selected_engine, characters=characters,
            on_back=show_level_select,
            on_previous=(lambda: show_game(index - 1)) if index > 0 else None,
            on_next=(lambda: show_game(index + 1)) if index < len(level_sizes) - 1 else None,
            on_level_loaded=lambda loaded: root.title(f"Griductive - {loaded.get_level_id()}"),
        )
        display(screen)

    show_main_menu()
    root.mainloop()
