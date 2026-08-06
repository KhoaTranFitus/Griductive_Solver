# logic/entailment.py

from core.enums import Verdict
from logic.dpll import DPLLSolver


def classify_character(
    clauses: list[list[int]],
    variable_id: int,
    solver: DPLLSolver,
) -> Verdict:
    """Classify a variable by checking which values the CNF entails."""
    if (
        not isinstance(variable_id, int)
        or isinstance(variable_id, bool)
        or variable_id <= 0
    ):
        raise ValueError("variable_id must be a positive integer.")

    base_result = solver.solve(clauses)

    if base_result.satisfiable is False:
        return Verdict.INCONSISTENT

    innocent_assumption_result = solver.solve(
        clauses,
        assumptions=[-variable_id],
    )

    if innocent_assumption_result.satisfiable is False:
        return Verdict.CRIMINAL

    criminal_assumption_result = solver.solve(
        clauses,
        assumptions=[variable_id],
    )

    if criminal_assumption_result.satisfiable is False:
        return Verdict.INNOCENT

    return Verdict.UNKNOWN
