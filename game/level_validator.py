# game/level_validator.py
from core.enums import ClueType, CountOperator, Parity, Verdict
from core.exceptions import LevelValidationError, RegionResolutionError
from core.models import Clue, Level
from logic.region_resolver import parse_region, resolve_region
from logic.semantic_evaluator import evaluate_clue

def _ensure_unique(
    values: list[str],
    label: str,
) -> None:
    if len(values) != len(set(values)):
        raise LevelValidationError(
            f"Duplicate {label} detected."
        )

def _validate_clue(
    clue: Clue,
    level: Level,
) -> None:
    cell_ids = set(level.get_cell_ids())

    if clue.owner_cell not in cell_ids:
        raise LevelValidationError(
            f"Clue {clue.id} has invalid owner cell: "
            f"{clue.owner_cell}"
        )

    if clue.type == ClueType.FACT:
        person = clue.data.get("person")
        status = clue.data.get("status")

        if person not in cell_ids:
            raise LevelValidationError(
                f"FACT clue {clue.id} references "
                f"unknown person: {person}"
            )

        if status not in {
            Verdict.CRIMINAL.value,
            Verdict.INNOCENT.value,
        }:
            raise LevelValidationError(
                f"FACT clue {clue.id} has "
                f"invalid status: {status}"
            )

    elif clue.type in {
        ClueType.SAME,
        ClueType.DIFFERENT,
    }:
        person1 = clue.data.get("person1")
        person2 = clue.data.get("person2")

        if person1 not in cell_ids:
            raise LevelValidationError(
                f"Clue {clue.id} references "
                f"unknown person: {person1}"
            )

        if person2 not in cell_ids:
            raise LevelValidationError(
                f"Clue {clue.id} references "
                f"unknown person: {person2}"
            )

        if person1 == person2:
            raise LevelValidationError(
                f"Clue {clue.id} must reference "
                "two different people."
            )

    elif clue.type in {
        ClueType.EXACTLY,
        ClueType.AT_LEAST,
        ClueType.AT_MOST,
        ClueType.PARITY,
    }:
        raw_region = clue.data.get("region")

        try:
            region = parse_region(raw_region)
            resolved_ids = resolve_region(region, level.cells)
        except RegionResolutionError as exc:
            raise LevelValidationError(
                f"Invalid region in clue {clue.id}: {exc}"
            ) from exc

        status = clue.data.get("status", Verdict.CRIMINAL.value)
        if status not in {Verdict.CRIMINAL.value, Verdict.INNOCENT.value}:
            raise LevelValidationError(
                f"Clue {clue.id} has invalid counting status: {status}"
            )

        if clue.type == ClueType.PARITY:
            try:
                Parity(clue.data.get("parity"))
            except ValueError as exc:
                raise LevelValidationError(
                    f"Clue {clue.id} requires parity EVEN or ODD."
                ) from exc
        else:
            k = clue.data.get("k")

            if not isinstance(k, int):
                raise LevelValidationError(
                    f"Clue {clue.id} requires integer k."
                )

            if not 0 <= k <= len(resolved_ids):
                raise LevelValidationError(
                    f"Clue {clue.id} has invalid k={k}; "
                    f"region size is {len(resolved_ids)}."
                )

    elif clue.type in {ClueType.EQUAL_COUNT, ClueType.COMPARE_COUNT}:
        status = clue.data.get("status", Verdict.CRIMINAL.value)
        if status not in {Verdict.CRIMINAL.value, Verdict.INNOCENT.value}:
            raise LevelValidationError(f"Clue {clue.id} has invalid counting status: {status}")
        raw_regions = (
            (clue.data.get("region1"), clue.data.get("region2"))
            if clue.type is ClueType.EQUAL_COUNT
            else (clue.data.get("left_region"), clue.data.get("right_region"))
        )
        try:
            for raw_region in raw_regions:
                resolve_region(parse_region(raw_region), level.cells)
        except RegionResolutionError as exc:
            raise LevelValidationError(f"Invalid region in clue {clue.id}: {exc}") from exc
        if clue.type is ClueType.COMPARE_COUNT:
            try:
                CountOperator(clue.data.get("operator"))
            except ValueError as exc:
                raise LevelValidationError(
                    f"Clue {clue.id} requires operator GT or LT."
                ) from exc

    elif clue.type is ClueType.CONNECTED:
        if clue.data.get("connectivity", "ORTHOGONAL") != "ORTHOGONAL":
            raise LevelValidationError(f"Clue {clue.id} only supports ORTHOGONAL connectivity.")
        status = clue.data.get("status", Verdict.CRIMINAL.value)
        if status not in {Verdict.CRIMINAL.value, Verdict.INNOCENT.value}:
            raise LevelValidationError(f"Clue {clue.id} has invalid connected status: {status}")
        try:
            resolve_region(parse_region(clue.data.get("region")), level.cells)
        except RegionResolutionError as exc:
            raise LevelValidationError(f"Invalid region in clue {clue.id}: {exc}") from exc

    # Evaluate clue against hidden solution
    assignment = {
        cid: (verdict == Verdict.CRIMINAL)
        for cid, verdict in level.hidden_solution.items()
    }
    try:
        is_true = evaluate_clue(clue, assignment, level.cells)
    except Exception as exc:
        raise LevelValidationError(f"Failed to evaluate clue {clue.id}: {exc}") from exc
    if not is_true:
        raise LevelValidationError(f"Clue {clue.id} contradicts the hidden solution.")

