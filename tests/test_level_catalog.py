import json
import re

import pytest

from core.enums import ClueType
from game.game_engine import GameEngine
from game.level_catalog import build_level_catalog
from gui.character_loader import load_characters
from logic.semantic_evaluator import evaluate_clue


def test_catalog_loads_the_six_authored_json_levels():
    levels = build_level_catalog()

    assert [level.id for level in levels] == [
        "level_01", "level_02", "level_03",
        "level_04", "level_05", "level_06",
    ]
    assert [level.size for level in levels] == [3, 3, 4, 4, 5, 5]


def test_catalog_rejects_a_file_with_the_wrong_size(tmp_path):
    source = json.loads(open("data/levels/level_01.json", encoding="utf-8").read())
    for number in range(1, 7):
        data = dict(source)
        data["id"] = f"level_{number:02d}"
        (tmp_path / f"level_{number:02d}.json").write_text(
            json.dumps(data), encoding="utf-8"
        )

    with pytest.raises(ValueError, match="level_03.json must be 4x4"):
        build_level_catalog(tmp_path)


def test_hard_levels_are_fact_free_and_fully_deductive():
    for level in build_level_catalog()[2:]:
        assert all(clue.type is not ClueType.FACT for clue in level.clues.values())
        assignment = {
            cell_id: verdict.value == "CRIMINAL"
            for cell_id, verdict in level.hidden_solution.items()
        }
        assert all(
            evaluate_clue(clue, assignment, level.cells)
            for clue in level.clues.values()
        )

        engine = GameEngine(level)
        moves = 0
        while not engine.is_solved():
            response = engine.auto_solve_step()
            assert response is not None, f"{level.id} became stuck after {moves} moves"
            moves += 1

        assert moves == len(level.cells) - len(level.initial_revealed)


def test_hard_level_display_text_uses_names_not_cell_coordinates():
    coordinate = re.compile(r"\b[A-E][1-5]\b")
    for level in build_level_catalog()[2:]:
        for clue in level.clues.values():
            assert coordinate.search(clue.display_text) is None, (
                f"{level.id}/{clue.id} exposes a cell coordinate: {clue.display_text}"
            )


def test_characters_are_alphabetical_in_every_level():
    characters = load_characters("data/characters.json")
    for level in build_level_catalog():
        names = [characters[cell.character_id].name for cell in level.cells]
        assert names == sorted(names, key=str.casefold), level.id
