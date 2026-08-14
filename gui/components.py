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
BG_ROOT         = "#0a0b0e"
BG_SIDEBAR      = "#0f1117"
BG_CARD         = "#161922"
BG_CARD_HOVER   = "#222736"
BG_POPUP        = "#141720"
BG_INPUT        = "#0d0f14"

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


# Card sizing configurations per grid size (3x3, 4x4, 5x5)
_CARD_CONFIGS: dict[int, dict] = {
    3: {
        "width": 175,
        "height": 210,
        "avatar_size_fd": 68,
        "avatar_size_fu": 34,
        "font_coord": 11,
        "font_name": 14,
        "font_occ": 12,
        "font_clue": 13,
    },
    4: {
        "width": 142,
        "height": 172,
        "avatar_size_fd": 54,
        "avatar_size_fu": 28,
        "font_coord": 10,
        "font_name": 13,
        "font_occ": 11,
        "font_clue": 12,
    },
    5: {
        "width": 118,
        "height": 144,
        "avatar_size_fd": 44,
        "avatar_size_fu": 24,
        "font_coord": 9,
        "font_name": 12,
        "font_occ": 10,
        "font_clue": 11,
    },
}


class CharacterCard(ctk.CTkFrame):
    """Board tile displaying a character card with face-down and face-up states.

    Face-Down Layout:
    -----------------
    Top-left: Coordinate (A1, B2...)
    Center: Prominent enlarged avatar image
    Below: Name (bold) & Occupation (muted)

    Face-Up Layout (Card C2 Style):
    -------------------------------
    Top Strip: Coordinate | Avatar | Name (bold) & Occupation (enlarged muted)
    Main Body: Large readable clue text dynamically wrapping to fill space
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
            corner_radius=10,
            fg_color=BG_CARD,
            border_width=2,
            border_color=BORDER_DEFAULT,
            **kwargs,
        )
        self.pack_propagate(False)
        self.grid_propagate(False)

        self._cell_id: str = ""
        self._character: Character | None = None
        self._is_revealed: bool = False
        self._verdict: Verdict | None = None
        self._clue: Clue | None = None
        self._highlighted: bool = False
        self._on_click = on_click

        # ══════════════════════════════════════════
        #  FACE-DOWN CONTAINER
        # ══════════════════════════════════════════
        self._fd_container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=6)

        self._fd_coord = ctk.CTkLabel(
            self._fd_container, text="",
            font=ctk.CTkFont(family="Consolas", size=cfg["font_coord"], weight="bold"),
            text_color=TEXT_SECONDARY, anchor="w",
        )
        self._fd_coord.pack(anchor="w", padx=6, pady=(3, 0))

        self._fd_avatar = ctk.CTkLabel(
            self._fd_container, text="",
            width=cfg["avatar_size_fd"], height=cfg["avatar_size_fd"],
        )
        self._fd_avatar.pack(pady=(2, 2))

        self._fd_name = ctk.CTkLabel(
            self._fd_container, text="",
            font=ctk.CTkFont(size=cfg["font_name"], weight="bold"),
            text_color=TEXT_PRIMARY,
            wraplength=cfg["width"] - 16, justify="center",
        )
        self._fd_name.pack(pady=(0, 0))

        self._fd_occ = ctk.CTkLabel(
            self._fd_container, text="",
            font=ctk.CTkFont(size=cfg["font_occ"]),
            text_color=TEXT_SECONDARY,
            wraplength=cfg["width"] - 16, justify="center",
        )
        self._fd_occ.pack(pady=(0, 4))

        # ══════════════════════════════════════════
        #  FACE-UP CONTAINER (Compact Header Strip + Large Clue Body)
        # ══════════════════════════════════════════
        self._fu_container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=6)

        # ── Compact Header Strip ──
        fu_header = ctk.CTkFrame(self._fu_container, fg_color="transparent")
        fu_header.pack(fill="x", padx=1, pady=(3, 0))

        self._fu_coord = ctk.CTkLabel(
            fu_header, text="",
            font=ctk.CTkFont(family="Consolas", size=cfg["font_coord"], weight="bold"),
            text_color=TEXT_SECONDARY, anchor="nw",
        )
        self._fu_coord.pack(side="left", anchor="n", padx=(0, 2), pady=(1, 0))

        self._fu_avatar = ctk.CTkLabel(
            fu_header, text="",
            width=cfg["avatar_size_fu"], height=cfg["avatar_size_fu"],
        )
        self._fu_avatar.pack(side="left", padx=(0, 2), pady=(3, 0), anchor="n")

        fu_info = ctk.CTkFrame(fu_header, fg_color="transparent")
        fu_info.pack(side="left", fill="x", expand=True, anchor="n")

        self._fu_name = ctk.CTkLabel(
            fu_info, text="",
            font=ctk.CTkFont(size=cfg["font_name"], weight="bold"),
            text_color=TEXT_PRIMARY, anchor="w", justify="left", height=12,
        )
        self._fu_name.pack(anchor="w", pady=(0, 1))

        self._fu_occ = ctk.CTkLabel(
            fu_info, text="",
            font=ctk.CTkFont(size=cfg["font_occ"]),
            text_color=TEXT_SECONDARY, anchor="w", justify="left", height=12,
        )
        self._fu_occ.pack(anchor="w", pady=(2, 0))

        # ── Large Clue Body Area ──
        self._lbl_clue = ctk.CTkLabel(
            self._fu_container, text="",
            font=ctk.CTkFont(size=cfg["font_clue"]),
            text_color="#ffffff",
            wraplength=cfg["width"] - 12,
            justify="center", anchor="center",
        )
        self._lbl_clue.pack(fill="both", expand=True, padx=4, pady=(4, 4))

        # Start with face-down visible
        self._fd_container.pack(fill="both", expand=True, padx=3, pady=3)

        # Click + hover bindings
        self.configure(cursor="hand2")
        self._bind_click_recursive(self)

    def _bind_click_recursive(self, widget: ctk.CTkBaseClass) -> None:
        """Bind click and hover events recursively to widget and children."""
        widget.bind("<Button-1>", self._handle_click)
        widget.bind("<Enter>", self._on_enter)
        widget.bind("<Leave>", self._on_leave)
        for child in widget.winfo_children():
            self._bind_click_recursive(child)

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
        self.configure(width=cfg["width"], height=cfg["height"])

        if not self._is_revealed:
            # ── Face-Down ──
            self._fu_container.pack_forget()
            self._fd_container.pack(fill="both", expand=True, padx=3, pady=3)

            self._fd_coord.configure(
                text=self._cell_id,
                font=ctk.CTkFont(family="Consolas", size=cfg["font_coord"], weight="bold"),
            )

            avatar_sz = cfg["avatar_size_fd"]
            img = None
            if self._character:
                img = load_avatar(self._character.avatar_path, avatar_sz)
            if img is None:
                img = create_placeholder(avatar_sz)
            self._fd_avatar.configure(image=img, width=avatar_sz, height=avatar_sz)
            self._fd_avatar._ref = img

            if self._character:
                self._fd_name.configure(
                    text=self._character.name,
                    font=ctk.CTkFont(size=cfg["font_name"], weight="bold"),
                    wraplength=cfg["width"] - 16,
                )
                self._fd_occ.configure(
                    text=self._character.occupation,
                    font=ctk.CTkFont(size=cfg["font_occ"]),
                    wraplength=cfg["width"] - 16,
                )
            else:
                self._fd_name.configure(text="Unknown")
                self._fd_occ.configure(text="")
        else:
            # ── Face-Up ──
            self._fd_container.pack_forget()
            self._fu_container.pack(fill="both", expand=True, padx=3, pady=3)

            self._fu_coord.configure(
                text=self._cell_id,
                font=ctk.CTkFont(family="Consolas", size=cfg["font_coord"], weight="bold"),
            )

            avatar_sz = cfg["avatar_size_fu"]
            img = None
            if self._character:
                img = load_avatar(self._character.avatar_path, avatar_sz)
            if img is None:
                img = create_placeholder(avatar_sz)
            self._fu_avatar.configure(image=img, width=avatar_sz, height=avatar_sz)
            self._fu_avatar._ref = img

            if self._character:
                self._fu_name.configure(
                    text=self._character.name,
                    font=ctk.CTkFont(size=cfg["font_name"], weight="bold"),
                    wraplength=cfg["width"] - avatar_sz - 35,
                )
                self._fu_occ.configure(
                    text=self._character.occupation,
                    font=ctk.CTkFont(size=cfg["font_occ"]),
                    wraplength=cfg["width"] - avatar_sz - 35,
                )
            else:
                self._fu_name.configure(text="Unknown")
                self._fu_occ.configure(text="")

            if self._clue is not None:
                self._lbl_clue.configure(
                    text=self._clue.display_text,
                    font=ctk.CTkFont(size=cfg["font_clue"]),
                    wraplength=cfg["width"] - 12,
                )
            else:
                self._lbl_clue.configure(text="")

        self._apply_style()

    def _apply_style(self) -> None:
        if self._highlighted:
            color = getattr(self, "_custom_border_color", None) or "#f1c40f"
            self.configure(border_color=color, border_width=3, corner_radius=10, fg_color=BG_CARD_HOVER)
        elif self._is_revealed and self._verdict == Verdict.CRIMINAL:
            self.configure(border_color=BORDER_CRIMINAL, border_width=2, corner_radius=10, fg_color=BG_CRIMINAL)
        elif self._is_revealed and self._verdict == Verdict.INNOCENT:
            self.configure(border_color=BORDER_INNOCENT, border_width=2, corner_radius=10, fg_color=BG_INNOCENT)
        else:
            self.configure(border_color=BORDER_DEFAULT, border_width=2, corner_radius=10, fg_color=BG_CARD)

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
#  HOW TO PLAY PANEL  —  Frameless rules panel
# ══════════════════════════════════════════════════════════

class HowToPlayPanel(ctk.CTkFrame):
    """Collapsible rules panel with interactive header toggle to free up space for Revealed Clues."""

    def __init__(self, master: ctk.CTkBaseClass, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        self._collapsed: bool = False

        # ── Header bar with title and expand/collapse arrow ──
        self._header = ctk.CTkFrame(self, fg_color="transparent", cursor="hand2")
        self._header.pack(fill="x", pady=(0, 4))

        self._lbl_title = ctk.CTkLabel(
            self._header,
            text="📖  HOW TO PLAY",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT_ACCENT,
            anchor="w",
        )
        self._lbl_title.pack(side="left", anchor="w")

        self._lbl_toggle = ctk.CTkLabel(
            self._header,
            text="▲",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT_SECONDARY,
            width=24,
            anchor="e",
        )
        self._lbl_toggle.pack(side="right", anchor="e")

        # ── Body container holding rules list ──
        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.pack(fill="x", pady=(0, 4))

        rules = [
            ("🎯", "Goal", "Deduce every suspect's status as Criminal or Innocent."),
            ("🃏", "Verdict", "Click any face-down card to declare a verdict."),
            ("📜", "Clues", "Revealed clues are true. Click face-up cards to highlight logic."),
            ("💡", "Logic", "Use proven facts and region constraints to solve grid."),
        ]

        for icon, title, desc in rules:
            row = ctk.CTkFrame(self._body, fg_color="transparent")
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(
                row,
                text=f"{icon} {title}:",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=TEXT_PRIMARY,
                anchor="w",
                width=85,
            ).pack(side="left", anchor="nw")

            ctk.CTkLabel(
                row,
                text=desc,
                font=ctk.CTkFont(size=11),
                text_color=TEXT_SECONDARY,
                wraplength=220,
                justify="left",
                anchor="w",
            ).pack(side="left", fill="x", expand=True)

        # Bind click handlers to header widgets
        self._header.bind("<Button-1>", lambda _e: self.toggle())
        self._lbl_title.bind("<Button-1>", lambda _e: self.toggle())
        self._lbl_toggle.bind("<Button-1>", lambda _e: self.toggle())

    def toggle(self) -> None:
        """Toggle collapse/expand state of the rules body."""
        self._collapsed = not self._collapsed
        if self._collapsed:
            self._body.pack_forget()
            self._lbl_toggle.configure(text="▼")
        else:
            self._body.pack(fill="x", pady=(0, 4))
            self._lbl_toggle.configure(text="▲")


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
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", height=36, **kwargs)

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(expand=True)

        buttons = [
            ("💡 Hint",       BTN_HINT,    BTN_HINT_H,    on_hint),
            ("⚡ Auto Solve", BTN_AUTO,    BTN_AUTO_H,    on_auto_solve),
            ("↻ Restart",    BTN_RESTART, BTN_RESTART_H, on_restart),
        ]

        for text, fg, hover, cmd in buttons:
            ctk.CTkButton(
                container, text=text,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=fg, hover_color=hover,
                width=90, height=32, corner_radius=8,
                command=cmd,
            ).pack(side="left", padx=3)


# ══════════════════════════════════════════════════════════
#  CONTROL PANEL (Legacy wrapper)
# ══════════════════════════════════════════════════════════

class ControlPanel(ctk.CTkFrame):
    """Sidebar panel with HINT, AUTO SOLVE, RESTART buttons."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        *,
        on_hint: Callable[[], None] | None = None,
        on_auto_solve: Callable[[], None] | None = None,
        on_restart: Callable[[], None] | None = None,
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
#  CLUE PANEL  —  Frameless scrollable clue list
# ══════════════════════════════════════════════════════════

