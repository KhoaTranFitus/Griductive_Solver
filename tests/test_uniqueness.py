from copy import deepcopy

import pytest

from core.exceptions import SolverError
from logic.dpll import DPLLSolver, SolverResult
from logic.uniqueness import (
    UniquenessStatus,
    build_primary_blocking_clause,
    check_uniqueness,
)


def make_solver_result(
    satisfiable: bool,
    assignment: dict[int, bool] | None = None,
) -> SolverResult:
    return SolverResult(
        satisfiable=satisfiable,
        assignment=assignment,
        decisions=0,
        propagations=0,
        backtracks=0,
        runtime_ms=0.0,
    )


class RecordingSolver:
    def __init__(self, results: list[SolverResult]) -> None:
        self._results = iter(results)
        self.calls: list[
            tuple[list[list[int]], list[int] | None]
        ] = []

    def solve(
        self,
        clauses: list[list[int]],
        assumptions: list[int] | None = None,
    ) -> SolverResult:
        self.calls.append((clauses, assumptions))
        return next(self._results)


class NeverCalledSolver:
    def solve(self, clauses, assumptions=None):
        raise AssertionError("Invalid primary IDs must fail before solving.")


@pytest.mark.parametrize(
    ("clauses", "primary_variable_ids", "expected"),
    [
        (
            [[1], [-2]],
            [1, 2],
            UniquenessStatus.UNIQUE,
        ),
        (
            [[1, 2]],
            [1, 2],
            UniquenessStatus.MULTIPLE,
        ),
        (
            [[1], [-1]],
            [1],
            UniquenessStatus.INCONSISTENT,
        ),
    ],
)
def test_check_uniqueness_classifies_formula(
    clauses: list[list[int]],
    primary_variable_ids: list[int],
    expected: UniquenessStatus,
) -> None:
    assert (
        check_uniqueness(
            clauses,
            primary_variable_ids,
            DPLLSolver(),
        )
        is expected
    )


def test_build_primary_blocking_clause() -> None:
    assignment = {
        1: True,
        2: False,
        3: True,
    }

    blocking_clause = build_primary_blocking_clause(
        assignment,
        [1, 2, 3],
    )

    assert blocking_clause == [-1, 2, -3]


def test_blocking_clause_is_sorted_and_ignores_auxiliary_variables() -> None:
    assignment = {
        1: True,
        2: False,
        3: True,
        4: False,
    }

    blocking_clause = build_primary_blocking_clause(
        assignment,
        [2, 1],
    )

    assert blocking_clause == [-1, 2]
    assert {abs(literal) for literal in blocking_clause} == {1, 2}


def test_auxiliary_ambiguity_does_not_make_primary_solution_multiple() -> None:
    clauses = [
        [1],
        [-2],
        [3, 4],
    ]

    result = check_uniqueness(clauses, [1, 2], DPLLSolver())

    assert result is UniquenessStatus.UNIQUE


def test_check_uniqueness_does_not_mutate_inputs() -> None:
    clauses = [[1], [-2], [3, 4]]
    primary_variable_ids = [2, 1]
    original_clauses = deepcopy(clauses)
    original_primary_ids = primary_variable_ids.copy()

    check_uniqueness(
        clauses,
        primary_variable_ids,
        DPLLSolver(),
    )

    assert clauses == original_clauses
    assert primary_variable_ids == original_primary_ids


def test_blocking_clause_does_not_mutate_assignment_or_primary_ids() -> None:
    assignment = {1: True, 2: False, 3: True}
    primary_variable_ids = [2, 1]
    original_assignment = assignment.copy()
    original_primary_ids = primary_variable_ids.copy()

    build_primary_blocking_clause(assignment, primary_variable_ids)

    assert assignment == original_assignment
    assert primary_variable_ids == original_primary_ids


def test_check_uniqueness_does_not_mutate_solver_assignments() -> None:
    first_assignment = {1: True, 2: False, 3: True}
    second_assignment = {1: False, 2: True, 3: False}
    original_first_assignment = first_assignment.copy()
    original_second_assignment = second_assignment.copy()
    solver = RecordingSolver(
        [
            make_solver_result(True, first_assignment),
            make_solver_result(True, second_assignment),
        ]
    )

    result = check_uniqueness([[1, 2]], [1, 2], solver)

    assert result is UniquenessStatus.MULTIPLE
    assert first_assignment == original_first_assignment
    assert second_assignment == original_second_assignment


