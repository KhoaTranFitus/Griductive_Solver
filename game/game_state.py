# game/game_state.py
from dataclasses import dataclass, field

from core.enums import Verdict


@dataclass
class GameState:
    revealed_cells: set[str] = field(default_factory=set)
    proved_verdicts: dict[str, Verdict] = field(default_factory=dict)
    reveal_order: list[str] = field(default_factory=list)
    selected_cell: str | None = None
    solved: bool = False

    def __post_init__(self) -> None:
        """Recover a stable order for callers using the legacy constructor."""
        seen = set(self.reveal_order)
        self.reveal_order.extend(
            cell_id
            for cell_id in self.proved_verdicts
            if cell_id in self.revealed_cells and cell_id not in seen
        )
        seen.update(self.reveal_order)
        self.reveal_order.extend(sorted(self.revealed_cells - seen))

    def is_revealed(self, cell_id: str) -> bool:
        return cell_id in self.revealed_cells

    def is_resolved(self, cell_id: str) -> bool:
        return cell_id in self.proved_verdicts

    def reveal_cell(
        self,
        cell_id: str,
        verdict: Verdict,
    ) -> None:
        if verdict not in {
            Verdict.CRIMINAL,
            Verdict.INNOCENT,
        }:
            raise ValueError(
                "A revealed cell must be CRIMINAL or INNOCENT."
            )

        if cell_id not in self.revealed_cells:
            self.reveal_order.append(cell_id)
        self.revealed_cells.add(cell_id)
        self.proved_verdicts[cell_id] = verdict

    def reset(
        self,
        initial_revealed: tuple[str, ...],
        initial_verdicts: dict[str, Verdict],
    ) -> None:
        self.revealed_cells = set(initial_revealed)
        self.reveal_order = list(initial_revealed)
        self.proved_verdicts = dict(initial_verdicts)
        self.selected_cell = None
        self.solved = False
