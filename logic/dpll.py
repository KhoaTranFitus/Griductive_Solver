# logic/dpll.py
from dataclasses import dataclass
from enum import Enum

from core.models import SolverStatistics


class ClauseState(str, Enum):
    """Possible states of a CNF clause under a partial assignment."""

    SATISFIED = "SATISFIED"
    UNRESOLVED = "UNRESOLVED"
    UNIT = "UNIT"
    CONFLICT = "CONFLICT"


@dataclass(frozen=True)
class ClauseAnalysis:
    """Result of evaluating one clause under a partial assignment."""

    state: ClauseState
    unit_literal: int | None = None


@dataclass(frozen=True)
class SolverResult:
    """Result and statistics returned by a completed SAT solver run."""

    satisfiable: bool
    assignment: dict[int, bool] | None
    decisions: int
    propagations: int
    backtracks: int
    runtime_ms: float


class DPLLSolver:
    """Foundation for the project's dependency-free DPLL SAT solver."""

    def solve(
        self,
        clauses: list[list[int]],
        assumptions: list[int] | None = None,
    ) -> SolverResult:
        """Solve a CNF formula once the full DPLL algorithm is implemented."""
        raise NotImplementedError(
            "Full DPLL solving is not implemented yet."
        )

    @staticmethod
    def _evaluate_literal(
        literal: int,
        assignment: dict[int, bool],
    ) -> bool | None:
        """Evaluate a signed literal without changing the assignment."""
        if literal == 0:
            raise ValueError("Literal 0 is invalid.")

        variable_id = abs(literal)

        if variable_id not in assignment:
            return None

        variable_value = assignment[variable_id]
        return variable_value if literal > 0 else not variable_value

    @classmethod
    def _analyze_clause(
        cls,
        clause: list[int],
        assignment: dict[int, bool],
    ) -> ClauseAnalysis:
        """Classify a clause without changing the clause or assignment."""
        if any(literal == 0 for literal in clause):
            raise ValueError("Clause cannot contain literal 0.")

        if not clause:
            return ClauseAnalysis(ClauseState.CONFLICT)

        distinct_literals: list[int] = []
        seen_literals: set[int] = set()

        for literal in clause:
            if -literal in seen_literals:
                return ClauseAnalysis(ClauseState.SATISFIED)

            if literal not in seen_literals:
                seen_literals.add(literal)
                distinct_literals.append(literal)

        unassigned_literals: list[int] = []

        for literal in distinct_literals:
            literal_value = cls._evaluate_literal(literal, assignment)

            if literal_value is True:
                return ClauseAnalysis(ClauseState.SATISFIED)

            if literal_value is None:
                unassigned_literals.append(literal)

        if not unassigned_literals:
            return ClauseAnalysis(ClauseState.CONFLICT)

        if len(unassigned_literals) == 1:
            return ClauseAnalysis(
                ClauseState.UNIT,
                unit_literal=unassigned_literals[0],
            )

        return ClauseAnalysis(ClauseState.UNRESOLVED)
