# game/game_engine.py
from core.enums import SubmissionResult, Verdict
from core.models import AgentMove, Level, PublicState, SubmissionResponse
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

    def auto_solve_step(self) -> SubmissionResponse | None:
        """Apply one forced move, or return None when none is available."""
        move = self.get_hint()
        if move is None:
            return None
        return self.submit_verdict(move.cell_id, move.verdict)

    def restart(self) -> None:
        self._state = self._create_initial_state()

    def is_solved(self) -> bool:
        return (
            len(self._state.proved_verdicts)
            == len(self._level.cells)
        )

    def get_level_id(self) -> str:
        return self._level.id
