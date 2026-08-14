from copy import deepcopy

import logic.deductive_agent as deductive_agent_module
from core.enums import ClueType, Verdict
from core.models import AgentMove, Cell, Clue, PublicState
from game.level_loader import load_level
from game.public_state import build_public_state
from game.game_state import GameState
from logic.deductive_agent import DeductiveAgent
from logic.variable_map import VariableMap


def make_cell(cell_id: str, row: int, column: int) -> Cell:
    return Cell(
        id=cell_id,
        row=row,
        column=column,
        character_id=f"character_{cell_id}",
        clue_id=f"clue_{cell_id}",
    )


def make_public_state(
    cells: tuple[Cell, ...],
    *,
    revealed_clues: tuple[Clue, ...] = (),
    proved_verdicts: dict[str, Verdict] | None = None,
    unresolved_cells: tuple[str, ...] | None = None,
) -> PublicState:
    proved = {} if proved_verdicts is None else proved_verdicts
    unresolved = (
        tuple(
            cell.id
            for cell in cells
            if cell.id not in proved
        )
        if unresolved_cells is None
        else unresolved_cells
    )
    size = max(
        (
            max(cell.row, cell.column)
            for cell in cells
        ),
        default=0,
    )
    return PublicState(
        level_id="agent-test",
        size=size,
        cells=cells,
        revealed_clues=revealed_clues,
        proved_verdicts=proved,
        unresolved_cells=unresolved,
    )


def make_fact(
    clue_id: str,
    cell_id: str,
    verdict: Verdict,
) -> Clue:
    return Clue(
        id=clue_id,
        owner_cell=cell_id,
        type=ClueType.FACT,
        data={
            "person": cell_id,
            "status": verdict.value,
        },
        display_text="",
    )


def test_agent_finds_first_forced_move_from_initial_public_state():
    level = load_level("data/levels/level_01.json")
    state = GameState(
        revealed_cells={"A1"},
        proved_verdicts={"A1": Verdict.CRIMINAL},
    )
    public_state = build_public_state(level, state)

    classifications = DeductiveAgent().classify_all(public_state)

    assert classifications["B2"] is Verdict.CRIMINAL
    assert DeductiveAgent().choose_next_move(public_state).cell_id == "B2"


def test_agent_reports_inconsistent_public_knowledge():
    level = load_level("data/levels/level_01.json")
    state = GameState(
        revealed_cells={"A1"},
        proved_verdicts={
            "A1": Verdict.CRIMINAL,
            "B2": Verdict.INNOCENT,
        },
    )
    public_state = build_public_state(level, state)

    classifications = DeductiveAgent().classify_all(public_state)

    assert classifications
    assert set(classifications.values()) == {Verdict.INCONSISTENT}
    assert DeductiveAgent().choose_next_move(public_state) is None


def test_classify_all_uses_public_encoder_and_real_variable_map_once(
    monkeypatch,
):
    cells = (
        make_cell("A10", 10, 1),
        make_cell("B2", 2, 2),
        make_cell("B1", 1, 2),
        make_cell("A2", 2, 1),
    )
    public_state = make_public_state(
        cells,
        proved_verdicts={"B1": Verdict.INNOCENT},
        unresolved_cells=("A10", "B2", "A2"),
    )
    knowledge_base = [[-1]]
    build_calls = []
    classify_calls = []

    class NoDirectSolve:
        def solve(self, clauses, assumptions=None):
            raise AssertionError(
                "DeductiveAgent must delegate SAT checks to entailment."
            )

    solver = NoDirectSolve()

    def fake_build_knowledge_base(
        revealed_clues,
        proved_verdicts,
        received_cells,
        variable_map,
    ):
        build_calls.append((
            revealed_clues,
            proved_verdicts,
            received_cells,
            variable_map,
        ))
        return knowledge_base

    verdicts_by_variable = {
        2: Verdict.CRIMINAL,
        3: Verdict.UNKNOWN,
        4: Verdict.INNOCENT,
    }

    def fake_classify_character(clauses, variable_id, received_solver):
        assert clauses is knowledge_base
        classify_calls.append((variable_id, received_solver))
        return verdicts_by_variable[variable_id]

    monkeypatch.setattr(
        deductive_agent_module,
        "build_knowledge_base",
        fake_build_knowledge_base,
    )
    monkeypatch.setattr(
        deductive_agent_module,
        "classify_character",
        fake_classify_character,
    )

    classifications = DeductiveAgent(solver=solver).classify_all(
        public_state
    )

    assert list(classifications) == ["A2", "B2", "A10"]
    assert classifications == {
        "A2": Verdict.CRIMINAL,
        "B2": Verdict.UNKNOWN,
        "A10": Verdict.INNOCENT,
    }
    assert len(build_calls) == 1
    revealed, proved, received_cells, variable_map = build_calls[0]
    assert revealed is public_state.revealed_clues
    assert proved is public_state.proved_verdicts
    assert received_cells is public_state.cells
    assert isinstance(variable_map, VariableMap)
    assert variable_map.get_variable("B1") == 1
    assert classify_calls == [
        (2, solver),
        (3, solver),
        (4, solver),
    ]


