# gui/components.py
"""Reusable GUI components for the Griductive logic-puzzle game.

Components
──────────
CharacterCard   – board tile showing avatar, name, occupation, verdict
VerdictPopup    – modal dialog triggered on face-down card click
ControlPanel    – HINT / AUTO SOLVE / RESTART / LOAD buttons
CluePanel       – scrollable list of revealed clues
StatusMessage   – colour-coded feedback banner
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont

from core.enums import Verdict
from core.models import Character, Clue


# ══════════════════════════════════════════════════════════
#  COLOUR PALETTE  —  Dark Minimalist
# ══════════════════════════════════════════════════════════

# Background layers
BG_ROOT         = "#221e1d"
BG_SIDEBAR      = "#1c1917"
BG_CARD         = "#2d2926"
BG_CARD_HOVER   = "#3a3430"
BG_POPUP        = "#2d2926"
BG_INPUT        = "#1c1917"

# Face-up card tints
BG_INNOCENT     = "#192a1f"
BG_CRIMINAL     = "#2e1b1b"

# Borders
BORDER_DEFAULT  = "#3d3632"
BORDER_INNOCENT = "#27ae60"
BORDER_CRIMINAL = "#c0392b"
BORDER_HINT     = "#d4a574"

# Text
TEXT_PRIMARY    = "#ece5dd"
TEXT_SECONDARY  = "#8c8279"
TEXT_ACCENT     = "#d4a574"

# Verdict colours
CLR_INNOCENT   = "#2ecc71"
CLR_CRIMINAL   = "#e74c3c"
CLR_UNKNOWN    = "#6b6560"

# Button colours                  normal      hover
BTN_HINT       = "#6c3d8f";  BTN_HINT_H    = "#7d4ea0"
BTN_AUTO       = "#8f6c2d";  BTN_AUTO_H    = "#a07d3e"
BTN_RESTART    = "#2c3e50";  BTN_RESTART_H = "#34495e"
BTN_LOAD       = "#1a5e50";  BTN_LOAD_H    = "#238b76"
BTN_CANCEL     = "#3d3632";  BTN_CANCEL_H  = "#4a433e"

# Status levels
CLR_SUCCESS    = "#2ecc71"
CLR_WARNING    = "#f39c12"
CLR_ERROR      = "#e74c3c"
CLR_INFO       = "#5dade2"

# Layout constants
AVATAR_SIZE         = 64
AVATAR_POPUP_SIZE   = 100
CARD_WIDTH          = 160
CARD_HEIGHT         = 265


# ══════════════════════════════════════════════════════════
#  AVATAR HELPERS
# ══════════════════════════════════════════════════════════

def load_avatar(path_str: str, size: int = AVATAR_SIZE) -> ctk.CTkImage | None:
    """Load a character avatar PNG. Returns *None* on any failure."""
    path = Path(path_str)
    if not path.exists():
        return None
    try:
        img = Image.open(path).convert("RGBA")
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
    except Exception:
        return None


def create_placeholder(size: int = AVATAR_SIZE) -> ctk.CTkImage:
    """Generate a neutral placeholder square with a "?" glyph."""
    img = Image.new("RGBA", (size, size), (45, 41, 38, 255))
    draw = ImageDraw.Draw(img)
    m = size // 5
    draw.rounded_rectangle(
        [m, m, size - m, size - m],
        radius=size // 8,
        fill=(60, 55, 50, 255),
        outline=(80, 75, 68, 255),
        width=2,
    )
    try:
        font = ImageFont.truetype("arial", size // 3)
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), "?", font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        ((size - tw) // 2, (size - th) // 2 - bbox[1]),
        "?", fill=(140, 130, 122, 255), font=font,
    )
    return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))


# Card sizing configurations per grid size (3x3, 4x4, 5x5) for seamless auto-fit scaling
_CARD_CONFIGS: dict[int, dict] = {
    3: {
        "width": 150,
        "height": 240,
        "avatar_size": 58,
        "font_name": 11,
        "font_occ": 9,
        "font_verdict": 9,
        "font_clue": 8,
        "padx": 5,
        "pady": 5,
    },
    4: {
        "width": 115,
        "height": 180,
        "avatar_size": 40,
        "font_name": 10,
        "font_occ": 8,
        "font_verdict": 8,
        "font_clue": 7,
        "padx": 3,
        "pady": 3,
    },
    5: {
        "width": 92,
        "height": 145,
        "avatar_size": 30,
        "font_name": 9,
        "font_occ": 7,
        "font_verdict": 7,
        "font_clue": 7,
        "padx": 2,
        "pady": 2,
    },
}


class CharacterCard(ctk.CTkFrame):
    """Board tile displaying one character.

    States
    ------
    Face-down : neutral dark card, unknown verdict, clue hidden.
    Face-up   : tinted background (green/red), verdict shown, clue visible.
    Highlighted : amber border glow (used by the HINT feature).
    """

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        grid_size: int = 3,
        on_click: Callable[[str], None] | None = None,
        **kwargs,
    ) -> None:
        self._grid_size = grid_size
        cfg = _CARD_CONFIGS.get(grid_size, _CARD_CONFIGS[3])
        super().__init__(
            master,
            width=cfg["width"],
            height=cfg["height"],
            corner_radius=14,
            fg_color=BG_CARD,
            border_width=2,
            border_color=BORDER_DEFAULT,
            **kwargs,
        )
        self.pack_propagate(False)

        self._cell_id: str = ""
        self._character: Character | None = None
        self._is_revealed: bool = False
        self._verdict: Verdict | None = None
        self._clue: Clue | None = None
        self._highlighted: bool = False
        self._on_click = on_click

        # ── sub-widgets ──
        self._lbl_coord = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(family="Consolas", size=9, weight="bold"),
            text_color=TEXT_SECONDARY, height=14,
        )
        self._lbl_coord.pack(padx=6, pady=(6, 0), anchor="nw")

        self._lbl_avatar = ctk.CTkLabel(
            self, text="", width=cfg["avatar_size"], height=cfg["avatar_size"],
        )
        self._lbl_avatar.pack(pady=(2, 2))

        self._lbl_name = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(size=cfg["font_name"], weight="bold"),
            text_color=TEXT_PRIMARY, wraplength=cfg["width"] - 12,
        )
        self._lbl_name.pack(padx=4)

        self._lbl_occ = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(size=cfg["font_occ"]),
            text_color=TEXT_SECONDARY, wraplength=cfg["width"] - 12,
        )
        self._lbl_occ.pack(padx=4, pady=(0, 2))

        self._lbl_verdict = ctk.CTkLabel(
            self, text="?",
            font=ctk.CTkFont(size=cfg["font_verdict"], weight="bold"),
            text_color=CLR_UNKNOWN, height=18,
        )
        self._lbl_verdict.pack(padx=6, pady=(2, 0))

        self._lbl_clue = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(size=cfg["font_clue"]),
            text_color=TEXT_SECONDARY,
            wraplength=cfg["width"] - 14, justify="center",
        )
        self._lbl_clue.pack(padx=6, pady=(2, 6), fill="x", expand=True)

        # Click + hover bindings (card and all children)
        self.configure(cursor="hand2")
        self.bind("<Button-1>", self._handle_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        for child in self.winfo_children():
            child.bind("<Button-1>", self._handle_click)
            child.bind("<Enter>", self._on_enter)
            child.bind("<Leave>", self._on_leave)

    # ── public API ────────────────────────────────

    def set_data(
        self,
        cell_id: str,
        character: Character | None,
        is_revealed: bool,
        verdict: Verdict | None,
        clue: Clue | None,
        grid_size: int = 3,
    ) -> None:
        """Bind data and re-render."""
        self._cell_id = cell_id
        self._character = character
        self._is_revealed = is_revealed
        self._verdict = verdict
        self._clue = clue
        self._grid_size = grid_size
        self._render()

    def set_highlighted(self, on: bool, border_color: str | None = None) -> None:
        self._highlighted = on
        self._custom_border_color = border_color if on else None
        self._apply_style()

    # ── internal ──────────────────────────────────

    def _render(self) -> None:
        cfg = _CARD_CONFIGS.get(self._grid_size, _CARD_CONFIGS[3])

        # Adapt frame dimensions
        self.configure(width=cfg["width"], height=cfg["height"])

        self._lbl_coord.configure(text=self._cell_id)

        # avatar
        img = None
        if self._character:
            img = load_avatar(self._character.avatar_path, cfg["avatar_size"])
        if img is None:
            img = create_placeholder(cfg["avatar_size"])
        self._lbl_avatar.configure(
            image=img, width=cfg["avatar_size"], height=cfg["avatar_size"]
        )
        self._lbl_avatar._ref = img  # prevent garbage collection

        # name / occupation
        if self._character:
            self._lbl_name.configure(
                text=self._character.name,
                font=ctk.CTkFont(size=cfg["font_name"], weight="bold"),
                wraplength=cfg["width"] - 12,
            )
            self._lbl_occ.configure(
                text=self._character.occupation,
                font=ctk.CTkFont(size=cfg["font_occ"]),
                wraplength=cfg["width"] - 12,
            )
        else:
            self._lbl_name.configure(text="Unknown")
            self._lbl_occ.configure(text="")

        # verdict badge
        if self._is_revealed and self._verdict is not None:
            if self._verdict == Verdict.CRIMINAL:
                self._lbl_verdict.configure(
                    text="CRIMINAL",
                    text_color=CLR_CRIMINAL,
                    font=ctk.CTkFont(size=cfg["font_verdict"], weight="bold"),
                )
            elif self._verdict == Verdict.INNOCENT:
                self._lbl_verdict.configure(
                    text="INNOCENT",
                    text_color=CLR_INNOCENT,
                    font=ctk.CTkFont(size=cfg["font_verdict"], weight="bold"),
                )
            else:
                self._lbl_verdict.configure(
                    text="?",
                    text_color=CLR_UNKNOWN,
                    font=ctk.CTkFont(size=cfg["font_verdict"], weight="bold"),
                )
        else:
            self._lbl_verdict.configure(
                text="?",
                text_color=CLR_UNKNOWN,
                font=ctk.CTkFont(size=cfg["font_verdict"], weight="bold"),
            )

        # clue (face-up only — never expose hidden clues)
        if self._is_revealed and self._clue is not None:
            self._lbl_clue.configure(
                text=f'"{self._clue.display_text}"',
                font=ctk.CTkFont(size=cfg["font_clue"]),
                wraplength=cfg["width"] - 14,
            )
        else:
            self._lbl_clue.configure(text="")

        self._apply_style()

    def _apply_style(self) -> None:
        if self._highlighted:
            color = getattr(self, "_custom_border_color", None) or BORDER_HINT
            self.configure(border_color=color, border_width=3, fg_color=BG_CARD_HOVER)
        elif self._is_revealed and self._verdict == Verdict.CRIMINAL:
            self.configure(border_color=BORDER_CRIMINAL, border_width=2, fg_color=BG_CRIMINAL)
        elif self._is_revealed and self._verdict == Verdict.INNOCENT:
            self.configure(border_color=BORDER_INNOCENT, border_width=2, fg_color=BG_INNOCENT)
        else:
            self.configure(border_color=BORDER_DEFAULT, border_width=2, fg_color=BG_CARD)

    def _on_enter(self, _e) -> None:
        if not self._is_revealed and not self._highlighted:
            self.configure(fg_color=BG_CARD_HOVER)

    def _on_leave(self, _e) -> None:
        if not self._is_revealed and not self._highlighted:
            self.configure(fg_color=BG_CARD)

    def _handle_click(self, _e) -> None:
        if self._on_click and self._cell_id:
            self._on_click(self._cell_id)


# ══════════════════════════════════════════════════════════
#  VERDICT POPUP  (modal dialog)
# ══════════════════════════════════════════════════════════

class VerdictPopup(ctk.CTkToplevel):
    """Modal dialog asking the player to declare Innocent or Criminal.

    Opened automatically when clicking an unsolved (face-down) card.
    Displays avatar, name, cell coordinate, occupation, and two
    bordered verdict buttons plus a Cancel option.
    """

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        cell_id: str,
        character: Character,
        on_verdict: Callable[[str, Verdict], None],
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)

        self._cell_id = cell_id
        self._character = character
        self._on_verdict = on_verdict

        # ── window chrome ──
        self.title("")
        self.configure(fg_color=BG_POPUP)
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        self.protocol("WM_DELETE_WINDOW", self._cancel)

        # ── build content ──
        self._build_ui()

        # ── centre on parent ──
        self.update_idletasks()
        parent = master.winfo_toplevel()
        px, py = parent.winfo_x(), parent.winfo_y()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        self.geometry(f"+{px + (pw - w) // 2}+{py + (ph - h) // 2}")

        # make modal
        self.grab_set()
        self.focus_set()

    def _build_ui(self) -> None:
        pad = ctk.CTkFrame(self, fg_color="transparent")
        pad.pack(padx=36, pady=32)

        # avatar (larger)
        img = load_avatar(self._character.avatar_path, AVATAR_POPUP_SIZE)
        if img is None:
            img = create_placeholder(AVATAR_POPUP_SIZE)
        lbl_avatar = ctk.CTkLabel(
            pad, text="", image=img,
            width=AVATAR_POPUP_SIZE, height=AVATAR_POPUP_SIZE,
        )
        lbl_avatar._ref = img
        lbl_avatar.pack(pady=(0, 14))

        # name
        ctk.CTkLabel(
            pad, text=self._character.name,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack()

        # cell · occupation
        ctk.CTkLabel(
            pad,
            text=f"[{self._cell_id}]  ·  {self._character.occupation}",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SECONDARY,
        ).pack(pady=(2, 18))

        # thin separator
        ctk.CTkFrame(pad, height=1, fg_color=BORDER_DEFAULT).pack(fill="x", pady=(0, 18))

        # question
        ctk.CTkLabel(
            pad, text="Innocent or Criminal?",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=TEXT_ACCENT,
        ).pack(pady=(0, 18))

        # verdict buttons (bordered outline style)
        btn_row = ctk.CTkFrame(pad, fg_color="transparent")
        btn_row.pack(pady=(0, 14))

        ctk.CTkButton(
            btn_row, text="INNOCENT",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="transparent",
            border_width=2, border_color=BORDER_INNOCENT,
            text_color=CLR_INNOCENT,
            hover_color=BORDER_INNOCENT,
            width=136, height=44, corner_radius=10,
            command=self._pick_innocent,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_row, text="CRIMINAL",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="transparent",
            border_width=2, border_color=BORDER_CRIMINAL,
            text_color=CLR_CRIMINAL,
            hover_color=BORDER_CRIMINAL,
            width=136, height=44, corner_radius=10,
            command=self._pick_criminal,
        ).pack(side="left", padx=(10, 0))

        # cancel link
        ctk.CTkButton(
            pad, text="Cancel",
            font=ctk.CTkFont(size=12),
            fg_color="transparent", text_color=TEXT_SECONDARY,
            hover_color=BTN_CANCEL_H,
            width=80, height=28,
            command=self._cancel,
        ).pack(pady=(4, 0))

    # ── callbacks ──

    def _pick_innocent(self) -> None:
        self._on_verdict(self._cell_id, Verdict.INNOCENT)
        self.destroy()

    def _pick_criminal(self) -> None:
        self._on_verdict(self._cell_id, Verdict.CRIMINAL)
        self.destroy()

    def _cancel(self) -> None:
        self.destroy()


# ══════════════════════════════════════════════════════════
#  HOW TO PLAY PANEL
# ══════════════════════════════════════════════════════════

class HowToPlayPanel(ctk.CTkFrame):
    """Dedicated rules panel explaining game mechanics with elegant typography."""

    def __init__(self, master: ctk.CTkBaseClass, **kwargs) -> None:
        super().__init__(master, corner_radius=14, fg_color=BG_CARD, **kwargs)

        ctk.CTkLabel(
            self, text="📖 HOW TO PLAY",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT_ACCENT,
        ).pack(padx=16, pady=(14, 10), anchor="w")

        rules = [
            ("🎯 Goal", "Deduce every suspect's status as Criminal or Innocent."),
            ("🃏 Verdict", "Click any face-down card to declare a verdict."),
            ("📜 Clues", "Revealed clues are always true. Click face-up cards to highlight clue logic!"),
            ("💡 Logic", "Use proven facts and region constraints to solve the grid."),
        ]

        for title, desc in rules:
            item = ctk.CTkFrame(self, fg_color=BG_INPUT, corner_radius=10)
            item.pack(padx=12, pady=5, fill="x")

            ctk.CTkLabel(
                item, text=title,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=TEXT_ACCENT, width=75, anchor="w",
            ).pack(side="left", padx=(10, 6), pady=8)

            ctk.CTkLabel(
                item, text=desc,
                font=ctk.CTkFont(size=11),
                text_color=TEXT_PRIMARY, wraplength=220, justify="left",
            ).pack(side="left", padx=(0, 8), pady=8, fill="x", expand=True)

        ctk.CTkFrame(self, height=10, fg_color="transparent").pack()


# ══════════════════════════════════════════════════════════
#  COMPACT ACTION TOOLBAR
# ══════════════════════════════════════════════════════════

class CompactActionToolbar(ctk.CTkFrame):
    """Compact horizontal bottom toolbar for game utility actions."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        *,
        on_hint: Callable[[], None] | None = None,
        on_auto_solve: Callable[[], None] | None = None,
        on_restart: Callable[[], None] | None = None,
        on_load: Callable[[], None] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(master, corner_radius=12, fg_color=BG_CARD, height=44, **kwargs)

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(padx=10, pady=5, expand=True)

        buttons = [
            ("💡 Hint",       BTN_HINT,    BTN_HINT_H,    on_hint),
            ("⚡ Auto Solve", BTN_AUTO,    BTN_AUTO_H,    on_auto_solve),
            ("↻ Restart",    BTN_RESTART, BTN_RESTART_H, on_restart),
            ("📂 Load Level", BTN_LOAD,    BTN_LOAD_H,    on_load),
        ]

        for text, fg, hover, cmd in buttons:
            ctk.CTkButton(
                container, text=text,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=fg, hover_color=hover,
                width=100, height=30, corner_radius=6,
                command=cmd,
            ).pack(side="left", padx=4)


