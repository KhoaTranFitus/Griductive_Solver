"""Run deduction experiments for every authored GriductiveSolver level."""

from __future__ import annotations

import csv
import sys
import time
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from core.models import Level  # noqa: E402
from game.game_engine import GameEngine  # noqa: E402
from game.level_catalog import build_level_catalog  # noqa: E402
from logic.cnf_encoder import (  # noqa: E402
    build_knowledge_base,
    get_encoding_statistics,
)
from logic.deductive_agent import DeductiveAgent  # noqa: E402
from logic.dpll import DPLLSolver, SolverResult  # noqa: E402
from logic.uniqueness import check_uniqueness  # noqa: E402
from logic.variable_map import VariableMap  # noqa: E402


DEFAULT_LEVELS_DIRECTORY = REPOSITORY_ROOT / "data" / "levels"
DEFAULT_OUTPUT_PATH = REPOSITORY_ROOT / "results" / "experiments.csv"

CSV_HEADER = (
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
)

MetricValue = str | int | float
ExperimentRow = dict[str, MetricValue]


class RecordingSolver(DPLLSolver):
    """Accumulate statistics from every real DPLL call in one trial."""

    def __init__(self) -> None:
        super().__init__()
        self.sat_calls = 0
        self.total_decisions = 0
        self.total_propagations = 0
        self.total_backtracks = 0
        self.total_solver_runtime_ms = 0.0

    def solve(
        self,
        clauses: list[list[int]],
        assumptions: list[int] | None = None,
    ) -> SolverResult:
        """Delegate to DPLL, record its returned statistics, and return it."""
        result = super().solve(clauses, assumptions=assumptions)
        self.sat_calls += 1
        self.total_decisions += result.decisions
        self.total_propagations += result.propagations
        self.total_backtracks += result.backtracks
        self.total_solver_runtime_ms += result.runtime_ms
        return result


def _empty_row(level: Level) -> ExperimentRow:
    """Create a complete failure-safe row before a level is attempted."""
    return {
        "level_id": level.id,
        "size": level.size,
        "primary_variables": 0,
        "auxiliary_variables": 0,
        "clauses": 0,
        "sat_calls": 0,
        "decisions": 0,
        "propagations": 0,
        "backtracks": 0,
        "deduction_steps": 0,
        "solver_runtime_ms": 0.0,
        "wall_runtime_ms": 0.0,
        "uniqueness": "ERROR",
        "status": "ERROR",
    }


def _copy_deduction_metrics(
    row: ExperimentRow,
    solver: RecordingSolver,
) -> None:
    """Copy the current deduction-only counters into an experiment row."""
    row.update({
        "sat_calls": solver.sat_calls,
        "decisions": solver.total_decisions,
        "propagations": solver.total_propagations,
        "backtracks": solver.total_backtracks,
        "solver_runtime_ms": solver.total_solver_runtime_ms,
    })


def run_level_experiment(
    level: Level,
    *,
    deduction_solver_factory: Callable[[], RecordingSolver] = RecordingSolver,
    uniqueness_solver_factory: Callable[[], DPLLSolver] = DPLLSolver,
) -> ExperimentRow:
    """Run one level and return one row, including partial metrics on error."""
    row = _empty_row(level)
    deduction_solver: RecordingSolver | None = None

    try:
        variable_map = VariableMap(level.cells)
        full_clue_cnf = build_knowledge_base(
            tuple(level.clues.values()),
            {},
            level.cells,
            variable_map,
        )
        encoding_statistics = get_encoding_statistics(
            full_clue_cnf,
            variable_map,
        )
        row.update(encoding_statistics)

        deduction_solver = deduction_solver_factory()
        agent = DeductiveAgent(solver=deduction_solver)
        engine = GameEngine(level, agent=agent)

        wall_start = time.perf_counter()
        try:
            deduction_result = engine.run_deduction_loop()
        finally:
            row["wall_runtime_ms"] = (
                time.perf_counter() - wall_start
            ) * 1000
            _copy_deduction_metrics(row, deduction_solver)

        row["deduction_steps"] = len(deduction_result.trace)

        primary_variable_ids = tuple(
            variable_map.get_variable(cell.id)
            for cell in level.cells
        )
        uniqueness_solver = uniqueness_solver_factory()
        uniqueness = check_uniqueness(
            full_clue_cnf,
            primary_variable_ids,
            uniqueness_solver,
        )

        row["uniqueness"] = uniqueness.value
        row["status"] = deduction_result.status.value
    except Exception as exc:  # Keep a row for every failed level.
        if deduction_solver is not None:
            _copy_deduction_metrics(row, deduction_solver)
        print(
            f"{level.id}: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )

    return row


def _csv_value(value: MetricValue) -> MetricValue:
    """Keep runtime output readable without changing in-memory metrics."""
    if isinstance(value, float):
        return f"{value:.6f}"
    return value


def write_csv(
    rows: Iterable[Mapping[str, MetricValue]],
    output_path: str | Path = DEFAULT_OUTPUT_PATH,
) -> Path:
    """Write experiment rows with the required fixed column order."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_HEADER)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                field: _csv_value(row[field])
                for field in CSV_HEADER
            })

    return path


def _table_value(value: MetricValue) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def print_results_table(rows: Iterable[Mapping[str, MetricValue]]) -> None:
    """Print a compact summary table for quick inspection."""
    table_fields = (
        "level_id",
        "size",
        "primary_variables",
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
    )
    labels = {
        "level_id": "level",
        "primary_variables": "vars",
        "propagations": "props",
        "backtracks": "backs",
        "deduction_steps": "steps",
        "solver_runtime_ms": "solver_ms",
        "wall_runtime_ms": "wall_ms",
    }
    materialized_rows = list(rows)
    rendered_rows = [
        {
            field: _table_value(row[field])
            for field in table_fields
        }
        for row in materialized_rows
    ]
    widths = {
        field: max(
            len(labels.get(field, field)),
            *(len(row[field]) for row in rendered_rows),
        )
        for field in table_fields
    }

    def render(values: Mapping[str, str]) -> str:
        return "  ".join(
            values[field].ljust(widths[field])
            for field in table_fields
        )

    header = {
        field: labels.get(field, field)
        for field in table_fields
    }
    print(render(header))
    print(render({field: "-" * widths[field] for field in table_fields}))
    for row in rendered_rows:
        print(render(row))


def run_experiments(
    levels: Iterable[Level] | None = None,
    output_path: str | Path = DEFAULT_OUTPUT_PATH,
) -> list[ExperimentRow]:
    """Run one fresh trial per supplied/catalog level and write its CSV."""
    selected_levels = (
        build_level_catalog(DEFAULT_LEVELS_DIRECTORY)
        if levels is None
        else list(levels)
    )
    rows = [
        run_level_experiment(level)
        for level in selected_levels
    ]
    written_path = write_csv(rows, output_path)
    print_results_table(rows)
    print(f"\nCSV: {written_path}")
    return rows


def main() -> int:
    """Run the authored level catalog from the command line."""
    run_experiments()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
