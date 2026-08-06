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


@pytest.mark.parametrize(
    ("clauses", "assignment", "expected"),
    [
        ([[5, 3], [2, -4]], {}, 2),
        ([[1], [2, 3]], {1: True, 2: False}, 3),
        ([[1, 2], [3, 4]], {1: True}, 3),
        ([[4, 4, 3], [2, 2]], {}, 2),
        ([[1, -1], [3, 4]], {}, 3),
        ([[1], [-2]], {1: True, 2: False}, None),
    ],
)
def test_choose_variable(clauses, assignment, expected):
    assert DPLLSolver._choose_variable(clauses, assignment) == expected


def test_choose_variable_does_not_mutate_inputs():
    clauses = [[5, 3, 3], [2, -4]]
    assignment = {5: False}
    original_clauses = [clause.copy() for clause in clauses]
    original_assignment = assignment.copy()

    DPLLSolver._choose_variable(clauses, assignment)

    assert clauses == original_clauses
    assert assignment == original_assignment


def test_dpll_solves_sat_by_unit_propagation_only():
    statistics = SolverStatistics()

    result = DPLLSolver._dpll([[1], [-1, 2]], {}, statistics)

    assert result == {1: True, 2: True}
    assert statistics.decisions == 0
    assert statistics.propagations == 2
    assert statistics.backtracks == 0


def test_dpll_solves_sat_with_one_decision():
    statistics = SolverStatistics()

    result = DPLLSolver._dpll([[1, 2], [-1, 2]], {}, statistics)

    assert result is not None
    assert result[1] is True
    assert result[2] is True
    assert statistics.decisions == 1
    assert statistics.propagations == 1
    assert statistics.backtracks == 0


def test_dpll_backtracks_to_successful_false_branch():
    statistics = SolverStatistics()
    clauses = [[-1, 2], [-1, -2], [1, 3]]

    result = DPLLSolver._dpll(clauses, {}, statistics)

    assert result is not None
    assert result[1] is False
    assert result[3] is True
    assert statistics.decisions == 2
    assert statistics.propagations == 2
    assert statistics.backtracks == 1


def test_dpll_finds_unsat_after_both_branches_fail():
    statistics = SolverStatistics()
    clauses = [[1, 2], [1, -2], [-1, 2], [-1, -2]]

    result = DPLLSolver._dpll(clauses, {}, statistics)

    assert result is None
    assert statistics.decisions == 2
    assert statistics.propagations == 2
    assert statistics.backtracks == 2


@pytest.mark.parametrize(
    ("clauses", "expected"),
    [
        ([], {}),
        ([[]], None),
    ],
)
def test_dpll_handles_empty_formula_and_empty_clause(clauses, expected):
    statistics = SolverStatistics()

    result = DPLLSolver._dpll(clauses, {}, statistics)

    assert result == expected
    assert statistics.decisions == 0
    assert statistics.propagations == 0
    assert statistics.backtracks == 0


def test_dpll_does_not_mutate_caller_assignment():
    assignment = {}
    original_assignment = assignment.copy()

    DPLLSolver._dpll(
        [[1, 2], [-1, 2]],
        assignment,
        SolverStatistics(),
    )

    assert assignment == original_assignment


def test_dpll_does_not_mutate_clauses():
    clauses = [[-1, 2], [-1, -2], [1, 3]]
    original_clauses = [clause.copy() for clause in clauses]

    DPLLSolver._dpll(clauses, {}, SolverStatistics())

    assert clauses == original_clauses


def test_dpll_failed_branch_assignment_does_not_leak():
    clauses = [[-1, 2], [-1, -2], [1, 3]]

    result = DPLLSolver._dpll(clauses, {}, SolverStatistics())

    assert result is not None
    assert result[1] is False
    assert result[3] is True
    assert 2 not in result


def test_dpll_is_deterministic_across_runs():
    clauses = [[-1, 2], [-1, -2], [1, 3]]
    runs = []

    for _ in range(5):
        statistics = SolverStatistics()
        result = DPLLSolver._dpll(clauses, {}, statistics)
        runs.append(
            (
                result,
                statistics.decisions,
                statistics.propagations,
                statistics.backtracks,
            )
        )

    assert all(run == runs[0] for run in runs[1:])


def test_solve_sat_by_unit_propagation_only():
    result = DPLLSolver().solve([[1], [-1, 2]])

    assert result.satisfiable is True
    assert result.assignment == {1: True, 2: True}
    assert result.decisions == 0
    assert result.propagations == 2
    assert result.backtracks == 0
    assert result.runtime_ms >= 0


