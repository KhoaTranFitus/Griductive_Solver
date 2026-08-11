"""Public interface for the deductive game agent.

The first integration version intentionally accepts ``PublicState`` only.
Implementations must build their knowledge base from revealed clues and proved
verdicts, never from a ``Level`` or its hidden solution.
"""

from core.enums import Verdict
from core.models import AgentMove, PublicState
from logic.cnf_encoder import build_knowledge_base
from logic.dpll import DPLLSolver
from logic.entailment import classify_character
from logic.variable_map import VariableMap


class DeductiveAgent:
    """Classify unresolved cells and choose only logically forced moves.

    A fresh variable map and knowledge base are built from the public state for
    each request.  This keeps the agent stateless and prevents hidden level
    data from leaking into deductions.
    """

    def __init__(
        self,
        solver: DPLLSolver | None = None,
    ) -> None:
        """Create an agent, optionally using an injected solver for tests."""
        self._solver = solver if solver is not None else DPLLSolver()

    @staticmethod
    def _row_major_unresolved_cells(
        public_state: PublicState,
    ) -> tuple[str, ...]:
        """Return public unresolved IDs ordered by their cell coordinates."""
        positions = {
            cell.id: (cell.row, cell.column)
            for cell in public_state.cells
        }
        return tuple(sorted(
            public_state.unresolved_cells,
            key=positions.__getitem__,
        ))

    def classify_all(
        self,
        public_state: PublicState,
    ) -> dict[str, Verdict]:
        """Classify every unresolved cell in public row-major order.

        The returned mapping must contain exactly the IDs in
        ``public_state.unresolved_cells``. A consistent knowledge base maps
        each ID to CRIMINAL, INNOCENT, or UNKNOWN. If the knowledge base is
        inconsistent, every unresolved ID maps to INCONSISTENT.
        """
        unresolved_cells = self._row_major_unresolved_cells(public_state)
        if not unresolved_cells:
            return {}

        variable_map = VariableMap(public_state.cells)
        knowledge_base = build_knowledge_base(
            public_state.revealed_clues,
            public_state.proved_verdicts,
            public_state.cells,
            variable_map,
        )

        classifications: dict[str, Verdict] = {}
        for cell_id in unresolved_cells:
            verdict = classify_character(
                knowledge_base,
                variable_map.get_variable(cell_id),
                self._solver,
            )
            if verdict is Verdict.INCONSISTENT:
                return {
                    unresolved_id: Verdict.INCONSISTENT
                    for unresolved_id in unresolved_cells
                }
            classifications[cell_id] = verdict

        return classifications

    def choose_next_move(
        self,
        public_state: PublicState,
    ) -> AgentMove | None:
        """Return the first forced move in public row-major order.

        Return ``None`` when the puzzle is solved, all unresolved cells are
        UNKNOWN, or the knowledge base is inconsistent. Never return a move
        whose verdict is UNKNOWN or INCONSISTENT.
        """
        classifications = self.classify_all(public_state)

        for cell_id in self._row_major_unresolved_cells(public_state):
            verdict = classifications[cell_id]
            if verdict in {Verdict.CRIMINAL, Verdict.INNOCENT}:
                return AgentMove(cell_id=cell_id, verdict=verdict)

        return None
