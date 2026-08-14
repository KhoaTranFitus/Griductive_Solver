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
    root.minsize(940, 640)
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

    # ══════════════════════════════════════════════════════════
    #  HOME SCREEN (MAIN MENU)  —  Ultra-Sleek Dark Design
    # ══════════════════════════════════════════════════════════

    def show_main_menu() -> None:
        root.title("Griductive")
        frame = ctk.CTkFrame(root, fg_color="#0a0b0e")

        # Subtle Ambient Glow Accents (Top-Left Blue & Bottom-Right Purple)
        glow_tl = ctk.CTkFrame(frame, width=280, height=280, corner_radius=140, fg_color="#0e1e38")
        glow_tl.place(relx=-0.08, rely=-0.1)

        glow_br = ctk.CTkFrame(frame, width=280, height=280, corner_radius=140, fg_color="#240c30")
        glow_br.place(relx=0.85, rely=0.75)

        # Center Container
        center = ctk.CTkFrame(frame, fg_color="transparent")
        center.place(relx=0.5, rely=0.48, anchor="center")

        # Large Tracked Title: G R I D U C T I V E
        ctk.CTkLabel(
            center,
            text="G  R  I  D  U  C  T  I  V  E",
            text_color="#ffffff",
            font=ctk.CTkFont(family="Consolas", size=48, weight="bold"),
        ).pack(pady=(0, 36))

        # Action Buttons Container
        btn_box = ctk.CTkFrame(center, fg_color="transparent")
        btn_box.pack(pady=0)

        # START GAME Button (Glowing Cyan Outline)
        ctk.CTkButton(
            btn_box,
            text="START GAME",
            width=260,
            height=46,
            fg_color="#0e1a2b",
            hover_color="#182c48",
            text_color="#e0f2fe",
            border_width=1,
            border_color="#4f7a9c",
            corner_radius=4,
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            command=show_level_select,
        ).pack(pady=7)

        # SETTINGS Button (Dark Sleek Outline)
        ctk.CTkButton(
            btn_box,
            text="SETTINGS",
            width=260,
            height=46,
            fg_color="#0d0f14",
            hover_color="#161a24",
            text_color="#9aa2b6",
            border_width=1,
            border_color="#252936",
            corner_radius=4,
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            command=show_settings_dialog,
        ).pack(pady=7)

        # QUIT Button (Dark Sleek Outline)
        ctk.CTkButton(
            btn_box,
            text="QUIT",
            width=260,
            height=46,
            fg_color="#0d0f14",
            hover_color="#161a24",
            text_color="#9aa2b6",
            border_width=1,
            border_color="#252936",
            corner_radius=4,
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            command=root.quit,
        ).pack(pady=7)

        display(frame)

    # ══════════════════════════════════════════════════════════
    #  LEVEL SELECT SCREEN  —  Matching Sleek Aesthetic
    # ══════════════════════════════════════════════════════════

    def show_level_select() -> None:
        root.title("Griductive - Select Level")
        frame = ctk.CTkFrame(root, fg_color="#0a0b0e")

        # Top Bar
        top_bar = ctk.CTkFrame(frame, fg_color="transparent")
        top_bar.pack(fill="x", padx=36, pady=(24, 0))

        ctk.CTkButton(
            top_bar,
            text="←  BACK TO MENU",
            width=160,
            height=36,
            fg_color="#0d0f14",
            hover_color="#161a24",
            text_color="#9aa2b6",
            border_width=1,
            border_color="#252936",
            corner_radius=4,
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            command=show_main_menu,
        ).pack(side="left")

        # Header Title
        ctk.CTkLabel(
            frame,
            text="S E L E C T   L E V E L",
            text_color="#ffffff",
            font=ctk.CTkFont(family="Consolas", size=32, weight="bold"),
        ).pack(pady=(16, 24))

        # Grid Sections Container
        sections = ctk.CTkFrame(frame, fg_color="transparent")
        sections.pack(fill="both", expand=True, padx=45, pady=(0, 40))

        section_colors = {
            3: "#4f7a9c",  # Cyan accent
            4: "#7c5ea8",  # Purple accent
            5: "#a85e78",  # Rose accent
        }

        for column, size in enumerate((3, 4, 5)):
            sections.grid_columnconfigure(column, weight=1)

            section = ctk.CTkFrame(
                sections,
                fg_color="#11131a",
                corner_radius=14,
                border_width=1,
                border_color="#232736",
            )
            section.grid(row=0, column=column, sticky="nsew", padx=12)

            accent_color = section_colors.get(size, "#4f7a9c")

            # Grid Mode Title
            ctk.CTkLabel(
                section,
                text=f"{size} × {size}  GRID",
                text_color=accent_color,
                font=ctk.CTkFont(family="Consolas", size=22, weight="bold"),
            ).pack(pady=(28, 20))

            matching = [i for i, level_size in enumerate(level_sizes) if level_size == size]
            for index in matching:
                level_number = index + 1
                ctk.CTkButton(
                    section,
                    text=f"LEVEL {level_number:02d}",
                    width=210,
                    height=46,
                    fg_color="#161924",
                    hover_color="#222838",
                    text_color="#ffffff",
                    border_width=1,
                    border_color="#2c3345",
                    corner_radius=6,
                    font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
                    command=lambda i=index: show_game(i),
                ).pack(pady=9)

        display(frame)

    # ══════════════════════════════════════════════════════════
    #  SETTINGS MODAL DIALOG
    # ══════════════════════════════════════════════════════════

    def show_settings_dialog() -> None:
        dialog = ctk.CTkToplevel(root)
        dialog.title("Settings")
        dialog.geometry("420x300")
        dialog.resizable(False, False)
        dialog.configure(fg_color="#0a0b0e")
        dialog.transient(root)
        dialog.grab_set()

        # Center on root
        dialog.update_idletasks()
        x = root.winfo_x() + (root.winfo_width() // 2) - 210
        y = root.winfo_y() + (root.winfo_height() // 2) - 150
        dialog.geometry(f"+{x}+{y}")

        card = ctk.CTkFrame(
            dialog,
            fg_color="#11131a",
            corner_radius=16,
            border_width=1,
            border_color="#232736",
        )
        card.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            card,
            text="S E T T I N G S",
            font=ctk.CTkFont(family="Consolas", size=20, weight="bold"),
            text_color="#ffffff",
        ).pack(pady=(20, 16))

        # Options
        row1 = ctk.CTkFrame(card, fg_color="transparent")
        row1.pack(fill="x", padx=24, pady=8)
        ctk.CTkLabel(
            row1, text="Theme Mode:", font=ctk.CTkFont(size=13), text_color="#9aa2b6"
        ).pack(side="left")
        ctk.CTkLabel(
            row1, text="Dark Aesthetic", font=ctk.CTkFont(size=13, weight="bold"), text_color="#e0f2fe"
        ).pack(side="right")

        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(fill="x", padx=24, pady=8)
        ctk.CTkLabel(
            row2, text="Version:", font=ctk.CTkFont(size=13), text_color="#9aa2b6"
        ).pack(side="left")
        ctk.CTkLabel(
            row2, text="v2.0.0", font=ctk.CTkFont(size=13, weight="bold"), text_color="#e0f2fe"
        ).pack(side="right")

        ctk.CTkButton(
            card,
            text="CLOSE",
            width=140,
            height=38,
            fg_color="#0e1a2b",
            hover_color="#182c48",
            text_color="#e0f2fe",
            border_width=1,
            border_color="#4f7a9c",
            corner_radius=4,
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            command=dialog.destroy,
        ).pack(pady=(24, 0))

    # ══════════════════════════════════════════════════════════
    #  GAME SCREEN LAUNCHER
    # ══════════════════════════════════════════════════════════

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

