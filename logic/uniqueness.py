"""Projected model uniqueness checks for CNF formulas.

Puzzle solutions are assignments to primary (cell-status) variables.  Any
auxiliary variables used by an encoding are intentionally excluded from the
blocking clause so that different auxiliary witnesses do not count as
different puzzle solutions.
"""

from collections.abc import Iterable, Mapping
from enum import Enum

from core.exceptions import SolverError
from logic.dpll import DPLLSolver


class UniquenessStatus(str, Enum):
    """Number of distinct satisfying assignments on primary variables."""

    UNIQUE = "UNIQUE"
    MULTIPLE = "MULTIPLE"
    INCONSISTENT = "INCONSISTENT"


def _normalize_primary_variable_ids(
    primary_variable_ids: Iterable[int],
) -> tuple[int, ...]:
    """Validate and return primary IDs in deterministic ascending order."""
    ids = tuple(primary_variable_ids)

    if any(
        not isinstance(variable_id, int)
        or isinstance(variable_id, bool)
        or variable_id <= 0
        for variable_id in ids
    ):
        raise ValueError(
            "primary_variable_ids must contain only positive integers."
        )

    if len(set(ids)) != len(ids):
        raise ValueError("primary_variable_ids cannot contain duplicates.")

    return tuple(sorted(ids))


def _validate_primary_assignment(
    assignment: Mapping[int, bool] | None,
    primary_variable_ids: tuple[int, ...],
) -> Mapping[int, bool]:
    """Enforce the solver contract for a satisfying result."""
    if assignment is None:
        raise SolverError("A SAT result must include an assignment.")
    if not isinstance(assignment, Mapping):
        raise SolverError("A SAT assignment must be a variable mapping.")

    missing_ids = [
        variable_id
        for variable_id in primary_variable_ids
        if variable_id not in assignment
    ]
    if missing_ids:
        raise SolverError(
            "SAT assignment is missing primary variable IDs: "
            f"{missing_ids}."
        )

    invalid_ids = [
        variable_id
        for variable_id in primary_variable_ids
        if not isinstance(assignment[variable_id], bool)
    ]
    if invalid_ids:
        raise SolverError(
            "SAT assignment has non-boolean values for primary variable "
            f"IDs: {invalid_ids}."
        )

    return assignment


def build_primary_blocking_clause(
    assignment: Mapping[int, bool],
    primary_variable_ids: Iterable[int],
) -> list[int]:
    """Block exactly one assignment projected onto the primary variables."""
    normalized_ids = _normalize_primary_variable_ids(primary_variable_ids)
    validated_assignment = _validate_primary_assignment(
        assignment,
        normalized_ids,
    )

    return [
        -variable_id if validated_assignment[variable_id] else variable_id
        for variable_id in normalized_ids
    ]


def check_uniqueness(
    clauses: list[list[int]],
    primary_variable_ids: Iterable[int],
    solver: DPLLSolver,
) -> UniquenessStatus:
    """Classify CNF solutions after projecting models onto primary variables.

    The original clauses, primary ID collection, and returned solver
    assignments are never modified.
    """
    normalized_ids = _normalize_primary_variable_ids(primary_variable_ids)
    first_result = solver.solve(clauses)

    if first_result.satisfiable is False:
        return UniquenessStatus.INCONSISTENT

    first_assignment = _validate_primary_assignment(
        first_result.assignment,
        normalized_ids,
    )
    blocking_clause = build_primary_blocking_clause(
        first_assignment,
        normalized_ids,
    )
    second_clauses = clauses + [blocking_clause]
    second_result = solver.solve(second_clauses)

    if second_result.satisfiable is False:
        return UniquenessStatus.UNIQUE

    _validate_primary_assignment(second_result.assignment, normalized_ids)
    return UniquenessStatus.MULTIPLE