class CluePanel(ctk.CTkFrame):
    """Scrollable panel showing revealed clues rendered directly on dark background."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_clue_click: Callable[[Clue], None] | None = None,
        **kwargs,
    ) -> None:
        self._characters: dict = kwargs.pop("characters", {})
        super().__init__(master, fg_color="transparent", **kwargs)
        self._on_clue_click = on_clue_click
        self._active_clue_id: str | None = None

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(
            header_frame, text="🔍  REVEALED CLUES",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT_ACCENT,
        ).pack(side="left")

        self._lbl_count = ctk.CTkLabel(
            header_frame, text="0",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=TEXT_PRIMARY,
            fg_color="#3d3632",
            corner_radius=8,
            width=24, height=18,
        )
        self._lbl_count.pack(side="right")

        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=BORDER_DEFAULT,
            scrollbar_button_hover_color=TEXT_SECONDARY,
        )
        self._scroll.pack(fill="both", expand=True)

        self._row_map: dict[str, ctk.CTkFrame] = {}

    def set_active_clue(self, clue_id: str | None) -> None:
        """Highlight active clue row in gold accent."""
        self._active_clue_id = clue_id
        for cid, row in self._row_map.items():
            if cid == clue_id:
                row.configure(fg_color="#3d3326", border_width=1, border_color="#f39c12")
            else:
                row.configure(fg_color="#272321", border_width=0)

    def update_clues(self, clues: tuple[Clue, ...]) -> None:
        """Replace all displayed clue rows."""
        for r in self._row_map.values():
            r.destroy()
        self._row_map.clear()

        self._lbl_count.configure(text=str(len(clues)))

        for idx, clue in enumerate(clues):
            is_active = (clue.id == self._active_clue_id)
            row = ctk.CTkFrame(
                self._scroll,
                fg_color="#3d3326" if is_active else ("#272321" if idx % 2 == 0 else "transparent"),
                corner_radius=6,
                border_width=1 if is_active else 0,
                border_color="#f39c12" if is_active else "#272321",
                cursor="hand2",
            )
            row.pack(padx=2, pady=2, fill="x")

            owner_name = clue.owner_cell
            if hasattr(self, "_characters") and self._characters:
                char = self._characters.get(clue.owner_cell)
                if char and hasattr(char, "name"):
                    owner_name = char.name

            lbl_owner = ctk.CTkLabel(
                row, text=f"[{owner_name}]",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=TEXT_ACCENT, width=75, anchor="w",
            )
            lbl_owner.pack(side="left", padx=(6, 4), pady=5)

            formatted_text = clue.display_text
            if hasattr(self, "_characters") and self._characters:
                for cid, char in self._characters.items():
                    if hasattr(char, "name"):
                        formatted_text = formatted_text.replace(cid, char.name)

            lbl_text = ctk.CTkLabel(
                row, text=formatted_text,
                font=ctk.CTkFont(size=11),
                text_color=TEXT_PRIMARY, wraplength=210, justify="left",
            )
            lbl_text.pack(side="left", padx=(0, 6), pady=5, fill="x", expand=True)

            if self._on_clue_click:
                handler = lambda _e, c=clue: self._on_clue_click(c)
                row.bind("<Button-1>", handler)
                lbl_owner.bind("<Button-1>", handler)
                lbl_text.bind("<Button-1>", handler)

            self._row_map[clue.id] = row

        if self._row_map:
            self._scroll._parent_canvas.yview_moveto(1.0)


# ══════════════════════════════════════════════════════════
#  STATUS MESSAGE  —  Clean feedback banner
# ══════════════════════════════════════════════════════════

class StatusMessage(ctk.CTkFrame):
    """Colour-coded feedback banner for submission results and game feedback."""

    _COLOURS = {
        "success": CLR_SUCCESS,
        "warning": CLR_WARNING,
        "error":   CLR_ERROR,
        "info":    CLR_INFO,
    }

    def __init__(self, master: ctk.CTkBaseClass, **kwargs) -> None:
        super().__init__(
            master, corner_radius=10, fg_color="#2a2522", border_width=1, border_color="#3a3430", height=44, **kwargs,
        )
        self.pack_propagate(False)

        self._accent = ctk.CTkFrame(
            self, fg_color=CLR_INFO, width=4, corner_radius=2,
        )
        self._accent.pack(side="left", fill="y", padx=0, pady=4)

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=(10, 12), pady=4)

        self._lbl = ctk.CTkLabel(
            content, text="Click a suspect card to begin.",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=TEXT_SECONDARY, wraplength=550, justify="left", anchor="w",
        )
        self._lbl.pack(fill="x", expand=True, pady=4)

    def set_message(self, text: str, level: str = "info") -> None:
        color = self._COLOURS.get(level, TEXT_SECONDARY)
        self._lbl.configure(text=text, text_color=color)
        self._accent.configure(fg_color=color)


# ══════════════════════════════════════════════════════════
#  VICTORY POPUP MODAL
# ══════════════════════════════════════════════════════════

class VictoryPopup(ctk.CTkToplevel):
    """Modal dialog displayed upon solving a puzzle level, showing elapsed time."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        elapsed_seconds: int,
        on_restart: Callable[[], None] | None = None,
        on_next: Callable[[], None] | None = None,
        on_back: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(master)
        self.title("Victory!")
        self.geometry("420x330")
        self.geometry("450x330")
        self.resizable(False, False)
        self.configure(fg_color="#1e1b18")
        self.transient(master.winfo_toplevel())
        self.grab_set()

        # Center on parent window
        self.update_idletasks()
        master_win = master.winfo_toplevel()
        x = master_win.winfo_x() + (master_win.winfo_width() // 2) - 225
        y = master_win.winfo_y() + (master_win.winfo_height() // 2) - 165
        self.geometry(f"+{x}+{y}")

        pad = ctk.CTkFrame(self, fg_color="#272321", corner_radius=16, border_width=2, border_color="#d4a574")
        pad.pack(fill="both", expand=True, padx=16, pady=16)

        # Trophy Icon & Title
        ctk.CTkLabel(
            pad, text="🏆", font=ctk.CTkFont(size=44)
        ).pack(pady=(16, 0))

        ctk.CTkLabel(
            pad, text="CASE SOLVED!",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#d4a574",
        ).pack(pady=(4, 2))

        ctk.CTkLabel(
            pad, text="Congratulations! You unmasked all suspects.",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SECONDARY,
        ).pack(pady=(0, 14))

        # Time Stat Card
        minutes = elapsed_seconds // 60
        seconds = elapsed_seconds % 60
        time_str = f"{minutes:02d}:{seconds:02d}"

        time_box = ctk.CTkFrame(pad, fg_color="#1e1b18", corner_radius=10, border_width=1, border_color="#3a3430")
        time_box.pack(padx=24, pady=(0, 16), fill="x")

        ctk.CTkLabel(
            time_box, text="⏱  COMPLETION TIME",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=TEXT_SECONDARY,
        ).pack(pady=(8, 2))

        ctk.CTkLabel(
            time_box, text=time_str,
            font=ctk.CTkFont(family="Consolas", size=26, weight="bold"),
            text_color="#2ecc71",
        ).pack(pady=(0, 8))

        # Action Buttons (Equal grid column weights)
        btn_frame = ctk.CTkFrame(pad, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=(0, 8))

        col_count = 1 + (1 if on_back else 0) + (1 if on_next else 0)
        for c in range(col_count):
            btn_frame.grid_columnconfigure(c, weight=1)

        col_idx = 0

        if on_back:
            ctk.CTkButton(
                btn_frame, text="← Levels",
                font=ctk.CTkFont(size=12),
                fg_color="#3d3632", hover_color="#4a433e", text_color=TEXT_PRIMARY,
                height=36, corner_radius=8,
                command=lambda: [self.destroy(), on_back()],
            ).grid(row=0, column=col_idx, sticky="ew", padx=3)
            col_idx += 1

        ctk.CTkButton(
            btn_frame, text="↻ Replay",
            font=ctk.CTkFont(size=12),
            fg_color="#3d3632", hover_color="#4a433e", text_color=TEXT_PRIMARY,
            height=36, corner_radius=8,
            command=lambda: [self.destroy(), on_restart() if on_restart else None],
        ).grid(row=0, column=col_idx, sticky="ew", padx=3)
        col_idx += 1

        if on_next:
            ctk.CTkButton(
                btn_frame, text="Next Level →",
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#d4a574", hover_color="#bd8e5d", text_color="#221e1d",
                height=36, corner_radius=8,
                command=lambda: [self.destroy(), on_next()],
            ).grid(row=0, column=col_idx, sticky="ew", padx=3)


# ══════════════════════════════════════════════════════════
#  VERDICT DEDUCTION FEEDBACK POPUPS
# ══════════════════════════════════════════════════════════

class VerdictFeedbackPopup(ctk.CTkToplevel):
    """Modal dialog displaying deduction feedback matching reference designs (without Share button).

    Supports two states:
    1. NOT_PROVABLE ("Conclusion not possible") - Yellow warning icon ⚠️
    2. CONTRADICTED ("That's not it") - Red prohibition icon 🚫
    """

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        character_name: str,
        verdict: str,
        result_type: str = "NOT_PROVABLE",
        opposite_verdict: str | None = None,
    ) -> None:
        super().__init__(master)

        is_contradicted = (result_type.upper() == "CONTRADICTED")
        title_text = "That's not it" if is_contradicted else "Conclusion not possible"
        self.title(title_text)

        self.geometry("440x310")
        self.resizable(False, False)
        self.configure(fg_color="#181514")
        self.transient(master.winfo_toplevel())
        self.grab_set()

        # Center on parent window
        self.update_idletasks()
        master_win = master.winfo_toplevel()
        x = master_win.winfo_x() + (master_win.winfo_width() // 2) - 220
        y = master_win.winfo_y() + (master_win.winfo_height() // 2) - 155
        self.geometry(f"+{x}+{y}")

        # Outer card frame matching reference dark styling
        card = ctk.CTkFrame(
            self,
            fg_color="#282320",
            corner_radius=18,
            border_width=1,
            border_color="#3e3733",
        )
        card.pack(fill="both", expand=True, padx=14, pady=14)

        # ── Top Circular Icon Badge ──
        icon_color = "#f07167" if is_contradicted else "#d4a574"
        icon_symbol = "🚫" if is_contradicted else "⚠️"

        icon_frame = ctk.CTkFrame(
            card,
            width=52, height=52, corner_radius=26,
            fg_color="transparent",
            border_width=2,
            border_color=icon_color,
        )
        icon_frame.pack(pady=(16, 8))
        icon_frame.pack_propagate(False)

        ctk.CTkLabel(
            icon_frame,
            text=icon_symbol,
            font=ctk.CTkFont(size=22),
            text_color=icon_color,
        ).pack(expand=True)

        # ── Title ──
        ctk.CTkLabel(
            card,
            text=title_text,
            font=ctk.CTkFont(family="Georgia", size=20, weight="bold"),
            text_color="#ffffff",
        ).pack(pady=(0, 10))

        # ── Body Text with Bold Tokens ──
        verdict_clean = verdict.lower()
        if opposite_verdict:
            opp_clean = opposite_verdict.lower()
        else:
            opp_clean = "innocent" if verdict_clean == "criminal" else "criminal"

        if is_contradicted:
            msg = (
                f"The statements you've unlocked rule out "
                f"{character_name} being {verdict_clean} — read them again and "
                f"take another angle."
            )
        else:
            msg = (
                f"You can't prove {character_name} is {verdict_clean} from the "
                f"statements you've unlocked yet — there's still "
                f"a consistent case where {character_name} is {opp_clean}.\n"
                f"Unlock more testimony first, or lean on a hint."
            )

        ctk.CTkLabel(
            card,
            text=msg,
            font=ctk.CTkFont(size=12),
            text_color="#d0c8c0",
            wraplength=370,
            justify="center",
        ).pack(pady=(0, 18), padx=16)

        # ── Single "Keep looking" Button (NO Share button) ──
        ctk.CTkButton(
            card,
            text="Keep looking",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#f07167",
            hover_color="#d85b51",
            text_color="#ffffff",
            height=42,
            width=170,
            corner_radius=12,
            command=self.destroy,
        ).pack(pady=(0, 14))


# Backward-compatibility alias
NotProvablePopup = VerdictFeedbackPopup

