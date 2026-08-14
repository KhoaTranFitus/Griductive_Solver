import pytest

from game.game_engine import GameEngine
from game.level_loader import load_level


EXPECTED_CHAINS = {
    "level_05": (
        "B5", "E2", "D5", "C5", "B1", "C1", "A3", "E5",
        "D1", "E1", "A2", "B2", "C2", "D2", "B3", "C3",
        "D3", "E3", "C4", "D4", "E4", "A4", "B4", "A5",
    ),
    "level_06": (
        "A1", "E5", "D1", "B1", "C1", "E1", "A3", "A2",
        "B3", "D3", "B2", "C2", "D2", "E2", "E3", "A4",
        "B4", "C4", "D4", "E4", "A5", "B5", "C5", "D5",
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
