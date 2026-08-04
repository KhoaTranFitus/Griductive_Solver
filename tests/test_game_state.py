import pytest

from core.enums import Verdict
from game.game_state import GameState


def test_reveal_cell():
    state = GameState()

    state.reveal_cell(
        "B1",
        Verdict.CRIMINAL,
    )

    assert state.is_revealed("B1")
    assert state.is_resolved("B1")
    assert state.proved_verdicts["B1"] == Verdict.CRIMINAL


def test_cannot_reveal_unknown_verdict():
    state = GameState()

    with pytest.raises(ValueError):
        state.reveal_cell(
            "B1",
            Verdict.UNKNOWN,
        )


def test_reset_state():
    state = GameState(
        revealed_cells={"A1", "B1"},
        proved_verdicts={
            "A1": Verdict.INNOCENT,
            "B1": Verdict.CRIMINAL,
        },
        selected_cell="B1",
        solved=True,
    )

    state.reset(
        initial_revealed=("A1",),
        initial_verdicts={
            "A1": Verdict.INNOCENT,
        },
    )

    assert state.revealed_cells == {"A1"}
    assert state.proved_verdicts == {
        "A1": Verdict.INNOCENT
    }
    assert state.selected_cell is None
    assert state.solved is False