def test_solve_immediate_unsat():
    result = DPLLSolver().solve([[1], [-1]])

    assert result.satisfiable is False
    assert result.assignment is None
    assert result.decisions == 0
    assert result.propagations == 1
    assert result.backtracks == 0
    assert result.runtime_ms >= 0


def test_solve_sat_requiring_branching():
    result = DPLLSolver().solve([[1, 2], [-1, 2]])

    assert result.satisfiable is True
    assert result.assignment == {1: True, 2: True}
    assert result.decisions == 1
    assert result.propagations == 1
    assert result.backtracks == 0


def test_solve_unsat_requiring_branching():
    clauses = [[1, 2], [1, -2], [-1, 2], [-1, -2]]

    result = DPLLSolver().solve(clauses)

    assert result.satisfiable is False
    assert result.assignment is None
    assert result.decisions == 2
    assert result.propagations == 2
    assert result.backtracks == 2


def test_solve_assumption_forces_another_variable():
    result = DPLLSolver().solve([[1, 2]], assumptions=[-1])

    assert result.satisfiable is True
    assert result.assignment == {1: False, 2: True}
    assert result.decisions == 0
    assert result.propagations == 1
    assert result.backtracks == 0


def test_solve_assumption_contradicts_formula():
    result = DPLLSolver().solve([[1]], assumptions=[-1])

    assert result.satisfiable is False
    assert result.assignment is None
    assert result.decisions == 0
    assert result.propagations == 0
    assert result.backtracks == 0


def test_solve_rejects_contradictory_assumptions():
    result = DPLLSolver().solve([], assumptions=[1, -1])

    assert result.satisfiable is False
    assert result.assignment is None
    assert result.decisions == 0
    assert result.propagations == 0
    assert result.backtracks == 0


def test_solve_accepts_repeated_identical_assumptions():
    result = DPLLSolver().solve([], assumptions=[3, 3])

    assert result.satisfiable is True
    assert result.assignment == {3: True}


def test_solve_includes_assumption_variable_not_in_clauses():
    result = DPLLSolver().solve([], assumptions=[-5])

    assert result.satisfiable is True
    assert result.assignment == {5: False}


def test_solve_returns_complete_assignment():
    result = DPLLSolver().solve([[1, 2]])

    assert result.satisfiable is True
    assert result.assignment == {1: True, 2: False}


def test_solve_handles_empty_cnf():
    result = DPLLSolver().solve([])

    assert result.satisfiable is True
    assert result.assignment == {}
    assert result.decisions == 0
    assert result.propagations == 0
    assert result.backtracks == 0


def test_solve_handles_cnf_containing_empty_clause():
    result = DPLLSolver().solve([[]])

    assert result.satisfiable is False
    assert result.assignment is None
    assert result.decisions == 0
    assert result.propagations == 0
    assert result.backtracks == 0


def test_solve_rejects_zero_literal_in_clause():
    with pytest.raises(ValueError):
        DPLLSolver().solve([[1, 0]])


def test_solve_rejects_zero_literal_in_assumptions():
    with pytest.raises(ValueError):
        DPLLSolver().solve([], assumptions=[0])


def test_solve_does_not_mutate_inputs():
    clauses = [[1, 2], [-1, 3]]
    assumptions = [-2]
    original_clauses = [clause.copy() for clause in clauses]
    original_assumptions = assumptions.copy()

    DPLLSolver().solve(clauses, assumptions)

    assert clauses == original_clauses
    assert all(
        clause == original_clause
        for clause, original_clause in zip(clauses, original_clauses)
    )
    assert assumptions == original_assumptions


def test_solve_resets_statistics_between_calls():
    solver = DPLLSolver()
    first_result = solver.solve([[1, 2], [-1, 2]])

    second_result = solver.solve([])

    assert first_result.decisions == 1
    assert second_result.decisions == 0
    assert second_result.propagations == 0
    assert second_result.backtracks == 0


def test_solve_is_deterministic_across_runs():
    solver = DPLLSolver()
    clauses = [[-1, 2], [-1, -2], [1, 3]]
    runs = []

    for _ in range(5):
        result = solver.solve(clauses)
        runs.append(
            (
                result.satisfiable,
                result.assignment,
                result.decisions,
                result.propagations,
                result.backtracks,
            )
        )

    assert all(run == runs[0] for run in runs[1:])


def test_solve_supports_sparse_variable_ids():
    clauses = [[2, 10], [-10, 25]]

    result = DPLLSolver().solve(clauses)

    assert result.satisfiable is True
    assert result.assignment is not None
    assert set(result.assignment) == {2, 10, 25}
