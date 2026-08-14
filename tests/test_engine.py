# tests/test_engine.py
from core.enums import Verdict
from game.game_engine import GameEngine
from game.level_loader import load_level


def test_initial_public_state():
    level = load_level("data/levels/level_01.json")
    engine = GameEngine(level)

    public_state = engine.get_public_state()

    assert public_state.level_id == "level_01"
    assert public_state.size == 3
    assert len(public_state.cells) == 9

    assert len(public_state.revealed_clues) == 1
    assert public_state.revealed_clues[0].id == "clue_A1"

    assert public_state.proved_verdicts == {
        "A1": Verdict.CRIMINAL
    }

    assert public_state.unresolved_cells == (
        "B1",
        "C1",
        "A2",
        "B2",
        "C2",
        "A3",
        "B3",
        "C3",
    )


def test_public_state_does_not_expose_hidden_solution():
    level = load_level("data/levels/level_01.json")
    engine = GameEngine(level)

    public_state = engine.get_public_state()

    assert not hasattr(public_state, "hidden_solution")
    assert not hasattr(public_state, "solution")
    assert not hasattr(public_state, "unrevealed_clues")


def test_engine_is_not_solved_initially():
    level = load_level("data/levels/level_01.json")
    engine = GameEngine(level)

    assert engine.is_solved() is False


def test_restart_restores_initial_state():
    level = load_level("data/levels/level_01.json")
    engine = GameEngine(level)

    # Tạm thay đổi state để kiểm tra restart.
    engine._state.reveal_cell(
        "B1",
        Verdict.CRIMINAL,
    )

    assert "B1" in engine.get_public_state().proved_verdicts

    engine.restart()
    public_state = engine.get_public_state()

    assert public_state.proved_verdicts == {
        "A1": Verdict.CRIMINAL
    }

    assert "B1" not in public_state.proved_verdicts
