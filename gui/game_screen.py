# gui/game_screen.py
"""Main game screen that assembles the board grid, clue panel, how to play guide,
bottom action toolbar, and status message into a cohesive layout.

The GameScreen communicates with the GameEngine exclusively through its public
interface (``get_public_state``, ``submit_verdict``, ``restart``, ``is_solved``,
``get_hint``, ``auto_solve_step``). It never accesses hidden solution data.
"""

from __future__ import annotations

import tkinter.filedialog as filedialog
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING

import customtkinter as ctk

from core.enums import ClueType, SubmissionResult, Verdict
from core.models import Character, Clue, PublicState
from gui.components import (
    CharacterCard,
    CluePanel,
    CompactActionToolbar,
    HowToPlayPanel,
    StatusMessage,
    VerdictPopup,
)
from logic.region_resolver import parse_region, resolve_region

if TYPE_CHECKING:
    from game.game_engine import GameEngine


class GameScreen(ctk.CTkFrame):
    """Full game screen with board grid, right rules & clues panel, and bottom action toolbar."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        engine: "GameEngine",
        characters: Mapping[str, Character],
        on_level_loaded: "callable | None" = None,
        on_back: "callable | None" = None,
        on_previous: "callable | None" = None,
        on_next: "callable | None" = None,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="#221e1d", **kwargs)

        self._engine = engine
        self._characters = dict(characters)
        self._on_level_loaded = on_level_loaded
        self._on_back = on_back
        self._on_previous = on_previous
        self._on_next = on_next
        self._highlighted_clue_id: str | None = None
        self._highlighted_cell: str | None = None
        self._cards: dict[str, CharacterCard] = {}
        self._auto_solving: bool = False

        self._build_layout()
        self._refresh_board()

    # ──────────────────────────────────────────────
    #  Layout construction
    # ──────────────────────────────────────────────
    def _build_layout(self) -> None:
        """Create the main grid layout:
        - Row 0: Board Container (Left) + Right Sidebar (How To Play + Revealed Clues)
        - Row 1: Bottom Area (Status Message + Compact Action Toolbar)
        """
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1, minsize=360)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        # ── Left: Board area ──
        self._board_container = ctk.CTkFrame(self, fg_color="transparent")
        self._board_container.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=(16, 8))

        # ── Right: Sidebar (How To Play + Revealed Clues) ──
        self._side_panel = ctk.CTkFrame(self, fg_color="transparent")
        self._side_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=(16, 8))

        # How to Play rules panel
        self._rules_panel = HowToPlayPanel(self._side_panel)
        self._rules_panel.pack(fill="x", pady=(0, 8))

        # Revealed clues panel
        self._clue_panel = CluePanel(
            self._side_panel,
            on_clue_click=self._on_clue_panel_click,
        )
        self._clue_panel.pack(fill="both", expand=True)

        # ── Bottom Bar: Status banner + Compact Action Toolbar ──
        self._bottom_bar = ctk.CTkFrame(self, fg_color="transparent")
        self._bottom_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 16))
        self._bottom_bar.grid_columnconfigure(0, weight=1)
        self._bottom_bar.grid_columnconfigure(1, weight=0)

        # Status message on bottom-left
        self._status = StatusMessage(self._bottom_bar)
        self._status.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        # Compact action toolbar on bottom-right
        self._toolbar = CompactActionToolbar(
            self._bottom_bar,
            on_hint=self._on_hint,
            on_auto_solve=self._on_auto_solve,
            on_restart=self._on_restart,
            on_load=self._on_load,
        )
        self._toolbar.grid(row=0, column=1, sticky="e")

    # ──────────────────────────────────────────────
    #  Board rendering
    # ──────────────────────────────────────────────
    def _refresh_board(self) -> None:
        """Re-create the entire board grid from the current public state."""
        public_state = self._engine.get_public_state()

        # Clear existing cards
        for card in self._cards.values():
            card.destroy()
        self._cards.clear()

        # Clear board container children
        for child in self._board_container.winfo_children():
            child.destroy()

        size = public_state.size
        pad_val = 5 if size == 3 else (3 if size == 4 else 2)

        # Title
        title_frame = ctk.CTkFrame(self._board_container, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 6))

        ctk.CTkButton(
            title_frame,
            text="← Levels",
            width=86,
            command=self._on_back,
            state="normal" if self._on_back else "disabled",
            fg_color="#3d3632",
            hover_color="#4a433e",
        ).pack(side="left", padx=(0, 12))

        ctk.CTkLabel(
            title_frame,
            text=f"🔍 {public_state.level_id.upper().replace('_', ' ')}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#ece5dd",
        ).pack(side="left", padx=(0, 12))

        ctk.CTkLabel(
            title_frame,
            text=f"Board: {size}×{size}",
            font=ctk.CTkFont(size=14),
            text_color="#8c8279",
        ).pack(side="left")

        ctk.CTkButton(
            title_frame,
            text="→",
            width=42,
            command=self._on_next,
            state="normal" if self._on_next else "disabled",
            fg_color="#3d3632",
            hover_color="#d4a574",
        ).pack(side="right", padx=(6, 0))
        ctk.CTkButton(
            title_frame,
            text="←",
            width=42,
            command=self._on_previous,
            state="normal" if self._on_previous else "disabled",
            fg_color="#3d3632",
            hover_color="#d4a574",
        ).pack(side="right")

        # Grid frame
        grid_frame = ctk.CTkFrame(self._board_container, fg_color="transparent")
        grid_frame.pack(expand=True)

        for i in range(size):
            grid_frame.grid_columnconfigure(i, weight=1, pad=pad_val)
            grid_frame.grid_rowconfigure(i, weight=1, pad=pad_val)

        # Build clue lookup
        clue_map: dict[str, Clue] = {}
        for clue in public_state.revealed_clues:
            clue_map[clue.owner_cell] = clue

        # Create cards
        for cell in public_state.cells:
            character = self._characters.get(cell.character_id)
            is_revealed = cell.id not in public_state.unresolved_cells
            verdict = public_state.proved_verdicts.get(cell.id)
            clue = clue_map.get(cell.id)

            card = CharacterCard(grid_frame, grid_size=size, on_click=self._on_card_click)
            card.set_data(cell.id, character, is_revealed, verdict, clue, grid_size=size)
            card.grid(
                row=cell.row - 1,
                column=cell.column - 1,
                padx=pad_val,
                pady=pad_val,
                sticky="nsew",
            )
            self._cards[cell.id] = card

        # Update clue panel
        self._clue_panel.update_clues(public_state.revealed_clues)

        # Reset active clue highlight
        self._highlighted_clue_id = None
        self._highlighted_cell = None

        # Update status
        if self._engine.is_solved():
            self._status.set_message("🎉 Congratulations! Case solved!", "success")
        else:
            unresolved = len(public_state.unresolved_cells)
            self._status.set_message(
                f"🔎 {unresolved} suspect(s) remaining. Click face-down card to declare verdict.",
                "info",
            )

    def _update_board_state(self) -> None:
        """Update existing cards without rebuilding the grid."""
        public_state = self._engine.get_public_state()

        clue_map: dict[str, Clue] = {}
        for clue in public_state.revealed_clues:
            clue_map[clue.owner_cell] = clue

        for cell in public_state.cells:
            card = self._cards.get(cell.id)
            if card is None:
                continue
            character = self._characters.get(cell.character_id)
            is_revealed = cell.id not in public_state.unresolved_cells
            verdict = public_state.proved_verdicts.get(cell.id)
            clue = clue_map.get(cell.id)
            card.set_data(cell.id, character, is_revealed, verdict, clue, grid_size=public_state.size)

        # Update clue panel
        self._clue_panel.update_clues(public_state.revealed_clues)

        # Re-apply active clue highlight if any
        if self._highlighted_clue_id:
            active_clue = next(
                (c for c in public_state.revealed_clues if c.id == self._highlighted_clue_id),
                None,
            )
            if active_clue:
                self._apply_clue_highlights(active_clue)
            else:
                self._clear_clue_highlights()

        # Update status
        if self._engine.is_solved():
            self._status.set_message("🎉 Congratulations! Case solved!", "success")

    # ──────────────────────────────────────────────
    #  Clue logic highlight computation
    # ──────────────────────────────────────────────
    def _compute_clue_highlights(self, clue: Clue) -> dict[str, str]:
        """Compute border colors for all cells related to a clue by logical rules."""
        highlights: dict[str, str] = {}
        public_state = self._engine.get_public_state()

        # Always highlight clue owner cell in Gold
        highlights[clue.owner_cell] = "#f39c12"

        ctype = clue.type
        cdata = clue.data

        if ctype == ClueType.FACT:
            person = cdata.get("person")
            status = str(cdata.get("status", "")).upper()
            if person:
                color = "#e74c3c" if status == "CRIMINAL" else "#2ecc71"
                highlights[person] = color

        elif ctype in (ClueType.SAME, ClueType.DIFFERENT):
            p1 = cdata.get("person1")
            p2 = cdata.get("person2")
            color = "#3498db" if ctype == ClueType.SAME else "#e67e22"
            if p1:
                highlights[p1] = color
            if p2:
                highlights[p2] = color

        elif ctype in (ClueType.EXACTLY, ClueType.AT_LEAST, ClueType.AT_MOST, ClueType.PARITY):
            raw_region = cdata.get("region")
            if isinstance(raw_region, dict):
                try:
                    region_obj = parse_region(raw_region)
                    region_cells = resolve_region(region_obj, public_state.cells)
                    for cid in region_cells:
                        if cid not in highlights:
                            highlights[cid] = "#f1c40f"
                except Exception:
                    pass

        elif ctype in (ClueType.EQUAL_COUNT, ClueType.COMPARE_COUNT):
            raw_regions = (
                (cdata.get("region1"), cdata.get("region2"))
                if ctype == ClueType.EQUAL_COUNT
                else (cdata.get("left_region"), cdata.get("right_region"))
            )
            for raw_region in raw_regions:
                if not isinstance(raw_region, dict):
                    continue
                try:
                    for cid in resolve_region(parse_region(raw_region), public_state.cells):
                        highlights.setdefault(cid, "#f1c40f")
                except Exception:
                    pass

        elif ctype == ClueType.CONNECTED:
            raw_region = cdata.get("region")
            if isinstance(raw_region, dict):
                try:
                    for cid in resolve_region(parse_region(raw_region), public_state.cells):
                        highlights.setdefault(cid, "#9b59b6")
                except Exception:
                    pass

        return highlights

    def _apply_clue_highlights(self, clue: Clue) -> None:
        """Light up borders of related cards according to clue logic, and reset unrelated cards."""
        highlights = self._compute_clue_highlights(clue)
        self._highlighted_clue_id = clue.id

        for cid, card in self._cards.items():
            if cid in highlights:
                card.set_highlighted(True, border_color=highlights[cid])
            else:
                card.set_highlighted(False)

        self._status.set_message(
            f"💡 Clue [{clue.owner_cell}]: \"{clue.display_text}\" — Related cards highlighted.",
            "info",
        )

    def _clear_clue_highlights(self) -> None:
        """Clear all clue highlights and reset card borders to standard."""
        self._highlighted_clue_id = None
        self._highlighted_cell = None
        for card in self._cards.values():
            card.set_highlighted(False)

    def _on_clue_panel_click(self, clue: Clue) -> None:
        """Handle clicking a clue row in the sidebar CluePanel."""
        if self._highlighted_clue_id == clue.id:
            self._clear_clue_highlights()
            self._status.set_message("Highlight cleared.", "info")
        else:
            self._apply_clue_highlights(clue)

    # ──────────────────────────────────────────────
    #  Card interaction & Popup
    # ──────────────────────────────────────────────
    def _on_card_click(self, cell_id: str) -> None:
        """Handle card click:
        - If face-down: open VerdictPopup to declare innocent/criminal.
        - If face-up with a clue: highlight/toggle related cards according to clue logic.
        """
        public_state = self._engine.get_public_state()
        cell_obj = next((c for c in public_state.cells if c.id == cell_id), None)
        if cell_obj is None:
            return

        character = self._characters.get(cell_obj.character_id)

        if cell_id in public_state.unresolved_cells:
            # Face-down card -> VerdictPopup
            if character is not None:
                VerdictPopup(
                    master=self,
                    cell_id=cell_id,
                    character=character,
                    on_verdict=self._submit_verdict_for_cell,
                )
        else:
            # Face-up card -> Check for revealed clue
            clue = next((c for c in public_state.revealed_clues if c.owner_cell == cell_id), None)
            if clue is not None:
                if self._highlighted_clue_id == clue.id:
                    self._clear_clue_highlights()
                    self._status.set_message("Highlight cleared.", "info")
                else:
                    self._apply_clue_highlights(clue)
            else:
                self._clear_clue_highlights()
                verdict = public_state.proved_verdicts.get(cell_id)
                name = character.name if character else cell_id
                self._status.set_message(
                    f"{name} [{cell_id}] is {verdict.value if verdict else '???'}.",
                    "info",
                )

    # ──────────────────────────────────────────────
    #  Verdict submission & Action handlers
    # ──────────────────────────────────────────────
    def _submit_verdict_for_cell(self, cell_id: str, verdict: Verdict) -> None:
        """Submit a verdict for a specific cell."""
        if self._engine.is_solved():
            self._status.set_message("✅ Game already solved!", "success")
            return

        try:
            response = self._engine.submit_verdict(cell_id, verdict)
        except NotImplementedError:
            self._status.set_message(
                "🔧 Logic Agent chưa sẵn sàng — CNF encoder chưa được implement.",
                "warning",
            )
            return
        except (KeyError, ValueError) as exc:
            self._status.set_message(f"❌ Error: {exc}", "error")
            return

        # Map result to message
        result_messages = {
            SubmissionResult.ACCEPTED: (
                f"✅ ACCEPTED! {cell_id} is {verdict.value}.",
                "success",
            ),
            SubmissionResult.NOT_PROVABLE: (
                f"⚠ NOT PROVABLE — Not enough information to prove {cell_id} is {verdict.value}.",
                "warning",
            ),
            SubmissionResult.CONTRADICTED: (
                f"❌ CONTRADICTED — Logic proves {cell_id} is {response.proved_verdict.value if response.proved_verdict else '???'}, not {verdict.value}.",
                "error",
            ),
            SubmissionResult.INCONSISTENT: (
                "💀 INCONSISTENT — The knowledge base has a contradiction!",
                "error",
            ),
        }
        msg, level = result_messages.get(
            response.result, (response.message, "info")
        )
        self._status.set_message(msg, level)

        # Refresh board after submission
        self._update_board_state()

    def _on_restart(self) -> None:
        """Restart the game and refresh the board."""
        self._engine.restart()
        self._clear_clue_highlights()
        self._auto_solving = False
        self._update_board_state()
        self._status.set_message("🔄 Game restarted!", "info")

    def _on_hint(self) -> None:
        """Get a hint from the agent and highlight the suggested card."""
        if self._engine.is_solved():
            self._status.set_message("✅ Game already solved!", "success")
            return

        try:
            move = self._engine.get_hint()
        except NotImplementedError:
            self._status.set_message(
                "🔧 Hint chưa khả dụng — Logic Agent chưa sẵn sàng.",
                "warning",
            )
            return
        except (ValueError, Exception) as exc:
            self._status.set_message(f"❌ Hint error: {exc}", "error")
            return

        if move is None:
            self._status.set_message(
                "🤔 No forced move found. Try revealing more clues!",
                "warning",
            )
            return

        # Clear previous clue highlight
        self._clear_clue_highlights()

        # Highlight the suggested card in Amber
        self._highlighted_cell = move.cell_id
        card = self._cards.get(move.cell_id)
        if card:
            card.set_highlighted(True, border_color="#f39c12")

        char = self._characters.get(
            next(
                (c.character_id for c in self._engine.get_public_state().cells if c.id == move.cell_id),
                "",
            )
        )
        name = char.name if char else move.cell_id
        self._status.set_message(
            f"💡 Hint: {name} [{move.cell_id}] → {move.verdict.value}",
            "info",
        )

    def _on_auto_solve(self) -> None:
        """Auto-solve one step at a time with visual delay."""
        if self._engine.is_solved():
            self._status.set_message("✅ Game already solved!", "success")
            return

        if self._auto_solving:
            self._auto_solving = False
            self._status.set_message("⏸ Auto-solve paused.", "warning")
            return

        self._auto_solving = True
        self._status.set_message("⚡ Auto-solving...", "info")
        self._auto_solve_step()

    def _auto_solve_step(self) -> None:
        """Execute one auto-solve step and schedule the next."""
        if not self._auto_solving or self._engine.is_solved():
            self._auto_solving = False
            if self._engine.is_solved():
                self._status.set_message("🎉 Auto-solve complete! Case solved!", "success")
            return

        try:
            response = self._engine.auto_solve_step()
        except NotImplementedError:
            self._auto_solving = False
            self._status.set_message(
                "🔧 Auto-solve chưa khả dụng — Logic Agent chưa sẵn sàng.",
                "warning",
            )
            return
        except Exception as exc:
            self._auto_solving = False
            self._status.set_message(f"❌ Auto-solve error: {exc}", "error")
            return

        if response is None:
            self._auto_solving = False
            self._status.set_message(
                "🤔 Auto-solve stopped — no more forced moves.",
                "warning",
            )
            return

        self._update_board_state()
        self._status.set_message(
            f"⚡ Solved {response.cell_id} → {response.submitted_verdict.value}",
            "success",
        )

        # Schedule next step with delay for visual feedback
        self.after(600, self._auto_solve_step)

    def _on_load(self) -> None:
        """Open a file dialog to load a new level."""
        filepath = filedialog.askopenfilename(
            title="Load Level",
            filetypes=[("JSON files", "*.json")],
            initialdir="data/levels",
        )
        if not filepath:
            return

        try:
            from game.level_loader import load_level
            from game.level_validator import validate_level
            from game.game_engine import GameEngine

            level = load_level(filepath)
            validate_level(level)
            self._engine = GameEngine(level)

            self._clear_clue_highlights()
            self._auto_solving = False

            self._refresh_board()
            self._status.set_message(
                f"📂 Loaded: {Path(filepath).stem}",
                "success",
            )

            if self._on_level_loaded:
                self._on_level_loaded(self._engine)

        except Exception as exc:
            self._status.set_message(f"❌ Load error: {exc}", "error")

    # ──────────────────────────────────────────────
    #  Public API for external engine swap
    # ──────────────────────────────────────────────
    def set_engine(self, engine: "GameEngine") -> None:
        """Replace the game engine and refresh the board."""
        self._engine = engine
        self._clear_clue_highlights()
        self._auto_solving = False
        self._refresh_board()
