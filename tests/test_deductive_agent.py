from core.enums import Verdict
from game.level_loader import load_level
from game.public_state import build_public_state
from game.game_state import GameState
from logic.deductive_agent import DeductiveAgent


def test_agent_finds_first_forced_move_from_initial_public_state():
    level = load_level("data/levels/level_01.json")
    state = GameState(
        revealed_cells={"A1"},
        proved_verdicts={"A1": Verdict.INNOCENT},
    )
    public_state = build_public_state(level, state)

    classifications = DeductiveAgent().classify_all(public_state)

    assert classifications["B1"] is Verdict.CRIMINAL
    assert DeductiveAgent().choose_next_move(public_state).cell_id == "B1"


def test_agent_reports_inconsistent_public_knowledge():
    level = load_level("data/levels/level_01.json")
    state = GameState(
        revealed_cells={"A1"},
        proved_verdicts={
            "A1": Verdict.INNOCENT,
            "B1": Verdict.INNOCENT,
        },
    )
    public_state = build_public_state(level, state)

    classifications = DeductiveAgent().classify_all(public_state)

    assert classifications
    assert set(classifications.values()) == {Verdict.INCONSISTENT}
    assert DeductiveAgent().choose_next_move(public_state) is None
