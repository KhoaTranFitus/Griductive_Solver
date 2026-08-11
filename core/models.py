# core/models.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.enums import (
    CardState,
    ClueType,
    DeductionStatus,
    RegionType,
    SubmissionResult,
    Verdict,
)

@dataclass(frozen=True)
class Character:
    id: str
    name: str
    gender: str
    occupation: str
    avatar_path: str


@dataclass(frozen=True)
class Cell:
    id: str
    row: int
    column: int
    character_id: str
    clue_id: str


@dataclass(frozen=True)
class Region:
    type: RegionType
    parameters: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class Clue:
    id: str
    owner_cell: str
    type: ClueType
    data: dict[str, Any]
    display_text: str


@dataclass(frozen=True)
class Level:
    id: str
    title: str
    size: int
    cells: tuple[Cell, ...]
    clues: dict[str, Clue]
    initial_revealed: tuple[str, ...]
    hidden_solution: dict[str, Verdict]

    def get_cell(self, cell_id: str) -> Cell:
        for cell in self.cells:
            if cell.id == cell_id:
                return cell

        raise KeyError(f"Cell not found: {cell_id}")

    def get_clue(self, clue_id: str) -> Clue:
        try:
            return self.clues[clue_id]
        except KeyError as exc:
            raise KeyError(f"Clue not found: {clue_id}") from exc

    def get_cell_ids(self) -> tuple[str, ...]:
        return tuple(cell.id for cell in self.cells)
    

@dataclass(frozen=True)
class PublicState:
    level_id: str
    size: int
    cells: tuple[Cell, ...]
    revealed_clues: tuple[Clue, ...]
    proved_verdicts: dict[str, Verdict]
    unresolved_cells: tuple[str, ...]

@dataclass(frozen=True)
class AgentMove:
    cell_id: str
    verdict: Verdict

@dataclass
class SolverStatistics:
    decisions: int = 0
    propagations: int = 0
    backtracks: int = 0
    runtime_ms: float = 0.0


@dataclass(frozen=True)
class SATQueryTrace:
    """Compact outcome of one SAT call made for an entailment check."""

    assumptions: tuple[int, ...]
    satisfiable: bool
    statistics: SolverStatistics


@dataclass(frozen=True)
class DeductionStep:
    """One forced verdict accepted by the game engine."""

    step_number: int
    active_clue_ids: tuple[str, ...]
    target_cell: str
    sat_queries: tuple[SATQueryTrace, ...]
    verdict: Verdict
    newly_revealed_clue_id: str
    solver_statistics: SolverStatistics


@dataclass(frozen=True)
class DeductionRunResult:
    """Terminal status and completed steps from a deduction loop."""

    status: DeductionStatus
    trace: tuple[DeductionStep, ...]

    @property
    def steps(self) -> tuple[DeductionStep, ...]:
        """Alias for callers that treat the trace as a step sequence."""
        return self.trace


@dataclass(frozen=True)
class SubmissionResponse:
    result: SubmissionResult
    cell_id: str
    submitted_verdict: Verdict
    proved_verdict: Verdict | None = None
    revealed_clue: Clue | None = None
    message: str = ""
