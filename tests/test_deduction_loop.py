from core.enums import (
    ClueType,
    DeductionStatus,
    SubmissionResult,
    Verdict,
)
from core.models import (
    AgentMove,
    Cell,
    Clue,
    DeductionRunResult,
    Level,
    PublicState,
    SATQueryTrace,
    SolverStatistics,
)
from game.game_engine import GameEngine
from game.level_loader import load_level
from logic.deductive_agent import DeductiveAgent


class RecordingAgent(DeductiveAgent):
    def __init__(self) -> None:
        super().__init__()
        self.received_states: list[PublicState] = []

    def choose_next_move(
        self,
        public_state: PublicState,
    ) -> AgentMove | None:
        self.received_states.append(public_state)
        return super().choose_next_move(public_state)


class RecordingEngine(GameEngine):
    def __init__(self, level: Level, agent=None) -> None:
        self.submissions: list[
            tuple[str, Verdict, SubmissionResult]
        ] = []
        super().__init__(level, agent=agent)

    def submit_verdict(
        self,
        cell_id: str,
        verdict: Verdict,
    ):
        response = super().submit_verdict(cell_id, verdict)
        self.submissions.append((cell_id, verdict, response.result))
        return response


class RejectedMoveAgent:
    def __init__(self) -> None:
        self.choose_states: list[PublicState] = []
        self.classify_states: list[PublicState] = []

    def choose_next_move(
        self,
        public_state: PublicState,
    ) -> AgentMove:
        self.choose_states.append(public_state)
        return AgentMove("B1", Verdict.CRIMINAL)

    def classify_all(
        self,
        public_state: PublicState,
    ) -> dict[str, Verdict]:
        self.classify_states.append(public_state)
        return {"B1": Verdict.UNKNOWN}


def make_cell(cell_id: str, row: int, column: int) -> Cell:
    return Cell(
        id=cell_id,
        row=row,
        column=column,
        character_id=f"character_{cell_id}",
        clue_id=f"clue_{cell_id}",
    )


def make_fact(
    clue_id: str,
    owner_cell: str,
    person: str,
    verdict: Verdict,
) -> Clue:
    return Clue(
        id=clue_id,
        owner_cell=owner_cell,
        type=ClueType.FACT,
        data={"person": person, "status": verdict.value},
        display_text="",
    )


def make_stuck_level() -> Level:
    cell = make_cell("A1", 1, 1)
    clue = make_fact(
        "clue_A1",
        owner_cell="A1",
        person="A1",
        verdict=Verdict.CRIMINAL,
    )
    return Level(
        id="stuck-hidden-fact",
        title="Hidden fact must not be used",
        size=1,
        cells=(cell,),
        clues={clue.id: clue},
        initial_revealed=(),
        hidden_solution={"A1": Verdict.CRIMINAL},
    )


def make_inconsistent_level() -> Level:
    a1 = make_cell("A1", 1, 1)
    b1 = make_cell("B1", 1, 2)
    revealed_contradiction = make_fact(
        "clue_A1",
        owner_cell="A1",
        person="A1",
        verdict=Verdict.INNOCENT,
    )
    hidden_clue = make_fact(
        "clue_B1",
        owner_cell="B1",
        person="B1",
        verdict=Verdict.CRIMINAL,
    )
    return Level(
        id="inconsistent-public-knowledge",
        title="Contradictory revealed clue",
        size=2,
        cells=(a1, b1),
        clues={
            revealed_contradiction.id: revealed_contradiction,
            hidden_clue.id: hidden_clue,
        },
        initial_revealed=("A1",),
        hidden_solution={
            "A1": Verdict.CRIMINAL,
            "B1": Verdict.CRIMINAL,
        },
    )


def statistic_projection(statistics: SolverStatistics):
    return (
        statistics.decisions,
        statistics.propagations,
        statistics.backtracks,
    )


def semantic_projection(result: DeductionRunResult):
    return (
        result.status,
        tuple(
            (
                step.step_number,
                step.active_clue_ids,
                step.target_cell,
                tuple(
                    (
                        query.assumptions,
                        query.satisfiable,
                        statistic_projection(query.statistics),
                    )
                    for query in step.sat_queries
                ),
                step.verdict,
                step.newly_revealed_clue_id,
                statistic_projection(step.solver_statistics),
            )
            for step in result.trace
        ),
    )


def assert_statistics(statistics: SolverStatistics) -> None:
    assert isinstance(statistics, SolverStatistics)
    assert statistics.decisions >= 0
    assert statistics.propagations >= 0
    assert statistics.backtracks >= 0
    assert statistics.runtime_ms >= 0.0


