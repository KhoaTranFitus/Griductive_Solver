# game/game_state.py
from dataclasses import dataclass, field

from core.enums import Verdict


@dataclass
class GameState:
    revealed_cells: set[str] = field(default_factory=set)
    proved_verdicts: dict[str, Verdict] = field(default_factory=dict)
    selected_cell: str | None = None
    solved: bool = False

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

        self.revealed_cells.add(cell_id)
        self.proved_verdicts[cell_id] = verdict

    def reset(
        self,
        initial_revealed: tuple[str, ...],
        initial_verdicts: dict[str, Verdict],
    ) -> None:
        self.revealed_cells = set(initial_revealed)
        self.proved_verdicts = dict(initial_verdicts)
        self.selected_cell = None
        self.solved = False