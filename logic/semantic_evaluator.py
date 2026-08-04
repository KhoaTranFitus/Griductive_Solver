# logic/semantic_evaluator.py
from core.enums import ClueType, Verdict
from core.exceptions import UnsupportedClueError
from core.models import Cell, Clue
from logic.region_resolver import parse_region, resolve_region

# Quy ước assignment
# {
#     "A1": True,   # Criminal
#     "B1": False,  # Innocent
# }

def _evaluate_fact(
    clue: Clue,
    assignment: dict[str, bool],
) -> bool:
    person = clue.data["person"]
    expected_status = Verdict(clue.data["status"])

    actual_value = assignment[person]

    if expected_status == Verdict.CRIMINAL:
        return actual_value is True

    if expected_status == Verdict.INNOCENT:
        return actual_value is False

    raise ValueError(
        f"FACT clue cannot use status {expected_status}"
    )

def _evaluate_same(
    clue: Clue,
    assignment: dict[str, bool],
) -> bool:
    person1 = clue.data["person1"]
    person2 = clue.data["person2"]

    return assignment[person1] == assignment[person2]

def _evaluate_different(
    clue: Clue,
    assignment: dict[str, bool],
) -> bool:
    person1 = clue.data["person1"]
    person2 = clue.data["person2"]

    return assignment[person1] != assignment[person2]

def _count_criminals(
    clue: Clue,
    assignment: dict[str, bool],
    cells: tuple[Cell, ...],
) -> int:
    region = parse_region(clue.data["region"])
    cell_ids = resolve_region(region, cells)

    return sum(
        1
        for cell_id in cell_ids
        if assignment[cell_id] is True
    )

def _evaluate_exactly(
    clue: Clue,
    assignment: dict[str, bool],
    cells: tuple[Cell, ...],
) -> bool:
    criminal_count = _count_criminals(
        clue,
        assignment,
        cells,
    )

    return criminal_count == clue.data["k"]

def _evaluate_at_least(
    clue: Clue,
    assignment: dict[str, bool],
    cells: tuple[Cell, ...],
) -> bool:
    criminal_count = _count_criminals(
        clue,
        assignment,
        cells,
    )

    return criminal_count >= clue.data["k"]

def _evaluate_at_most(
    clue: Clue,
    assignment: dict[str, bool],
    cells: tuple[Cell, ...],
) -> bool:
    criminal_count = _count_criminals(
        clue,
        assignment,
        cells,
    )

    return criminal_count <= clue.data["k"]

def evaluate_clue(
    clue: Clue,
    assignment: dict[str, bool],
    cells: tuple[Cell, ...],
) -> bool:
    required_ids = {
        cell.id
        for cell in cells
    }

    missing_ids = required_ids - assignment.keys()

    if missing_ids:
        raise ValueError(
            "Semantic evaluation requires a complete "
            f"assignment. Missing: {sorted(missing_ids)}"
        )

    if clue.type == ClueType.FACT:
        return _evaluate_fact(clue, assignment)

    if clue.type == ClueType.SAME:
        return _evaluate_same(clue, assignment)

    if clue.type == ClueType.DIFFERENT:
        return _evaluate_different(clue, assignment)

    if clue.type == ClueType.EXACTLY:
        return _evaluate_exactly(
            clue,
            assignment,
            cells,
        )

    if clue.type == ClueType.AT_LEAST:
        return _evaluate_at_least(
            clue,
            assignment,
            cells,
        )

    if clue.type == ClueType.AT_MOST:
        return _evaluate_at_most(
            clue,
            assignment,
            cells,
        )

    raise UnsupportedClueError(
        f"Unsupported clue type: {clue.type}"
    )