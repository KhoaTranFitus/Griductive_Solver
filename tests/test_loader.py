# tests/test_loader.py
import json

import pytest

from core.exceptions import LevelValidationError
from game.level_loader import load_level
from game.level_validator import validate_level


def test_load_level_01():
    level = load_level("data/levels/level_01.json")

    assert level.id == "level_01"
    assert level.size == 3
    assert len(level.cells) == 9
    assert len(level.clues) == 9

    validate_level(level)


def test_loader_normalizes_cells_to_row_major_order(tmp_path):
    source_path = "data/levels/level_01.json"
    with open(source_path, "r", encoding="utf-8") as source:
        raw_level = json.load(source)

    raw_level["cells"] = list(reversed(raw_level["cells"]))
    shuffled_path = tmp_path / "shuffled_level.json"
    shuffled_path.write_text(
        json.dumps(raw_level),
        encoding="utf-8",
    )

    level = load_level(shuffled_path)

    assert [cell.id for cell in level.cells] == [
        "A1", "B1", "C1",
        "A2", "B2", "C2",
        "A3", "B3", "C3",
    ]


@pytest.mark.parametrize("status", ["UNKNOWN", "INCONSISTENT"])
def test_fact_rejects_non_final_verdicts(tmp_path, status):
    source_path = "data/levels/level_01.json"
    with open(source_path, "r", encoding="utf-8") as source:
        raw_level = json.load(source)

    raw_level["clues"][0] = {
        "id": "clue_A1",
        "owner_cell": "A1",
        "type": "FACT",
        "data": {"person": "A1", "status": status},
        "display_text": "Invalid fact for validation testing.",
    }
    invalid_path = tmp_path / "invalid_fact_level.json"
    invalid_path.write_text(
        json.dumps(raw_level),
        encoding="utf-8",
    )

    level = load_level(invalid_path)

    with pytest.raises(LevelValidationError, match="invalid status"):
        validate_level(level)