# ══════════════════════════════════════════════════════════
#  CONTROL PANEL (Legacy wrapper)
# ══════════════════════════════════════════════════════════

class ControlPanel(ctk.CTkFrame):
    """Sidebar panel with HINT, AUTO SOLVE, RESTART, LOAD buttons."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        *,
        on_hint: Callable[[], None] | None = None,
        on_auto_solve: Callable[[], None] | None = None,
        on_restart: Callable[[], None] | None = None,
        on_load: Callable[[], None] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(master, corner_radius=14, fg_color=BG_CARD, **kwargs)

        ctk.CTkLabel(
            self, text="ACTIONS",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=TEXT_ACCENT,
        ).pack(padx=14, pady=(14, 8))

        buttons = [
            ("💡  Hint",        BTN_HINT,    BTN_HINT_H,    on_hint),
            ("⚡  Auto Solve",  BTN_AUTO,    BTN_AUTO_H,    on_auto_solve),
            ("↻   Restart",     BTN_RESTART, BTN_RESTART_H, on_restart),
            ("📂  Load Level",  BTN_LOAD,    BTN_LOAD_H,    on_load),
        ]
        for text, fg, hover, cmd in buttons:
            ctk.CTkButton(
                self, text=text,
                font=ctk.CTkFont(size=12),
                fg_color=fg, hover_color=hover,
                height=34, corner_radius=8,
                command=cmd,
            ).pack(padx=14, pady=3, fill="x")

        ctk.CTkFrame(self, height=8, fg_color="transparent").pack()


# ══════════════════════════════════════════════════════════
#  CLUE PANEL
# ══════════════════════════════════════════════════════════

class CluePanel(ctk.CTkFrame):
    """Scrollable panel showing all currently revealed clues."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_clue_click: Callable[[Clue], None] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(master, corner_radius=14, fg_color=BG_CARD, **kwargs)
        self._on_clue_click = on_clue_click

        ctk.CTkLabel(
            self, text="REVEALED CLUES",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=TEXT_ACCENT,
        ).pack(padx=14, pady=(14, 6))

        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=BORDER_DEFAULT,
            scrollbar_button_hover_color=TEXT_SECONDARY,
        )
        self._scroll.pack(padx=8, pady=(0, 10), fill="both", expand=True)

        self._rows: list[ctk.CTkFrame] = []

    def update_clues(self, clues: tuple[Clue, ...]) -> None:
        """Replace all displayed clue rows."""
        for r in self._rows:
            r.destroy()
        self._rows.clear()

        for clue in clues:
            row = ctk.CTkFrame(self._scroll, fg_color=BG_INPUT, corner_radius=8, cursor="hand2")
            row.pack(padx=4, pady=2, fill="x")

            lbl_owner = ctk.CTkLabel(
                row, text=f"[{clue.owner_cell}]",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=TEXT_ACCENT, width=36,
            )
            lbl_owner.pack(side="left", padx=(8, 4), pady=6)

            lbl_text = ctk.CTkLabel(
                row, text=clue.display_text,
                font=ctk.CTkFont(size=10),
                text_color=TEXT_PRIMARY, wraplength=200, justify="left",
            )
            lbl_text.pack(side="left", padx=(0, 8), pady=6, fill="x", expand=True)

            if self._on_clue_click:
                handler = lambda _e, c=clue: self._on_clue_click(c)
                row.bind("<Button-1>", handler)
                lbl_owner.bind("<Button-1>", handler)
                lbl_text.bind("<Button-1>", handler)

            self._rows.append(row)


# ══════════════════════════════════════════════════════════
#  STATUS MESSAGE
# ══════════════════════════════════════════════════════════

class StatusMessage(ctk.CTkFrame):
    """Colour-coded banner for submission results and game feedback."""

    _COLOURS = {
        "success": CLR_SUCCESS,
        "warning": CLR_WARNING,
        "error":   CLR_ERROR,
        "info":    CLR_INFO,
    }

    def __init__(self, master: ctk.CTkBaseClass, **kwargs) -> None:
        super().__init__(
            master, corner_radius=14, fg_color=BG_CARD, **kwargs,
        )

        ctk.CTkLabel(
            self, text="STATUS",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT_ACCENT,
        ).pack(padx=14, pady=(8, 2), anchor="w")

        self._lbl = ctk.CTkLabel(
            self, text="Click a suspect card to begin.",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_SECONDARY, wraplength=450, justify="left",
        )
        self._lbl.pack(padx=14, pady=(0, 8), anchor="w", fill="x")

    def set_message(self, text: str, level: str = "info") -> None:
        self._lbl.configure(
            text=text,
            text_color=self._COLOURS.get(level, TEXT_SECONDARY),
        )
