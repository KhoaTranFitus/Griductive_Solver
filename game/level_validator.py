# game/level_validator.py
from core.enums import ClueType, Verdict
from core.exceptions import LevelValidationError, RegionResolutionError
from core.models import Clue, Level
from logic.region_resolver import parse_region, resolve_region

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

        if clue.type != ClueType.PARITY:
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

    for cell in level.cells:
        if cell.clue_id not in level.clues:
            raise LevelValidationError(
                f"Cell {cell.id} references "
                f"missing clue {cell.clue_id}."
            )

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