def test_check_uniqueness_is_deterministic() -> None:
    clauses = [[1, 2]]
    solver = DPLLSolver()

    results = [
        check_uniqueness(clauses, [2, 1], solver)
        for _ in range(5)
    ]

    assert results == [UniquenessStatus.MULTIPLE] * 5


def test_sparse_primary_variable_ids_are_used_directly() -> None:
    assignment = {
        2: True,
        10: False,
        25: True,
    }

    blocking_clause = build_primary_blocking_clause(
        assignment,
        [25, 2, 10],
    )

    assert blocking_clause == [-2, 10, -25]


def test_sparse_primary_variable_ids_support_uniqueness_check() -> None:
    clauses = [[2], [-10], [25]]

    result = check_uniqueness(
        clauses,
        [25, 2, 10],
        DPLLSolver(),
    )

    assert result is UniquenessStatus.UNIQUE


@pytest.mark.parametrize(
    "primary_variable_ids",
    [
        [0],
        [-1],
        [True],
        [1, "2"],
    ],
)
def test_check_uniqueness_rejects_non_positive_integer_primary_ids(
    primary_variable_ids,
) -> None:
    with pytest.raises(ValueError, match="positive integers"):
        check_uniqueness(
            [],
            primary_variable_ids,
            NeverCalledSolver(),
        )


def test_check_uniqueness_rejects_duplicate_primary_ids() -> None:
    with pytest.raises(ValueError, match="duplicates"):
        check_uniqueness([], [1, 1], NeverCalledSolver())


@pytest.mark.parametrize(
    ("primary_variable_ids", "message"),
    [
        ([0], "positive integers"),
        ([1, 1], "duplicates"),
    ],
)
def test_blocking_clause_rejects_invalid_primary_ids(
    primary_variable_ids: list[int],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        build_primary_blocking_clause(
            {1: True},
            primary_variable_ids,
        )


@pytest.mark.parametrize(
    ("first_assignment", "message"),
    [
        (None, "must include an assignment"),
        ([], "must be a variable mapping"),
        ({1: True}, "missing primary variable IDs: \\[2\\]"),
        ({1: True, 2: 0}, "non-boolean values"),
    ],
)
def test_check_uniqueness_rejects_invalid_first_sat_assignment(
    first_assignment,
    message: str,
) -> None:
    solver = RecordingSolver(
        [make_solver_result(True, first_assignment)]
    )

    with pytest.raises(SolverError, match=message):
        check_uniqueness([[1], [-2]], [1, 2], solver)

    assert len(solver.calls) == 1


def test_check_uniqueness_rejects_incomplete_second_sat_assignment() -> None:
    solver = RecordingSolver(
        [
            make_solver_result(True, {1: True, 2: False}),
            make_solver_result(True, {1: False}),
        ]
    )

    with pytest.raises(
        SolverError,
        match="missing primary variable IDs: \\[2\\]",
    ):
        check_uniqueness([[1, 2]], [1, 2], solver)

    assert len(solver.calls) == 2


@pytest.mark.parametrize(
    ("solver_results", "expected", "expected_call_count"),
    [
        (
            [make_solver_result(False)],
            UniquenessStatus.INCONSISTENT,
            1,
        ),
        (
            [
                make_solver_result(True, {1: True, 2: False}),
                make_solver_result(False),
            ],
            UniquenessStatus.UNIQUE,
            2,
        ),
        (
            [
                make_solver_result(True, {1: True, 2: False}),
                make_solver_result(True, {1: False, 2: True}),
            ],
            UniquenessStatus.MULTIPLE,
            2,
        ),
    ],
)
def test_solver_call_count_and_second_query(
    solver_results: list[SolverResult],
    expected: UniquenessStatus,
    expected_call_count: int,
) -> None:
    clauses = [[1, 2]]
    original_clauses = deepcopy(clauses)
    solver = RecordingSolver(solver_results)

    result = check_uniqueness(clauses, [1, 2], solver)

    assert result is expected
    assert len(solver.calls) == expected_call_count
    assert solver.calls[0] == (clauses, None)
    assert solver.calls[0][0] is clauses
    assert clauses == original_clauses

    if expected_call_count == 2:
        second_clauses, assumptions = solver.calls[1]
        assert second_clauses == clauses + [[-1, 2]]
        assert second_clauses is not clauses
        assert len(second_clauses) == len(clauses) + 1
        assert second_clauses[:-1] == clauses
        assert assumptions is None
