# logic/entailment.py
from dataclasses import dataclass

from core.enums import Verdict
from core.models import SATQueryTrace, SolverStatistics
from logic.dpll import DPLLSolver, SolverResult


@dataclass(frozen=True)
class EntailmentDetails:
    """Verdict plus compact SAT evidence used to derive it."""

    verdict: Verdict
    sat_queries: tuple[SATQueryTrace, ...]
    solver_statistics: SolverStatistics


def _statistics_from_result(result: SolverResult) -> SolverStatistics:
    return SolverStatistics(
        decisions=result.decisions,
        propagations=result.propagations,
        backtracks=result.backtracks,
        runtime_ms=result.runtime_ms,
    )


def _run_query(
    clauses: list[list[int]],
    solver: DPLLSolver,
    assumptions: list[int] | None,
) -> tuple[SolverResult, SATQueryTrace]:
    result = solver.solve(clauses, assumptions=assumptions)
    return result, SATQueryTrace(
        assumptions=tuple(assumptions or ()),
        satisfiable=result.satisfiable,
        statistics=_statistics_from_result(result),
    )


def _details(
    verdict: Verdict,
    queries: list[SATQueryTrace],
) -> EntailmentDetails:
    return EntailmentDetails(
        verdict=verdict,
        sat_queries=tuple(queries),
        solver_statistics=SolverStatistics(
            decisions=sum(
                query.statistics.decisions for query in queries
            ),
            propagations=sum(
                query.statistics.propagations for query in queries
            ),
            backtracks=sum(
                query.statistics.backtracks for query in queries
            ),
            runtime_ms=sum(
                query.statistics.runtime_ms for query in queries
            ),
        ),
    )


def classify_character_with_details(
    clauses: list[list[int]],
    variable_id: int,
    solver: DPLLSolver,
) -> EntailmentDetails:
    """Classify a variable and retain only SAT outcomes and statistics."""
    if (
        not isinstance(variable_id, int)
        or isinstance(variable_id, bool)
        or variable_id <= 0
    ):
        raise ValueError("variable_id must be a positive integer.")

    queries: list[SATQueryTrace] = []
    base_result, base_query = _run_query(clauses, solver, None)
    queries.append(base_query)

    if base_result.satisfiable is False:
        return _details(Verdict.INCONSISTENT, queries)

    innocent_result, innocent_query = _run_query(
        clauses,
        solver,
        [-variable_id],
    )
    queries.append(innocent_query)

    if innocent_result.satisfiable is False:
        return _details(Verdict.CRIMINAL, queries)

    criminal_result, criminal_query = _run_query(
        clauses,
        solver,
        [variable_id],
    )
    queries.append(criminal_query)

    if criminal_result.satisfiable is False:
        return _details(Verdict.INNOCENT, queries)

    return _details(Verdict.UNKNOWN, queries)


def classify_character(
    clauses: list[list[int]],
    variable_id: int,
    solver: DPLLSolver,
) -> Verdict:
    """Classify a variable by checking which values the CNF entails."""
    return classify_character_with_details(
        clauses,
        variable_id,
        solver,
    ).verdict
