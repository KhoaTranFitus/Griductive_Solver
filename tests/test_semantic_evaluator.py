from game.level_loader import load_level
from game.level_validator import validate_level
from logic.semantic_evaluator import evaluate_clue


def convert_solution_to_bool(level):
    return {
        cell_id: verdict.value == "CRIMINAL"
        for cell_id, verdict in level.hidden_solution.items()
    }


def test_level_is_valid():
    level = load_level("data/levels/level_01.json")
    validate_level(level)


def test_all_clues_match_hidden_solution():
    level = load_level("data/levels/level_01.json")
    assignment = convert_solution_to_bool(level)

    for clue in level.clues.values():
        assert evaluate_clue(
            clue,
            assignment,
            level.cells,
        ), f"Clue is false: {clue.id}"