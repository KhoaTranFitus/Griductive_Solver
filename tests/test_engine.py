# tests/test_engine.py
import pytest

from core.enums import SubmissionResult, Verdict
from core.models import AgentMove
from game.game_engine import GameEngine
from game.level_loader import load_level


class StubAgent:
    def __init__(self, classifications, next_move=None):
        self.classifications = classifications
        self.next_move = next_move
        self.received_states = []

    def classify_all(self, public_state):
        self.received_states.append(public_state)
        return dict(self.classifications)

    def choose_next_move(self, public_state):
        self.received_states.append(public_state)
        return self.next_move


def make_engine(classifications):
    level = load_level("data/levels/level_01.json")
    agent = StubAgent(classifications)
    return GameEngine(level, agent=agent), agent


def test_submit_verdict_accepts_forced_value_and_reveals_clue():
    engine, agent = make_engine({"B1": Verdict.CRIMINAL})

    response = engine.submit_verdict("B1", Verdict.CRIMINAL)

    assert response.result is SubmissionResult.ACCEPTED
    assert response.proved_verdict is Verdict.CRIMINAL
    assert response.revealed_clue.id == "clue_B1"
    assert engine.get_public_state().proved_verdicts["B1"] is Verdict.CRIMINAL
    assert len(agent.received_states) == 1
    assert [
        clue.owner_cell for clue in engine.get_public_state().revealed_clues
    ] == ["A1", "B1"]


def test_submit_verdict_rejects_unknown_without_mutating_state():
    engine, _ = make_engine({"B1": Verdict.UNKNOWN})
    before = engine.get_public_state()

    response = engine.submit_verdict("B1", Verdict.CRIMINAL)

    assert response.result is SubmissionResult.NOT_PROVABLE
    assert engine.get_public_state() == before


def test_submit_verdict_reports_contradicted_without_mutating_state():
    engine, _ = make_engine({"B1": Verdict.INNOCENT})
    before = engine.get_public_state()

    response = engine.submit_verdict("B1", Verdict.CRIMINAL)

    assert response.result is SubmissionResult.CONTRADICTED
    assert response.proved_verdict is Verdict.INNOCENT
    assert engine.get_public_state() == before


def test_submit_verdict_reports_inconsistent_without_mutating_state():
    engine, _ = make_engine({"B1": Verdict.INCONSISTENT})
    before = engine.get_public_state()

    response = engine.submit_verdict("B1", Verdict.CRIMINAL)

    assert response.result is SubmissionResult.INCONSISTENT
    assert engine.get_public_state() == before


def test_submit_verdict_rejects_non_final_verdict():
    engine, _ = make_engine({})

    with pytest.raises(ValueError, match="CRIMINAL or INNOCENT"):
        engine.submit_verdict("B1", Verdict.UNKNOWN)


def test_submit_verdict_rejects_unknown_cell():
    engine, _ = make_engine({})

    with pytest.raises(KeyError, match="Cell not found"):
        engine.submit_verdict("Z9", Verdict.CRIMINAL)


def test_restart_restores_initial_public_state():
    engine, _ = make_engine({"B1": Verdict.CRIMINAL})
    initial_state = engine.get_public_state()
    engine.submit_verdict("B1", Verdict.CRIMINAL)

    engine.restart()

    assert engine.get_public_state() == initial_state


def test_get_hint_is_read_only():
    level = load_level("data/levels/level_01.json")
    move = AgentMove("B1", Verdict.CRIMINAL)
    agent = StubAgent({"B1": Verdict.CRIMINAL}, next_move=move)
    engine = GameEngine(level, agent=agent)
    before = engine.get_public_state()

    assert engine.get_hint() == move
    assert engine.get_public_state() == before


def test_auto_solve_step_applies_exactly_one_move():
    level = load_level("data/levels/level_01.json")
    move = AgentMove("B1", Verdict.CRIMINAL)
    agent = StubAgent({"B1": Verdict.CRIMINAL}, next_move=move)
    engine = GameEngine(level, agent=agent)

    response = engine.auto_solve_step()

    assert response is not None
    assert response.result is SubmissionResult.ACCEPTED
    assert set(engine.get_public_state().proved_verdicts) == {"A1", "B1"}


def test_auto_solve_step_returns_none_when_agent_has_no_move():
    engine, _ = make_engine({})

    assert engine.auto_solve_step() is None
