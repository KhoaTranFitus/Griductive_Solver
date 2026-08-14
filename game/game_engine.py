# game/game_engine.py
from core.enums import DeductionStatus, SubmissionResult, Verdict
from core.models import (
    AgentMove,
    DeductionRunResult,
    DeductionStep,
    Level,
    PublicState,
    SolverStatistics,
    SubmissionResponse,
)
from game.game_state import GameState
from game.public_state import build_public_state
from logic.deductive_agent import DeductiveAgent


class GameEngine:
    def __init__(
        self,
        level: Level,
        agent: DeductiveAgent | None = None,
    ) -> None:
        self._level = level
        self._agent = agent if agent is not None else DeductiveAgent()
        self._state = self._create_initial_state()

    def _create_initial_state(self) -> GameState:
        initial_verdicts = {
            cell_id: self._level.hidden_solution[cell_id]
            for cell_id in self._level.initial_revealed
        }

        return GameState(
            revealed_cells=set(self._level.initial_revealed),
            proved_verdicts=initial_verdicts,
            reveal_order=list(self._level.initial_revealed),
        )

    def get_public_state(self) -> PublicState:
        return build_public_state(
            self._level,
            self._state,
        )

    def submit_verdict(
        self,
        cell_id: str,
        verdict: Verdict,
    ) -> SubmissionResponse:
        """Submit a verdict and reveal a cell only when logically entailed."""
        if verdict not in {Verdict.CRIMINAL, Verdict.INNOCENT}:
            raise ValueError(
                "A submitted verdict must be CRIMINAL or INNOCENT."
            )

        cell = self._level.get_cell(cell_id)
        existing_verdict = self._state.proved_verdicts.get(cell_id)

        if existing_verdict is not None:
            result = (
                SubmissionResult.ACCEPTED
                if existing_verdict is verdict
                else SubmissionResult.CONTRADICTED
            )
            return SubmissionResponse(
                result=result,
                cell_id=cell_id,
                submitted_verdict=verdict,
                proved_verdict=existing_verdict,
                revealed_clue=self._level.get_clue(cell.clue_id),
                message="Cell has already been resolved.",
            )

        public_state = self.get_public_state()
        classify_one = getattr(self._agent, "classify_one", None)
        if callable(classify_one):
            proved_verdict = classify_one(public_state, cell_id)
        else:
            classifications = self._agent.classify_all(public_state)
            proved_verdict = classifications.get(cell_id, Verdict.UNKNOWN)

        if proved_verdict is Verdict.INCONSISTENT:
            return SubmissionResponse(
                result=SubmissionResult.INCONSISTENT,
                cell_id=cell_id,
                submitted_verdict=verdict,
                proved_verdict=Verdict.INCONSISTENT,
                message="The current knowledge base is inconsistent.",
            )

        if proved_verdict is Verdict.UNKNOWN:
            return SubmissionResponse(
                result=SubmissionResult.NOT_PROVABLE,
                cell_id=cell_id,
                submitted_verdict=verdict,
                proved_verdict=Verdict.UNKNOWN,
                message="The submitted verdict is not logically provable.",
            )

        if proved_verdict is not verdict:
            return SubmissionResponse(
                result=SubmissionResult.CONTRADICTED,
                cell_id=cell_id,
                submitted_verdict=verdict,
                proved_verdict=proved_verdict,
                message="The opposite verdict is logically forced.",
            )

        self._state.reveal_cell(cell_id, proved_verdict)
        revealed_clue = self._level.get_clue(cell.clue_id)

        return SubmissionResponse(
            result=SubmissionResult.ACCEPTED,
            cell_id=cell_id,
            submitted_verdict=verdict,
            proved_verdict=proved_verdict,
            revealed_clue=revealed_clue,
            message="The verdict was accepted and the clue was revealed.",
        )

    def get_hint(self) -> AgentMove | None:
        """Return the next forced move without changing game state."""
        public_state = self.get_public_state()
        move = self._agent.choose_next_move(public_state)

        if move is None:
            return None
        if move.cell_id not in public_state.unresolved_cells:
            raise ValueError("The agent returned a resolved or unknown cell.")
        if move.verdict not in {Verdict.CRIMINAL, Verdict.INNOCENT}:
            raise ValueError("The agent returned a non-final verdict.")

        return move

    def auto_solve_step(
        self,
        proved_move: AgentMove | None = None,
    ) -> SubmissionResponse | None:
        """Apply one forced move, or return None when none is available."""
        move = proved_move if proved_move is not None else self.get_hint()
        if move is None:
            return None

        if move.cell_id not in self.get_public_state().unresolved_cells:
            return None
        if move.verdict not in {Verdict.CRIMINAL, Verdict.INNOCENT}:
            raise ValueError("The agent returned a non-final verdict.")

        # ``get_hint`` has already proved this verdict against the current
        # public state. Applying it directly avoids repeating the same SAT
        # queries immediately in ``submit_verdict``.
        cell = self._level.get_cell(move.cell_id)
        self._state.reveal_cell(move.cell_id, move.verdict)
        return SubmissionResponse(
            result=SubmissionResult.ACCEPTED,
            cell_id=move.cell_id,
            submitted_verdict=move.verdict,
            proved_verdict=move.verdict,
            revealed_clue=self._level.get_clue(cell.clue_id),
            message="The verdict was accepted and the clue was revealed.",
        )

    def run_deduction_loop(self) -> DeductionRunResult:
        """Apply forced public deductions until reaching a terminal state.

        Completed trace steps are recorded only after ``submit_verdict`` has
        accepted a move and a new public clue is observable. A run-level
        ``STUCK`` status represents a consistent state whose unresolved cells
        are all unknown; no guess is submitted in that case.
        """
        trace: list[DeductionStep] = []

        while True:
            public_state = self.get_public_state()
            if self.is_solved():
                return DeductionRunResult(
                    status=DeductionStatus.SOLVED,
                    trace=tuple(trace),
                )

            move = self.get_hint()
            if move is None:
                classifications = self._agent.classify_all(public_state)
                status = (
                    DeductionStatus.INCONSISTENT
                    if any(
                        verdict is Verdict.INCONSISTENT
                        for verdict in classifications.values()
                    )
                    else DeductionStatus.STUCK
                )
                return DeductionRunResult(
                    status=status,
                    trace=tuple(trace),
                )

            sat_queries = ()
            solver_statistics = SolverStatistics()
            explain_move = getattr(self._agent, "explain_move", None)
            if callable(explain_move):
                explanation = explain_move(public_state, move)
                sat_queries = explanation.sat_queries
                solver_statistics = explanation.solver_statistics

            response = self.submit_verdict(move.cell_id, move.verdict)
            if response.result is SubmissionResult.INCONSISTENT:
                return DeductionRunResult(
                    status=DeductionStatus.INCONSISTENT,
                    trace=tuple(trace),
                )
            if response.result is not SubmissionResult.ACCEPTED:
                return DeductionRunResult(
                    status=DeductionStatus.STUCK,
                    trace=tuple(trace),
                )

            updated_public_state = self.get_public_state()
            active_clue_ids = tuple(
                clue.id for clue in public_state.revealed_clues
            )
            active_clue_id_set = set(active_clue_ids)
            newly_revealed_clue_ids = tuple(
                clue.id
                for clue in updated_public_state.revealed_clues
                if clue.id not in active_clue_id_set
            )
            if len(newly_revealed_clue_ids) != 1:
                raise RuntimeError(
                    "An accepted unresolved verdict must reveal exactly one "
                    "new public clue."
                )

            trace.append(DeductionStep(
                step_number=len(trace) + 1,
                active_clue_ids=active_clue_ids,
                target_cell=move.cell_id,
                sat_queries=sat_queries,
                verdict=move.verdict,
                newly_revealed_clue_id=newly_revealed_clue_ids[0],
                solver_statistics=solver_statistics,
            ))

    def restart(self) -> None:
        self._state = self._create_initial_state()

    def is_solved(self) -> bool:
        return (
            len(self._state.proved_verdicts)
            == len(self._level.cells)
        )

    def get_level_id(self) -> str:
        return self._level.id
