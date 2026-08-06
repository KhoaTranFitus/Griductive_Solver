# logic/dpll.py
import time
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
        """Solve a CNF formula with temporary literal assumptions."""
        start_time = time.perf_counter()
        statistics = SolverStatistics()
        assumption_literals = assumptions if assumptions is not None else []
        variable_ids: set[int] = set()

        for clause in clauses:
            for literal in clause:
                if literal == 0:
                    raise ValueError("Clause cannot contain literal 0.")

                variable_ids.add(abs(literal))

        for literal in assumption_literals:
            if literal == 0:
                raise ValueError("Assumptions cannot contain literal 0.")

            variable_ids.add(abs(literal))

        initial_assignment: dict[int, bool] = {}

        for literal in assumption_literals:
            variable_id = abs(literal)
            required_value = literal > 0

            if variable_id not in initial_assignment:
                initial_assignment[variable_id] = required_value
                continue

            if initial_assignment[variable_id] != required_value:
                runtime_ms = (time.perf_counter() - start_time) * 1000
                return SolverResult(
                    satisfiable=False,
                    assignment=None,
                    decisions=statistics.decisions,
                    propagations=statistics.propagations,
                    backtracks=statistics.backtracks,
                    runtime_ms=runtime_ms,
                )

        result = self._dpll(
            clauses,
            initial_assignment,
            statistics,
        )

        if result is None:
            runtime_ms = (time.perf_counter() - start_time) * 1000
            return SolverResult(
                satisfiable=False,
                assignment=None,
                decisions=statistics.decisions,
                propagations=statistics.propagations,
                backtracks=statistics.backtracks,
                runtime_ms=runtime_ms,
            )

        complete_assignment = {
            variable_id: result.get(variable_id, False)
            for variable_id in sorted(variable_ids)
        }

        runtime_ms = (time.perf_counter() - start_time) * 1000
        return SolverResult(
            satisfiable=True,
            assignment=complete_assignment,
            decisions=statistics.decisions,
            propagations=statistics.propagations,
            backtracks=statistics.backtracks,
            runtime_ms=runtime_ms,
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

    @classmethod
    def _has_conflict(
        cls,
        clauses: list[list[int]],
        assignment: dict[int, bool],
    ) -> bool:
        """Return whether any clause conflicts with the assignment."""
        return any(
            cls._analyze_clause(clause, assignment).state
            is ClauseState.CONFLICT
            for clause in clauses
        )

    @classmethod
    def _all_clauses_satisfied(
        cls,
        clauses: list[list[int]],
        assignment: dict[int, bool],
    ) -> bool:
        """Return whether every clause is satisfied by the assignment."""
        return all(
            cls._analyze_clause(clause, assignment).state
            is ClauseState.SATISFIED
            for clause in clauses
        )

    @classmethod
    def _find_unit_literal(
        cls,
        clauses: list[list[int]],
        assignment: dict[int, bool],
    ) -> int | None:
        """Return the first unit literal in input clause order, if any."""
        for clause in clauses:
            analysis = cls._analyze_clause(clause, assignment)

            if analysis.state is ClauseState.UNIT:
                return analysis.unit_literal

        return None

    @classmethod
    def _unit_propagate(
        cls,
        clauses: list[list[int]],
        assignment: dict[int, bool],
        statistics: SolverStatistics,
    ) -> bool:
        """Apply unit assignments in place until stable or conflicting."""
        while True:
            if cls._has_conflict(clauses, assignment):
                return False

            unit_literal = cls._find_unit_literal(clauses, assignment)

            if unit_literal is None:
                return True

            variable_id = abs(unit_literal)
            required_value = unit_literal > 0

            if variable_id in assignment:
                if assignment[variable_id] != required_value:
                    return False

                continue

            assignment[variable_id] = required_value
            statistics.propagations += 1

    @classmethod
    def _choose_variable(
        cls,
        clauses: list[list[int]],
        assignment: dict[int, bool],
    ) -> int | None:
        """Choose the smallest unassigned variable in unresolved clauses."""
        candidates: set[int] = set()

        for clause in clauses:
            analysis = cls._analyze_clause(clause, assignment)

            if analysis.state not in (
                ClauseState.UNRESOLVED,
                ClauseState.UNIT,
            ):
                continue

            for literal in set(clause):
                variable_id = abs(literal)

                if variable_id not in assignment:
                    candidates.add(variable_id)

        return min(candidates) if candidates else None

    @classmethod
    def _dpll(
        cls,
        clauses: list[list[int]],
        assignment: dict[int, bool],
        statistics: SolverStatistics,
    ) -> dict[int, bool] | None:
        """Search for a satisfying partial assignment recursively."""
        working_assignment = assignment.copy()

        propagation_ok = cls._unit_propagate(
            clauses,
            working_assignment,
            statistics,
        )

        if not propagation_ok:
            return None

        if cls._all_clauses_satisfied(clauses, working_assignment):
            return working_assignment

        variable_id = cls._choose_variable(clauses, working_assignment)

        if variable_id is None:
            return None

        for value in (True, False):
            branch_assignment = working_assignment.copy()
            branch_assignment[variable_id] = value
            statistics.decisions += 1

            result = cls._dpll(
                clauses,
                branch_assignment,
                statistics,
            )

            if result is not None:
                return result

            statistics.backtracks += 1

        return None
