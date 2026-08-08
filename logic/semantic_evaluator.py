"""Direct clue semantics used to verify CNF encodings and level solutions."""

from core.enums import ClueType, Verdict
from core.exceptions import UnsupportedClueError
from core.models import Cell, Clue
from logic.region_resolver import parse_region, resolve_region


def _count(raw_region, status, assignment, cells) -> int:
    ids = resolve_region(parse_region(raw_region), cells)
    return sum(
        assignment[cid] if status is Verdict.CRIMINAL else not assignment[cid]
        for cid in ids
    )


def _connected(clue, assignment, cells) -> bool:
    ids = resolve_region(parse_region(clue.data["region"]), cells)
    status = Verdict(clue.data.get("status", Verdict.CRIMINAL.value))
    positions = {cell.id: (cell.row, cell.column) for cell in cells}
    selected = {cid for cid in ids if assignment[cid] is (status is Verdict.CRIMINAL)}
    if len(selected) <= 1:
        return True
    reached = {next(iter(selected))}
    while True:
        expanded = reached | {
            candidate for candidate in selected
            if any(
                abs(positions[candidate][0] - positions[current][0])
                + abs(positions[candidate][1] - positions[current][1]) == 1
                for current in reached
            )
        }
        if expanded == reached:
            return reached == selected
        reached = expanded


def evaluate_clue(clue: Clue, assignment: dict[str, bool], cells: tuple[Cell, ...]) -> bool:
    missing = {cell.id for cell in cells} - assignment.keys()
    if missing:
        raise ValueError(f"Semantic evaluation requires a complete assignment. Missing: {sorted(missing)}")

    if clue.type is ClueType.FACT:
        expected = Verdict(clue.data["status"])
        return assignment[clue.data["person"]] is (expected is Verdict.CRIMINAL)
    if clue.type is ClueType.SAME:
        return assignment[clue.data["person1"]] == assignment[clue.data["person2"]]
    if clue.type is ClueType.DIFFERENT:
        return assignment[clue.data["person1"]] != assignment[clue.data["person2"]]

    status = Verdict(clue.data.get("status", Verdict.CRIMINAL.value))
    if clue.type in {ClueType.EXACTLY, ClueType.AT_LEAST, ClueType.AT_MOST, ClueType.PARITY}:
        count = _count(clue.data["region"], status, assignment, cells)
        if clue.type is ClueType.EXACTLY:
            return count == clue.data["k"]
        if clue.type is ClueType.AT_LEAST:
            return count >= clue.data["k"]
        if clue.type is ClueType.AT_MOST:
            return count <= clue.data["k"]
        return count % 2 == (0 if clue.data["parity"] == "EVEN" else 1)

    if clue.type in {ClueType.EQUAL_COUNT, ClueType.COMPARE_COUNT}:
        left_raw = clue.data.get("region1", clue.data.get("left_region"))
        right_raw = clue.data.get("region2", clue.data.get("right_region"))
        left = _count(left_raw, status, assignment, cells)
        right = _count(right_raw, status, assignment, cells)
        if clue.type is ClueType.EQUAL_COUNT:
            return left == right
        return left > right if clue.data["operator"] == "GT" else left < right

    if clue.type is ClueType.CONNECTED:
        return _connected(clue, assignment, cells)

    raise UnsupportedClueError(f"Unsupported clue type: {clue.type}")
