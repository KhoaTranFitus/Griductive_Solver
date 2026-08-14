import csv
from dataclasses import replace

from game.level_loader import load_level
from experiments.run_experiments import (
    CSV_HEADER,
    RecordingSolver,
    run_experiments,
    run_level_experiment,
)
from logic.dpll import DPLLSolver, SolverResult


def test_recording_solver_counts_calls_and_aggregates_statistics(monkeypatch):
    first_result = SolverResult(
        satisfiable=True,
        assignment={1: True},
        decisions=1,
        propagations=2,
        backtracks=3,
        runtime_ms=4.5,
    )
    second_result = SolverResult(
        satisfiable=False,
        assignment=None,
        decisions=5,
        propagations=6,
        backtracks=7,
        runtime_ms=8.5,
    )
    results = iter((first_result, second_result))

    def fake_solve(self, clauses, assumptions=None):
        return next(results)

    monkeypatch.setattr(DPLLSolver, "solve", fake_solve)
    solver = RecordingSolver()

    first = solver.solve([[1, 2], [-1, 2]])
    second = solver.solve([[1], [-1]])

    assert first is first_result
    assert second is second_result
    assert solver.sat_calls == 2
    assert solver.total_decisions == first.decisions + second.decisions
    assert (
        solver.total_propagations
        == first.propagations + second.propagations
    )
    assert solver.total_backtracks == first.backtracks + second.backtracks
    assert solver.total_solver_runtime_ms == (
        first.runtime_ms + second.runtime_ms
    )


def test_new_recording_solver_resets_all_counters():
    used_solver = RecordingSolver()
    used_solver.solve([[1]])

    fresh_solver = RecordingSolver()

    assert used_solver.sat_calls == 1
    assert fresh_solver.sat_calls == 0
    assert fresh_solver.total_decisions == 0
    assert fresh_solver.total_propagations == 0
    assert fresh_solver.total_backtracks == 0
    assert fresh_solver.total_solver_runtime_ms == 0.0


def test_uniqueness_solver_metrics_are_separate_from_deduction_metrics():
    level = load_level("data/levels/level_01.json")
    deduction_solver = RecordingSolver()
    uniqueness_solver = RecordingSolver()

    row = run_level_experiment(
        level,
        deduction_solver_factory=lambda: deduction_solver,
        uniqueness_solver_factory=lambda: uniqueness_solver,
    )

    assert row["status"] == "SOLVED"
    assert row["uniqueness"] == "UNIQUE"
    assert row["sat_calls"] == deduction_solver.sat_calls
    assert uniqueness_solver.sat_calls == 2
    assert row["sat_calls"] != (
        deduction_solver.sat_calls + uniqueness_solver.sat_calls
    )


def test_each_level_run_starts_with_fresh_deduction_counters():
    level = load_level("data/levels/level_01.json")

    first = run_level_experiment(level)
    second = run_level_experiment(level)

    assert first["status"] == second["status"] == "SOLVED"
    assert first["sat_calls"] == second["sat_calls"]
    assert first["decisions"] == second["decisions"]
    assert first["propagations"] == second["propagations"]
    assert first["backtracks"] == second["backtracks"]


def test_run_experiments_writes_exact_header_and_one_row(tmp_path):
    level = load_level("data/levels/level_01.json")
    output_path = tmp_path / "experiments.csv"

    rows = run_experiments([level], output_path)

    with output_path.open(encoding="utf-8", newline="") as csv_file:
        csv_rows = list(csv.reader(csv_file))

    assert list(CSV_HEADER) == [
        "level_id",
        "size",
        "primary_variables",
        "auxiliary_variables",
        "clauses",
        "sat_calls",
        "decisions",
        "propagations",
        "backtracks",
        "deduction_steps",
        "solver_runtime_ms",
        "wall_runtime_ms",
        "uniqueness",
        "status",
    ]
    assert csv_rows[0] == list(CSV_HEADER)
    assert len(rows) == 1
    assert len(csv_rows) == 2
    assert csv_rows[1][0] == level.id
    assert rows[0]["primary_variables"] == 9
    assert rows[0]["auxiliary_variables"] == 0
    assert rows[0]["clauses"] == 19
    assert rows[0]["deduction_steps"] == 8


def test_error_level_is_retained_as_one_csv_row(tmp_path):
    level = load_level("data/levels/level_01.json")
    broken_level = replace(level, id="broken_level", cells=())
    output_path = tmp_path / "experiments.csv"

    rows = run_experiments([broken_level], output_path)

    with output_path.open(encoding="utf-8", newline="") as csv_file:
        csv_rows = list(csv.DictReader(csv_file))

    assert len(rows) == 1
    assert rows[0]["level_id"] == "broken_level"
    assert rows[0]["status"] == "ERROR"
    assert len(csv_rows) == 1
    assert csv_rows[0]["level_id"] == "broken_level"
    assert csv_rows[0]["status"] == "ERROR"
