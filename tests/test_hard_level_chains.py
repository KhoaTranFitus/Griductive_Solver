import pytest

from core.enums import ClueType
from game.game_engine import GameEngine
from game.level_loader import load_level


EXPECTED_CHAINS = {
    "level_05": (
        "B5", "E2", "D5", "C5", "B1", "C1", "A3", "E5",
        "D1", "E1", "A2", "B2", "C2", "D2", "B3", "C3",
        "D3", "E3", "C4", "D4", "E4", "A4", "B4", "A5",
    ),
    "level_06": (
        "A1", "E5", "B1", "C1", "D1", "E1", "A3", "B3",
        "C3", "B2", "E3", "A2", "C2", "D2", "E2", "A4",
        "B4", "C4", "D4", "E4", "B5", "C5", "D5", "A5",
    ),
}


@pytest.mark.parametrize("level_id", ("level_05", "level_06"))
def test_hard_level_full_deduction_chain(level_id):
    level = load_level(f"data/levels/{level_id}.json")
    engine = GameEngine(level)
    actual_chain = []

    while not engine.is_solved():
        response = engine.auto_solve_step()
        assert response is not None, (
            f"{level_id} became stuck after {len(actual_chain)} moves"
        )
        assert response.proved_verdict is level.hidden_solution[response.cell_id]
        assert response.revealed_clue is level.clues[f"clue_{response.cell_id}"]
        actual_chain.append(response.cell_id)

    assert tuple(actual_chain) == EXPECTED_CHAINS[level_id]
    assert len(set(actual_chain)) == len(actual_chain) == 24


def test_level_05_requires_cross_grid_revisits_and_has_no_empty_clues():
    level = load_level("data/levels/level_05.json")
    chain = EXPECTED_CHAINS["level_05"]
    rows = tuple(int(cell_id[1:]) for cell_id in chain)

    assert all(clue.type is not ClueType.NONE for clue in level.clues.values())

    # The route repeatedly moves between earlier and later rows instead of
    # clearing the board in visual order, so prior evidence must be retained.
    assert sum(left != right for left, right in zip(rows, rows[1:])) >= 10
    assert sum(right < left for left, right in zip(rows, rows[1:])) >= 3


def test_level_06_is_a_complete_cross_grid_knowledge_chain():
    level = load_level("data/levels/level_06.json")
    chain = EXPECTED_CHAINS["level_06"]
    rows = tuple(int(cell_id[1:]) for cell_id in chain)

    assert level.initial_revealed == ("D3",)
    assert all(clue.type is not ClueType.NONE for clue in level.clues.values())
    assert sum(left != right for left, right in zip(rows, rows[1:])) >= 7
    assert sum(right < left for left, right in zip(rows, rows[1:])) >= 3
