"""Public interface for the deductive game agent.

The first integration version intentionally accepts ``PublicState`` only.
Implementations must build their knowledge base from revealed clues and proved
verdicts, never from a ``Level`` or its hidden solution.
"""

from core.enums import Verdict
from core.models import AgentMove, PublicState
from logic.dpll import DPLLSolver


class DeductiveAgent:
    """Classify unresolved cells and choose only logically forced moves.

    The method bodies remain integration points until Member 1's public CNF
    encoder and variable-map functions are available. Their signatures and
    behavior are stable for callers such as ``GameEngine`` and the GUI.
    """

    def __init__(
        self,
        solver: DPLLSolver | None = None,
    ) -> None:
        """Create an agent, optionally using an injected solver for tests."""
        self._solver = solver if solver is not None else DPLLSolver()

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
        raise NotImplementedError(
            "DeductiveAgent requires the shared CNF encoder and VariableMap."
        )

    def choose_next_move(
        self,
        public_state: PublicState,
    ) -> AgentMove | None:
        """Return the first forced move in public row-major order.

        Return ``None`` when the puzzle is solved, all unresolved cells are
        UNKNOWN, or the knowledge base is inconsistent. Never return a move
        whose verdict is UNKNOWN or INCONSISTENT.
        """
        raise NotImplementedError(
            "DeductiveAgent requires the shared CNF encoder and VariableMap."
        )
