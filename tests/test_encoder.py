# tests/test_encoder.py
from game.level_loader import load_level
from logic.semantic_evaluator import evaluate_clue


def _solution_to_bool_assignment(level):
    return {
        cell_id: verdict.value == "CRIMINAL"
        for cell_id, verdict
        in level.hidden_solution.items()
    }


def test_all_clues_are_true_for_hidden_solution():
    level = load_level("data/levels/level_01.json")
    assignment = _solution_to_bool_assignment(level)

    for clue in level.clues.values():
        assert evaluate_clue(
            clue,
            assignment,
            level.cells,
        ), f"Clue is false: {clue.id}"