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

def _parse_cell(raw_cell: dict[str, Any]) -> Cell:
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
            f"Invalid cell data: {raw_cell}"
        ) from exc


def _parse_clue(raw_clue: dict[str, Any]) -> Clue:
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
            f"Invalid clue data: {raw_clue}"
        ) from exc


def _parse_solution(
    raw_solution: dict[str, Any],
) -> dict[str, Verdict]:
    solution: dict[str, Verdict] = {}

    try:
        for cell_id, verdict_value in raw_solution.items():
            solution[str(cell_id)] = Verdict(verdict_value)
    except (AttributeError, ValueError) as exc:
        raise LevelLoadError(
            "Invalid solution format."
        ) from exc

    return solution

def load_level(file_path: str | Path) -> Level:
    raw = _read_json(file_path)

    try:
        cells = tuple(sorted(
            (
                _parse_cell(raw_cell)
                for raw_cell in raw["cells"]
            ),
            key=lambda cell: (cell.row, cell.column),
        ))

        clue_list = [
            _parse_clue(raw_clue)
            for raw_clue in raw["clues"]
        ]

        clues = {
            clue.id: clue
            for clue in clue_list
        }

        initial_revealed = tuple(
            str(cell_id)
            for cell_id in raw["initial_revealed"]
        )

        hidden_solution = _parse_solution(raw["solution"])

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
            f"Missing required level field: {exc.args[0]}"
        ) from exc
    except (TypeError, ValueError) as exc:
        raise LevelLoadError(
            f"Invalid level data: {exc}"
        ) from exc
