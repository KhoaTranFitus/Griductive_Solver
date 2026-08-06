# tests/test_dpll.py
import pytest

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
