# gui/game_screen.py
"""Main game screen that assembles the board grid, clue panel, how to play guide,
bottom action toolbar, and status message into a cohesive layout.

The GameScreen communicates with the GameEngine exclusively through its public
interface (``get_public_state``, ``submit_verdict``, ``restart``, ``is_solved``,
``get_hint``, ``auto_solve_step``). It never accesses hidden solution data.
"""

from __future__ import annotations

import tkinter.filedialog as filedialog
import threading
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
    NotProvablePopup,
    StatusMessage,
    VerdictPopup,
    VictoryPopup,
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
        display_level_number: int | None = None,
        on_level_loaded: "callable | None" = None,
        on_back: "callable | None" = None,
        on_previous: "callable | None" = None,
        on_next: "callable | None" = None,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="#221e1d", **kwargs)

        self._engine = engine
        self._characters = dict(characters)
        self._display_level_number = display_level_number
        self._on_level_loaded = on_level_loaded
        self._on_back = on_back
        self._on_previous = on_previous
        self._on_next = on_next
        self._highlighted_clue_id: str | None = None
        self._highlighted_cell: str | None = None
        self._cards: dict[str, CharacterCard] = {}
        self._auto_solving: bool = False
        self._auto_worker_running: bool = False
        self._auto_worker_result = None
        self._auto_worker_error: Exception | None = None

        # Timer & Victory tracking
        self._elapsed_seconds: int = 0
        self._timer_running: bool = False
        self._timer_job: str | None = None
        self._victory_shown: bool = False

        self._build_layout()
        self._refresh_board()
        self._start_timer()

    # ──────────────────────────────────────────────
    #  Timer management
    # ──────────────────────────────────────────────
    def _start_timer(self) -> None:
        self._stop_timer()
        self._elapsed_seconds = 0
        self._timer_running = True
        self._update_timer_label()
        self._schedule_timer_tick()

    def _stop_timer(self) -> None:
        self._timer_running = False
        if hasattr(self, "_timer_job") and self._timer_job is not None:
            try:
                self.after_cancel(self._timer_job)
            except Exception:
                pass
            self._timer_job = None

    def _schedule_timer_tick(self) -> None:
        if self._timer_running:
            self._timer_job = self.after(1000, self._on_timer_tick)

    def _on_timer_tick(self) -> None:
        if not self._timer_running:
            return
        self._elapsed_seconds += 1
        self._update_timer_label()
        self._schedule_timer_tick()

    def _update_timer_label(self) -> None:
        m = self._elapsed_seconds // 60
        s = self._elapsed_seconds % 60
        if hasattr(self, "_lbl_timer"):
            self._lbl_timer.configure(text=f"⏱ {m:02d}:{s:02d}")

    # ──────────────────────────────────────────────
    #  Layout construction
    # ──────────────────────────────────────────────
    def _build_layout(self) -> None:
        """Create clean minimalist 2-column layout:
        - Left Column (weight=3): Control Bar at top, Scrollable Grid in middle, Status at bottom.
        - Right Column (weight=2): Title, Level indicator, Date, Timer, How to Play, Revealed Clues.
        """
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # ── Left Column: Game Board & Integrated Controls ──
        self._left_panel = ctk.CTkFrame(self, fg_color="transparent")
        self._left_panel.grid(row=0, column=0, sticky="nsew", padx=(20, 8), pady=16)
        self._left_panel.grid_columnconfigure(0, weight=1)
        self._left_panel.grid_rowconfigure(1, weight=1)

        # Top Integrated Control Bar
        self._top_bar = ctk.CTkFrame(self._left_panel, fg_color="transparent")
        self._top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Level Navigation (Back, Badge, Prev/Next) on left of top bar
        ctk.CTkButton(
            self._top_bar, text="← Levels", width=85, height=32, corner_radius=8,
            command=self._on_back if self._on_back else lambda: None,
            fg_color="#3d3632", hover_color="#4a433e", font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left", padx=(0, 10))

        self._lbl_level_badge = ctk.CTkLabel(
            self._top_bar, text="LEVEL 01 · 3×3",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#d4a574", fg_color="#2d2926", corner_radius=8, padx=12, pady=4,
        )
        self._lbl_level_badge.pack(side="left", padx=(0, 6))

        self._btn_prev = ctk.CTkButton(
            self._top_bar, text="←", width=34, height=32, corner_radius=8,
            command=self._on_previous, state="normal" if self._on_previous else "disabled",
            fg_color="#3d3632", hover_color="#d4a574", font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._btn_prev.pack(side="left", padx=(2, 2))

        self._btn_next = ctk.CTkButton(
            self._top_bar, text="→", width=34, height=32, corner_radius=8,
            command=self._on_next, state="normal" if self._on_next else "disabled",
            fg_color="#3d3632", hover_color="#d4a574", font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._btn_next.pack(side="left", padx=(0, 12))

        # Action Buttons (Hint, Auto Solve, Restart, Load) on right of top bar
        action_row = ctk.CTkFrame(self._top_bar, fg_color="transparent")
        action_row.pack(side="right")

        buttons = [
            ("💡 Hint",       "#6c3d8f", "#7d4ea0", self._on_hint),
            ("⚡ Auto Solve", "#8f6c2d", "#a07d3e", self._on_auto_solve),
            ("↻ Restart",    "#2c3e50", "#34495e", self._on_restart),
            ("📂 Load",       "#1a5e50", "#238b76", self._on_load),
        ]
        for text, fg, hover, cmd in buttons:
            ctk.CTkButton(
                action_row, text=text, font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=fg, hover_color=hover, width=88, height=32, corner_radius=8,
                command=cmd,
            ).pack(side="left", padx=3)

        # Center Area: Scrollable Board Container
        self._board_container = ctk.CTkScrollableFrame(
            self._left_panel, fg_color="transparent",
            scrollbar_button_color="#3a3430", scrollbar_button_hover_color="#8c8279",
        )
        self._board_container.grid(row=1, column=0, sticky="nsew")

        # Bottom Area: Status banner
        self._status = StatusMessage(self._left_panel)
        self._status.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        # ── Right Column: Info & Instructions (Direct on background) ──
        self._side_panel = ctk.CTkFrame(self, fg_color="transparent")
        self._side_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 20), pady=16)

        # Title Block Header Row with Timer on top right!
        header_row = ctk.CTkFrame(self._side_panel, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, 2))

        ctk.CTkLabel(
            header_row, text="GRIDUCTIVE",
            font=ctk.CTkFont(size=24, weight="bold"), text_color="#d4a574",
        ).pack(side="left")

        self._lbl_timer = ctk.CTkLabel(
            header_row, text="⏱ 00:00",
            font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
            text_color="#d4a574", fg_color="#2d2926", corner_radius=6,
            padx=8, pady=2,
        )
        self._lbl_timer.pack(side="right")

        self._lbl_side_level = ctk.CTkLabel(
            self._side_panel, text="LEVEL 01  ·  Board: 3×3",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#ece5dd",
        )
        self._lbl_side_level.pack(anchor="w", pady=(0, 2))

        # Current date display
        from datetime import datetime
        current_date_str = datetime.now().strftime("%B %d, %Y")
        ctk.CTkLabel(
            self._side_panel, text=current_date_str,
            font=ctk.CTkFont(size=11), text_color="#8c8279",
        ).pack(anchor="w", pady=(0, 10))

        # Separator line
        ctk.CTkFrame(self._side_panel, height=1, fg_color="#3a3430").pack(fill="x", pady=(0, 10))

        # How to Play rules panel
        self._rules_panel = HowToPlayPanel(self._side_panel)
        self._rules_panel.pack(fill="x", pady=(0, 10))

        # Separator line
        ctk.CTkFrame(self._side_panel, height=1, fg_color="#3a3430").pack(fill="x", pady=(0, 10))

        # Revealed clues panel
        self._clue_panel = CluePanel(
            self._side_panel,
            on_clue_click=self._on_clue_panel_click,
            characters={},
        )
        self._clue_panel.pack(fill="both", expand=True)

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

        # Update header & sidebar info
        level_text = (
            f"LEVEL {self._display_level_number}"
            if self._display_level_number is not None
            else public_state.level_id.upper().replace("_", " ")
        )
        board_text = f"Board: {size}×{size}"
        self._lbl_level_badge.configure(text=level_text)
        self._lbl_side_level.configure(text=f"{level_text}  ·  {board_text}")

        # Update nav button states
        if hasattr(self, "_btn_prev") and self._btn_prev:
            self._btn_prev.configure(state="normal" if self._on_previous else "disabled")
        if hasattr(self, "_btn_next") and self._btn_next:
            self._btn_next.configure(state="normal" if self._on_next else "disabled")

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

        # Build cell → Character mapping for clue owner labels
        cell_char_map = {}
        for cell in public_state.cells:
            char = self._characters.get(cell.character_id)
            if char:
                cell_char_map[cell.id] = char

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

        # Update clue panel with character name mapping
        self._clue_panel._characters = cell_char_map
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

        # Update status & check victory modal
        if self._engine.is_solved():
            self._stop_timer()
            self._status.set_message("🎉 Congratulations! Case solved!", "success")
            if not self._victory_shown:
                self._victory_shown = True
                VictoryPopup(
                    master=self,
                    elapsed_seconds=self._elapsed_seconds,
                    on_restart=self._on_restart,
                    on_next=self._on_next,
                    on_back=self._on_back,
                )
        else:
            unresolved = len(public_state.unresolved_cells)
            self._status.set_message(
                f"🔎 {unresolved} suspect(s) remaining. Click face-down card to declare verdict.",
                "info",
            )

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
                cdata.get("region1", cdata.get("left_region")),
                cdata.get("region2", cdata.get("right_region")),
            )
            region_colors = ("#3498db", "#e67e22")
            for raw_region, color in zip(raw_regions, region_colors):
                if not isinstance(raw_region, dict):
                    continue
                try:
                    for cid in resolve_region(parse_region(raw_region), public_state.cells):
                        # A cell shared by both regions is shown in purple.
                        if cid in highlights and cid != clue.owner_cell:
                            highlights[cid] = "#9b59b6"
                        else:
                            highlights.setdefault(cid, color)
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

        elif ctype == ClueType.COUNT_PROPERTY:
            raw_region = cdata.get("subject_region")
            if isinstance(raw_region, dict):
                try:
                    subject_ids = resolve_region(parse_region(raw_region), public_state.cells)
                    for cid in subject_ids:
                        highlights.setdefault(cid, "#9b59b6")

                    prop = cdata.get("property", {})
                    if prop.get("type") == "NEIGHBOR_COUNT":
                        for subject_id in subject_ids:
                            neighbor_region = {
                                "type": "NEIGHBORS",
                                "center": subject_id,
                            }
                            for cid in resolve_region(
                                parse_region(neighbor_region), public_state.cells
                            ):
                                highlights.setdefault(cid, "#f1c40f")
                except Exception:
                    pass

        return highlights

    def _apply_clue_highlights(self, clue: Clue) -> None:
        """Light up borders of related cards according to clue logic, and reset unrelated cards."""
        highlights = self._compute_clue_highlights(clue)
        self._highlighted_clue_id = clue.id
        self._clue_panel.set_active_clue(clue.id)

        for cid, card in self._cards.items():
            if cid in highlights:
                card.set_highlighted(True, border_color=highlights[cid])
            else:
                card.set_highlighted(False)

        owner_name = clue.owner_cell
        char = self._characters.get(clue.owner_cell)
        if char and hasattr(char, "name"):
            owner_name = char.name

        self._status.set_message(
            f"💡 Clue [{owner_name}]: \"{clue.display_text}\" — Related cards highlighted.",
            "info",
        )

    def _clear_clue_highlights(self) -> None:
        """Clear all clue highlights and reset card borders to standard."""
        self._highlighted_clue_id = None
        self._highlighted_cell = None
        self._clue_panel.set_active_clue(None)
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
        - If face-down (unresolved): open VerdictPopup to declare innocent/criminal.
        - If face-up (solved/revealed) with a clue: highlight/toggle related cards according to clue logic.
        - If face-up (solved/revealed) without a clue: display character info, DO NOT open VerdictPopup.
        """
        public_state = self._engine.get_public_state()
        cell_obj = next((c for c in public_state.cells if c.id == cell_id), None)
        if cell_obj is None:
            return

        character = self._characters.get(cell_obj.character_id)

        if cell_id in public_state.unresolved_cells:
            # Face-down card -> VerdictPopup
            if character is not None and not self._engine.is_solved():
                VerdictPopup(
                    master=self,
                    cell_id=cell_id,
                    character=character,
                    on_verdict=self._submit_verdict_for_cell,
                )
        else:
            # Face-up (solved) card -> NEVER open VerdictPopup
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
                verdict_str = verdict.value if verdict else "REVEALED"
                self._status.set_message(
                    f"ℹ️ {name} [{cell_id}] is already solved as {verdict_str}.",
                    "info",
                )

    # ──────────────────────────────────────────────
    #  Verdict submission & Action handlers
    # ──────────────────────────────────────────────
    def _get_character_name_for_cell(self, cell_id: str) -> str:
        """Resolve human-readable character name for a cell coordinate."""
        cell_obj = next((c for c in self._engine.get_public_state().cells if c.id == cell_id), None)
        if cell_obj:
            char = self._characters.get(cell_obj.character_id)
            if char and hasattr(char, "name"):
                return char.name
        return cell_id

    def _submit_verdict_for_cell(self, cell_id: str, verdict: Verdict) -> None:
        """Submit a verdict for a specific cell and present clean feedback."""
        if self._engine.is_solved():
            self._status.set_message("🎉 Congratulations! Case already solved!", "success")
            return

        try:
            response = self._engine.submit_verdict(cell_id, verdict)
        except Exception as exc:
            self._status.set_message(f"❌ Error evaluating verdict: {exc}", "error")
            return

        name = self._get_character_name_for_cell(cell_id)

        if response.result == SubmissionResult.ACCEPTED:
            self._status.set_message(
                f"✅ ACCEPTED — Verdict confirmed! {name} [{cell_id}] is {verdict.value}.",
                "success",
            )
        elif response.result == SubmissionResult.NOT_PROVABLE:
            self._status.set_message(
                f"⚠️ NOT PROVABLE — Not enough evidence yet to prove {name} [{cell_id}] is {verdict.value}.",
                "warning",
            )
            NotProvablePopup(
                master=self,
                character_name=name,
                verdict=verdict.value,
            )
        elif response.result == SubmissionResult.CONTRADICTED:
            proved = response.proved_verdict.value if response.proved_verdict else "different"
            self._status.set_message(
                f"❌ CONTRADICTED — Evidence proves {name} [{cell_id}] is {proved}, not {verdict.value}!",
                "error",
            )
        elif response.result == SubmissionResult.INCONSISTENT:
            self._status.set_message(
                "💀 INCONSISTENT — The knowledge base contains a contradiction!",
                "error",
            )
        else:
            self._status.set_message(response.message or "Verdict processed.", "info")

        self._update_board_state()

    def _on_restart(self) -> None:
        """Restart the game and fully reset board, clue list, highlights, timer, and status."""
        self._auto_solving = False
        self._engine.restart()
        self._highlighted_clue_id = None
        self._highlighted_cell = None
        self._victory_shown = False
        self._clear_clue_highlights()
        self._refresh_board()
        self._start_timer()
        self._status.set_message("🔄 Game restarted! All progress reset.", "info")

    def _on_hint(self) -> None:
        """Get a hint from the agent and highlight the suggested card."""
        if self._engine.is_solved():
            self._status.set_message("🎉 Congratulations! Case already solved!", "success")
            return

        try:
            move = self._engine.get_hint()
        except Exception as exc:
            self._status.set_message(f"❌ Hint error: {exc}", "error")
            return

        if move is None:
            self._status.set_message(
                "🤔 No forced deduction available. Try revealing more clues!",
                "warning",
            )
            return

        self._clear_clue_highlights()

        self._highlighted_cell = move.cell_id
        card = self._cards.get(move.cell_id)
        if card:
            card.set_highlighted(True, border_color="#f39c12")

        name = self._get_character_name_for_cell(move.cell_id)

        self._status.set_message(
            f"💡 Hint: {name} [{move.cell_id}] → {move.verdict.value}",
            "info",
        )

    def _on_auto_solve(self) -> None:
        """Auto-solve step-by-step with visual reveal delay."""
        if self._engine.is_solved():
            self._status.set_message("🎉 Congratulations! Case already solved!", "success")
            return

        if self._auto_solving:
            self._auto_solving = False
            self._status.set_message("⏸ Auto-solve paused.", "warning")
            return

        self._auto_solving = True
        self._status.set_message("⚡ Auto-solving step-by-step...", "info")
        self._auto_solve_step()

    def _auto_solve_step(self) -> None:
        """Execute one auto-solve step and animate the next."""
        if not self.winfo_exists() or not self._auto_solving or self._engine.is_solved():
            self._auto_solving = False
            if self._engine.is_solved():
                self._status.set_message("🎉 Auto-solve complete! Case solved!", "success")
            return

        if self._auto_worker_running:
            return

        # SAT search can take seconds on larger boards. Keep it off Tk's event
        # thread so painting, dragging and the timer remain responsive.
        self._auto_worker_running = True
        self._auto_worker_result = None
        self._auto_worker_error = None

        def find_move() -> None:
            try:
                self._auto_worker_result = self._engine.get_hint()
            except Exception as exc:
                self._auto_worker_error = exc
            finally:
                self._auto_worker_running = False

        threading.Thread(target=find_move, daemon=True).start()
        self.after(40, self._poll_auto_solve_result)

    def _poll_auto_solve_result(self) -> None:
        """Consume a background SAT result from Tk's event thread."""
        if self._auto_worker_running:
            if self.winfo_exists():
                self.after(40, self._poll_auto_solve_result)
            return

        if not self.winfo_exists() or not self._auto_solving:
            return
        if self._auto_worker_error is not None:
            self._auto_solving = False
            self._status.set_message(
                f"❌ Auto-solve error: {self._auto_worker_error}", "error"
            )
            return

        move = self._auto_worker_result
        response = self._engine.auto_solve_step(move) if move is not None else None

        if response is None:
            self._auto_solving = False
            self._status.set_message(
                "🤔 Auto-solve paused — no more forced deductions available.",
                "warning",
            )
            return

        self._update_board_state()

        name = self._get_character_name_for_cell(response.cell_id)

        self._status.set_message(
            f"⚡ Solved: {name} [{response.cell_id}] → {response.submitted_verdict.value}",
            "success",
        )

        # Schedule next step for smooth animated reveal
        if self.winfo_exists() and self._auto_solving:
            self.after(600, self._auto_solve_step)

    def _on_load(self) -> None:
        """Open a file dialog to load a new level and reset state cleanly."""
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

            self._highlighted_clue_id = None
            self._highlighted_cell = None
            self._auto_solving = False
            self._victory_shown = False

            self._refresh_board()
            self._start_timer()
            self._status.set_message(
                f"📂 Loaded level: {Path(filepath).stem}",
                "success",
            )

            if self._on_level_loaded:
                self._on_level_loaded(self._engine)

        except Exception as exc:
            self._status.set_message(f"❌ Load level error: {exc}", "error")

    # ──────────────────────────────────────────────
    #  Public API for external engine swap
    # ──────────────────────────────────────────────
    def set_engine(self, engine: "GameEngine") -> None:
        """Replace the game engine and refresh the board state and timer."""
        self._engine = engine
        self._clear_clue_highlights()
        self._auto_solving = False
        self._victory_shown = False
        self._refresh_board()
        self._start_timer()
