# game/level_loader.py
import json
from pathlib import Path
from typing import Any

from core.enums import ClueType, Verdict
from core.exceptions import LevelLoadError
from core.models import Cell, Clue, Level

def _read_json(file_path: str | Path) -> dict[str, Any]:
    path = Path(file_path)

    if not path.exists():
        raise LevelLoadError(f"Level file does not exist: {path}")

    if not path.is_file():
        raise LevelLoadError(f"Level path is not a file: {path}")

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise LevelLoadError(
            f"Invalid JSON in level file {path}: {exc}"
        ) from exc
    except OSError as exc:
        raise LevelLoadError(
            f"Cannot read level file {path}: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise LevelLoadError("Level root must be a JSON object.")

    return data

def _parse_cell(raw_cell: dict[str, Any], file_path: str | Path) -> Cell:
    try:
        return Cell(
            id=str(raw_cell["id"]),
            row=int(raw_cell["row"]),
            column=int(raw_cell["column"]),
            character_id=str(raw_cell["character_id"]),
            clue_id=str(raw_cell["clue_id"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise LevelLoadError(
            f"Invalid cell data in {file_path}: {exc} - {raw_cell}"
        ) from exc


def _parse_clue(raw_clue: dict[str, Any], file_path: str | Path) -> Clue:
    try:
        return Clue(
            id=str(raw_clue["id"]),
            owner_cell=str(raw_clue["owner_cell"]),
            type=ClueType(raw_clue["type"]),
            data=dict(raw_clue["data"]),
            display_text=str(raw_clue["display_text"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise LevelLoadError(
            f"Invalid clue data in {file_path}: {exc} - {raw_clue}"
        ) from exc


def _parse_solution(
    raw_solution: dict[str, Any],
    file_path: str | Path,
) -> dict[str, Verdict]:
    solution: dict[str, Verdict] = {}

    try:
        for cell_id, verdict_value in raw_solution.items():
            solution[str(cell_id)] = Verdict(verdict_value)
    except (AttributeError, ValueError) as exc:
        raise LevelLoadError(
            f"Invalid solution format in {file_path}: {exc}"
        ) from exc

    return solution

def load_level(file_path: str | Path) -> Level:
    raw = _read_json(file_path)

    try:
        if not isinstance(raw.get("cells"), list):
            raise LevelLoadError(f"'cells' must be a list in {file_path}")
        if not isinstance(raw.get("clues"), list):
            raise LevelLoadError(f"'clues' must be a list in {file_path}")
        if not isinstance(raw.get("solution"), dict):
            raise LevelLoadError(f"'solution' must be a dict in {file_path}")
        if not isinstance(raw.get("initial_revealed"), list):
            raise LevelLoadError(f"'initial_revealed' must be a list in {file_path}")

        cells = tuple(sorted(
            (
                _parse_cell(raw_cell, file_path)
                for raw_cell in raw["cells"]
            ),
            key=lambda cell: (cell.row, cell.column),
        ))

        clue_list = []
        clue_ids = set()
        for raw_clue in raw["clues"]:
            clue = _parse_clue(raw_clue, file_path)
            if clue.id in clue_ids:
                raise LevelLoadError(f"Duplicate clue ID in {file_path}: {clue.id}")
            clue_ids.add(clue.id)
            clue_list.append(clue)

        clues = {
            clue.id: clue
            for clue in clue_list
        }

        initial_revealed = tuple(
            str(cell_id)
            for cell_id in raw["initial_revealed"]
        )

        hidden_solution = _parse_solution(raw["solution"], file_path)

        return Level(
            id=str(raw["id"]),
            title=str(raw["title"]),
            size=int(raw["size"]),
            cells=cells,
            clues=clues,
            initial_revealed=initial_revealed,
            hidden_solution=hidden_solution,
        )

    except KeyError as exc:
        raise LevelLoadError(
            f"Missing required level field in {file_path}: {exc.args[0]}"
        ) from exc
    except (TypeError, ValueError) as exc:
        raise LevelLoadError(
            f"Invalid level data in {file_path}: {exc}"
        ) from exc
