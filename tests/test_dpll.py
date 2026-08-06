# tests/test_dpll.py
import pytest

from core.models import SolverStatistics
from logic.dpll import ClauseState, DPLLSolver


@pytest.mark.parametrize(
    ("literal", "assignment", "expected"),
    [
        (3, {3: True}, True),
        (3, {3: False}, False),
        (-3, {3: False}, True),
        (-3, {3: True}, False),
        (4, {3: True}, None),
    ],
)
def test_evaluate_literal(literal, assignment, expected):
    assert DPLLSolver._evaluate_literal(literal, assignment) is expected


def test_evaluate_literal_rejects_zero():
    with pytest.raises(ValueError):
        DPLLSolver._evaluate_literal(0, {})


def test_evaluate_literal_does_not_mutate_assignment():
    assignment = {3: True}
    original_assignment = assignment.copy()

    DPLLSolver._evaluate_literal(-3, assignment)

    assert assignment == original_assignment


@pytest.mark.parametrize(
    ("clause", "assignment", "expected_state", "expected_unit"),
    [
        ([1, -2], {1: True}, ClauseState.SATISFIED, None),
        ([1, -2], {}, ClauseState.UNRESOLVED, None),
        ([1, -2], {1: False}, ClauseState.UNIT, -2),
        ([1, -2], {1: False, 2: True}, ClauseState.CONFLICT, None),
        ([], {}, ClauseState.CONFLICT, None),
        ([1, -1], {}, ClauseState.SATISFIED, None),
        ([1, 1], {}, ClauseState.UNIT, 1),
    ],
)
def test_analyze_clause(
    clause,
    assignment,
    expected_state,
    expected_unit,
):
    analysis = DPLLSolver._analyze_clause(clause, assignment)

    assert analysis.state is expected_state
    assert analysis.unit_literal == expected_unit


def test_analyze_clause_rejects_zero_literal():
    with pytest.raises(ValueError):
        DPLLSolver._analyze_clause([1, 0], {})


def test_analyze_clause_does_not_mutate_inputs():
    clause = [1, 1, -2]
    assignment = {2: True}
    original_clause = clause.copy()
    original_assignment = assignment.copy()

    DPLLSolver._analyze_clause(clause, assignment)

    assert clause == original_clause
    assert assignment == original_assignment


@pytest.mark.parametrize(
    ("clauses", "assignment", "expected"),
    [
        ([[1], [-1]], {1: True}, True),
        ([[1, 2], [-1, 2]], {}, False),
        ([[]], {}, True),
        ([], {}, False),
    ],
)
def test_has_conflict(clauses, assignment, expected):
    assert DPLLSolver._has_conflict(clauses, assignment) is expected


@pytest.mark.parametrize(
    ("clauses", "assignment", "expected"),
    [
        ([[1], [-1, 2]], {1: True, 2: True}, True),
        ([[1, 2]], {}, False),
        ([[1]], {}, False),
        ([[1]], {1: False}, False),
        ([], {}, True),
        ([[]], {}, False),
    ],
)
def test_all_clauses_satisfied(clauses, assignment, expected):
    assert DPLLSolver._all_clauses_satisfied(clauses, assignment) is expected


def test_cnf_helpers_do_not_mutate_inputs():
    clauses = [[1], [-1, 2]]
    assignment = {1: True}
    original_clauses = [clause.copy() for clause in clauses]
    original_assignment = assignment.copy()

    DPLLSolver._has_conflict(clauses, assignment)
    DPLLSolver._all_clauses_satisfied(clauses, assignment)
    DPLLSolver._find_unit_literal(clauses, assignment)

    assert clauses == original_clauses
    assert assignment == original_assignment


@pytest.mark.parametrize(
    ("clauses", "assignment", "expected"),
    [
        ([[1]], {}, 1),
        ([[2], [1]], {}, 2),
        ([[1, 2], [-1, 2]], {}, None),
        ([[1, 1]], {}, 1),
    ],
)
def test_find_unit_literal(clauses, assignment, expected):
    assert DPLLSolver._find_unit_literal(clauses, assignment) == expected


@pytest.mark.parametrize(
    (
        "clauses",
        "initial_assignment",
        "expected_result",
        "expected_assignment",
        "expected_propagations",
    ),
    [
        (
            [[1], [-1, 2], [-2, 3]],
            {},
            True,
            {1: True, 2: True, 3: True},
            3,
        ),
        ([[1]], {1: False}, False, {1: False}, 0),
        ([[1], [-1]], {}, False, {1: True}, 1),
        ([[1, 2], [-1, 2]], {}, True, {}, 0),
        ([[1, 2]], {1: False}, True, {1: False, 2: True}, 1),
        ([[1, 1]], {}, True, {1: True}, 1),
        ([[1, -1]], {}, True, {}, 0),
        ([], {}, True, {}, 0),
        ([[]], {}, False, {}, 0),
    ],
)
def test_unit_propagate(
    clauses,
    initial_assignment,
    expected_result,
    expected_assignment,
    expected_propagations,
):
    statistics = SolverStatistics()

    result = DPLLSolver._unit_propagate(
        clauses,
        initial_assignment,
        statistics,
    )

    assert result is expected_result
    assert initial_assignment == expected_assignment
    assert statistics.propagations == expected_propagations
    assert statistics.decisions == 0
    assert statistics.backtracks == 0


def test_unit_propagate_does_not_mutate_clauses():
    clauses = [[1], [-1, 2], [-2, 3]]
    original_clauses = [clause.copy() for clause in clauses]

    DPLLSolver._unit_propagate(clauses, {}, SolverStatistics())

    assert clauses == original_clauses


def test_unit_propagate_preserves_decisions_and_backtracks():
    statistics = SolverStatistics(decisions=4, backtracks=2)

    DPLLSolver._unit_propagate([[1]], {}, statistics)

    assert statistics.propagations == 1
    assert statistics.decisions == 4
    assert statistics.backtracks == 2
