# tests/test_entailment.py

import pytest

from core.enums import Verdict
from logic.dpll import DPLLSolver, SolverResult
from logic.entailment import classify_character


def make_solver_result(satisfiable: bool) -> SolverResult:
    return SolverResult(
        satisfiable=satisfiable,
        assignment={} if satisfiable else None,
        decisions=0,
        propagations=0,
        backtracks=0,
        runtime_ms=0.0,
    )


class RecordingSolver:
    def __init__(self, results: list[SolverResult]) -> None:
        self._results = iter(results)
        self.calls: list[tuple[list[list[int]], list[int] | None]] = []

    def solve(
        self,
        clauses: list[list[int]],
        assumptions: list[int] | None = None,
    ) -> SolverResult:
        self.calls.append((clauses, assumptions))
        return next(self._results)


@pytest.mark.parametrize(
    ("clauses", "variable_id", "expected"),
    [
        ([[1, 2], [-1, 2]], 2, Verdict.CRIMINAL),
        ([[1, 2], [-1, 2]], 1, Verdict.UNKNOWN),
        ([[-1]], 1, Verdict.INNOCENT),
        ([[1]], 1, Verdict.CRIMINAL),
        ([[1], [-1]], 1, Verdict.INCONSISTENT),
        ([[1]], 5, Verdict.UNKNOWN),
        ([], 1, Verdict.UNKNOWN),
        ([[1, 2]], 1, Verdict.UNKNOWN),
    ],
)
def test_classify_character(
    clauses: list[list[int]],
    variable_id: int,
    expected: Verdict,
) -> None:
    assert (
        classify_character(clauses, variable_id, DPLLSolver())
        is expected
    )


@pytest.mark.parametrize("variable_id", [0, -1])
def test_classify_character_rejects_invalid_variable_id(
    variable_id: int,
) -> None:
    with pytest.raises(ValueError):
        classify_character([], variable_id, DPLLSolver())


def test_classify_character_does_not_mutate_clauses() -> None:
    clauses = [[1, 2], [-1, 2]]
    original_clauses = [clause.copy() for clause in clauses]

    classify_character(clauses, 2, DPLLSolver())

    assert clauses == original_clauses


def test_classify_character_is_deterministic() -> None:
    clauses = [[1, 2], [-1, 2]]
    solver = DPLLSolver()

    results = [
        classify_character(clauses, 1, solver)
        for _ in range(5)
    ]

    assert all(result is Verdict.UNKNOWN for result in results)


def test_inconsistent_kb_only_calls_solver_once() -> None:
    clauses = [[1], [-1]]
    solver = RecordingSolver([make_solver_result(False)])

    result = classify_character(clauses, 1, solver)

    assert result is Verdict.INCONSISTENT
    assert solver.calls == [(clauses, None)]


def test_forced_criminal_stops_after_negative_assumption() -> None:
    clauses = [[1]]
    solver = RecordingSolver(
        [
            make_solver_result(True),
            make_solver_result(False),
        ]
    )

    result = classify_character(clauses, 1, solver)

    assert result is Verdict.CRIMINAL
    assert solver.calls == [
        (clauses, None),
        (clauses, [-1]),
    ]


def test_forced_innocent_uses_positive_assumption_last() -> None:
    clauses = [[-1]]
    solver = RecordingSolver(
        [
            make_solver_result(True),
            make_solver_result(True),
            make_solver_result(False),
        ]
    )

    result = classify_character(clauses, 1, solver)

    assert result is Verdict.INNOCENT
    assert solver.calls == [
        (clauses, None),
        (clauses, [-1]),
        (clauses, [1]),
    ]


def test_unknown_uses_both_assumptions_in_order() -> None:
    clauses = [[1, 2]]
    solver = RecordingSolver(
        [
            make_solver_result(True),
            make_solver_result(True),
            make_solver_result(True),
        ]
    )

    result = classify_character(clauses, 1, solver)

    assert result is Verdict.UNKNOWN
    assert solver.calls == [
        (clauses, None),
        (clauses, [-1]),
        (clauses, [1]),
    ]