def test_choose_next_move_skips_unknown_before_forced_verdict(
    monkeypatch,
):
    cells = (
        make_cell("A10", 10, 1),
        make_cell("B2", 2, 2),
        make_cell("A2", 2, 1),
    )
    public_state = make_public_state(
        cells,
        unresolved_cells=("A10", "B2", "A2"),
    )
    verdicts_by_variable = {
        1: Verdict.UNKNOWN,
        2: Verdict.INNOCENT,
        3: Verdict.CRIMINAL,
    }

    monkeypatch.setattr(
        deductive_agent_module,
        "build_knowledge_base",
        lambda revealed, proved, received_cells, variable_map: [],
    )
    monkeypatch.setattr(
        deductive_agent_module,
        "classify_character",
        lambda clauses, variable_id, solver: verdicts_by_variable[
            variable_id
        ],
    )

    move = DeductiveAgent().choose_next_move(public_state)

    assert move == AgentMove(
        cell_id="B2",
        verdict=Verdict.INNOCENT,
    )


def test_multiple_forced_verdicts_choose_first_row_major_deterministically():
    cells = (
        make_cell("A10", 10, 1),
        make_cell("B2", 2, 2),
        make_cell("A2", 2, 1),
    )
    public_state = make_public_state(
        cells,
        revealed_clues=(
            make_fact("fact_A10", "A10", Verdict.CRIMINAL),
            make_fact("fact_B2", "B2", Verdict.CRIMINAL),
            make_fact("fact_A2", "A2", Verdict.INNOCENT),
        ),
        unresolved_cells=("A10", "B2", "A2"),
    )
    agent = DeductiveAgent()

    first_classification = agent.classify_all(public_state)
    second_classification = agent.classify_all(public_state)
    first_move = agent.choose_next_move(public_state)
    second_move = agent.choose_next_move(public_state)

    assert list(first_classification) == ["A2", "B2", "A10"]
    assert first_classification == second_classification
    assert first_move == second_move == AgentMove(
        cell_id="A2",
        verdict=Verdict.INNOCENT,
    )


def test_all_unknown_returns_no_move():
    cells = (
        make_cell("B1", 1, 2),
        make_cell("A1", 1, 1),
    )
    public_state = make_public_state(
        cells,
        unresolved_cells=("B1", "A1"),
    )
    agent = DeductiveAgent()

    classifications = agent.classify_all(public_state)

    assert list(classifications) == ["A1", "B1"]
    assert set(classifications.values()) == {Verdict.UNKNOWN}
    assert agent.choose_next_move(public_state) is None


def test_solved_public_state_returns_empty_without_building_kb(monkeypatch):
    public_state = make_public_state(
        (make_cell("A1", 1, 1),),
        proved_verdicts={"A1": Verdict.CRIMINAL},
        unresolved_cells=(),
    )

    def fail_if_called(*args, **kwargs):
        raise AssertionError("A solved state does not need a knowledge base.")

    monkeypatch.setattr(
        deductive_agent_module,
        "build_knowledge_base",
        fail_if_called,
    )
    agent = DeductiveAgent()

    assert agent.classify_all(public_state) == {}
    assert agent.choose_next_move(public_state) is None


def test_agent_uses_only_public_data_and_does_not_mutate_state():
    cells = (
        make_cell("B1", 1, 2),
        make_cell("A1", 1, 1),
    )
    public_state = make_public_state(
        cells,
        revealed_clues=(
            make_fact("revealed_fact", "B1", Verdict.CRIMINAL),
        ),
        proved_verdicts={"A1": Verdict.INNOCENT},
        unresolved_cells=("B1",),
    )
    before = deepcopy(public_state)
    agent = DeductiveAgent()

    classifications = agent.classify_all(public_state)
    move = agent.choose_next_move(public_state)

    assert not hasattr(public_state, "hidden_solution")
    assert classifications == {"B1": Verdict.CRIMINAL}
    assert move == AgentMove("B1", Verdict.CRIMINAL)
    assert public_state == before