def validate_level(level: Level) -> None:
    if level.size not in {3, 4, 5}:
        raise LevelValidationError(
            "Level size must be 3, 4, or 5."
        )

    expected_cell_count = level.size * level.size

    if len(level.cells) != expected_cell_count:
        raise LevelValidationError(
            f"Expected {expected_cell_count} cells, "
            f"found {len(level.cells)}."
        )

    cell_ids = [
        cell.id
        for cell in level.cells
    ]

    clue_ids = list(level.clues.keys())

    character_ids = [
        cell.character_id
        for cell in level.cells
    ]

    _ensure_unique(cell_ids, "cell IDs")
    _ensure_unique(clue_ids, "clue IDs")
    _ensure_unique(character_ids, "character IDs")

    expected_positions = {
        (row, column)
        for row in range(1, level.size + 1)
        for column in range(1, level.size + 1)
    }

    actual_positions = {
        (cell.row, cell.column)
        for cell in level.cells
    }

    if actual_positions != expected_positions:
        raise LevelValidationError(
            "Cells do not cover every board position exactly once."
        )

    if len(level.clues) != len(level.cells):
        raise LevelValidationError(
            f"Expected {len(level.cells)} clues, "
            f"found {len(level.clues)}."
        )

    for cell in level.cells:
        if cell.clue_id not in level.clues:
            raise LevelValidationError(
                f"Cell {cell.id} references "
                f"missing clue {cell.clue_id}."
            )
        clue = level.clues[cell.clue_id]
        if clue.owner_cell != cell.id:
            raise LevelValidationError(
                f"Cell {cell.id} references clue {clue.id} "
                f"which is owned by {clue.owner_cell}."
            )

    owner_cells = [clue.owner_cell for clue in level.clues.values()]
    _ensure_unique(owner_cells, "owner cells")
    solution_ids = set(level.hidden_solution.keys())
    expected_ids = set(cell_ids)

    if solution_ids != expected_ids:
        missing = expected_ids - solution_ids
        extra = solution_ids - expected_ids

        raise LevelValidationError(
            f"Solution mismatch. Missing={sorted(missing)}, "
            f"extra={sorted(extra)}"
        )

    for cell_id in level.initial_revealed:
        if cell_id not in expected_ids:
            raise LevelValidationError(
                f"Invalid initially revealed cell: {cell_id}"
            )

    if len(set(level.initial_revealed)) != len(
        level.initial_revealed
    ):
        raise LevelValidationError(
            "initial_revealed contains duplicates."
        )

    for clue in level.clues.values():
        _validate_clue(clue, level)