def test_real_agent_loop_updates_public_state_and_builds_accepted_trace():
    level = load_level("data/levels/level_01.json")
    agent = RecordingAgent()
    engine = RecordingEngine(level, agent=agent)

    result = engine.run_deduction_loop()

    assert result.status is DeductionStatus.SOLVED
    assert engine.is_solved()
    assert len(result.trace) == len(level.cells) - len(level.initial_revealed)
    assert len(agent.received_states) == len(result.trace)
    assert len(engine.submissions) == len(result.trace)

    first, second = result.trace[:2]
    assert (
        first.step_number,
        first.active_clue_ids,
        first.target_cell,
        first.verdict,
        first.newly_revealed_clue_id,
    ) == (
        1,
        ("clue_A1",),
        "B1",
        Verdict.CRIMINAL,
        "clue_B1",
    )
    assert (
        second.step_number,
        second.active_clue_ids,
        second.target_cell,
        second.verdict,
        second.newly_revealed_clue_id,
    ) == (
        2,
        ("clue_A1", "clue_B1"),
        "C1",
        Verdict.INNOCENT,
        "clue_C1",
    )
    assert [
        (query.assumptions, query.satisfiable)
        for query in first.sat_queries
    ] == [
        ((), True),
        ((-2,), False),
    ]
    assert [
        (query.assumptions, query.satisfiable)
        for query in second.sat_queries
    ] == [
        ((), True),
        ((-3,), True),
        ((3,), False),
    ]

    states_after_steps = [
        *agent.received_states[1:],
        engine.get_public_state(),
    ]
    for step_number, (step, before, after, submission) in enumerate(
        zip(
            result.trace,
            agent.received_states,
            states_after_steps,
            engine.submissions,
        ),
        start=1,
    ):
        before_clue_ids = tuple(clue.id for clue in before.revealed_clues)
        after_clue_ids = tuple(clue.id for clue in after.revealed_clues)

        assert step.step_number == step_number
        assert step.active_clue_ids == before_clue_ids
        assert step.newly_revealed_clue_id not in before_clue_ids
        assert after_clue_ids == (
            *before_clue_ids,
            step.newly_revealed_clue_id,
        )
        assert step.target_cell not in before.proved_verdicts
        assert after.proved_verdicts[step.target_cell] is step.verdict
        assert step.target_cell not in after.unresolved_cells
        assert submission == (
            step.target_cell,
            step.verdict,
            SubmissionResult.ACCEPTED,
        )
        assert not hasattr(before, "hidden_solution")
        assert isinstance(step.sat_queries, tuple)
        assert step.sat_queries
        assert_statistics(step.solver_statistics)
        for query in step.sat_queries:
            assert isinstance(query, SATQueryTrace)
            assert isinstance(query.assumptions, tuple)
            assert isinstance(query.satisfiable, bool)
            assert_statistics(query.statistics)

    assert "clue_C1" not in {
        clue.id for clue in agent.received_states[0].revealed_clues
    }
    assert "clue_C1" not in {
        clue.id for clue in agent.received_states[1].revealed_clues
    }

    state_after_solving = engine.get_public_state()
    submission_count = len(engine.submissions)
    choose_count = len(agent.received_states)

    already_solved_result = engine.run_deduction_loop()

    assert already_solved_result.status is DeductionStatus.SOLVED
    assert already_solved_result.trace == ()
    assert engine.get_public_state() == state_after_solving
    assert len(engine.submissions) == submission_count
    assert len(agent.received_states) == choose_count


def test_unknown_public_knowledge_stops_without_using_hidden_fact():
    agent = RecordingAgent()
    engine = RecordingEngine(make_stuck_level(), agent=agent)
    before = engine.get_public_state()

    result = engine.run_deduction_loop()

    assert result.status is DeductionStatus.STUCK
    assert result.trace == ()
    assert engine.submissions == []
    assert engine.get_public_state() == before
    assert not engine.is_solved()
    assert len(agent.received_states) == 1
    assert agent.received_states[0].revealed_clues == ()
    assert not hasattr(agent.received_states[0], "hidden_solution")


def test_inconsistent_public_knowledge_stops_without_submitting_move():
    agent = RecordingAgent()
    engine = RecordingEngine(make_inconsistent_level(), agent=agent)
    before = engine.get_public_state()

    result = engine.run_deduction_loop()

    assert result.status is DeductionStatus.INCONSISTENT
    assert result.trace == ()
    assert engine.submissions == []
    assert engine.get_public_state() == before
    assert not engine.is_solved()
    assert len(agent.received_states) == 1
    assert tuple(
        clue.id for clue in agent.received_states[0].revealed_clues
    ) == ("clue_A1",)
    assert not hasattr(agent.received_states[0], "hidden_solution")


def test_rejected_forced_move_stops_without_trace_or_state_change():
    level = load_level("data/levels/level_01.json")
    agent = RejectedMoveAgent()
    engine = RecordingEngine(level, agent=agent)
    before = engine.get_public_state()

    result = engine.run_deduction_loop()

    assert result.status is DeductionStatus.STUCK
    assert result.trace == ()
    assert engine.submissions == [
        ("B1", Verdict.CRIMINAL, SubmissionResult.NOT_PROVABLE),
    ]
    assert engine.get_public_state() == before
    assert len(agent.choose_states) == 1
    assert len(agent.classify_states) == 1
    assert agent.choose_states[0] == agent.classify_states[0] == before
    assert not hasattr(agent.choose_states[0], "hidden_solution")
    assert tuple(
        clue.id for clue in agent.choose_states[0].revealed_clues
    ) == ("clue_A1",)


def test_real_agent_deduction_sequence_is_semantically_deterministic():
    first = GameEngine(
        load_level("data/levels/level_01.json")
    ).run_deduction_loop()
    second = GameEngine(
        load_level("data/levels/level_01.json")
    ).run_deduction_loop()

    assert semantic_projection(first) == semantic_projection(second)
