# game/game_engine.py
from core.models import Level, PublicState
from game.game_state import GameState
from game.public_state import build_public_state


class GameEngine:
    def __init__(self, level: Level):
        self._level = level
        self._state = self._create_initial_state()

    def _create_initial_state(self) -> GameState:
        initial_verdicts = {
            cell_id: self._level.hidden_solution[cell_id]
            for cell_id in self._level.initial_revealed
        }

        return GameState(
            revealed_cells=set(self._level.initial_revealed),
            proved_verdicts=initial_verdicts,
        )

    def get_public_state(self) -> PublicState:
        return build_public_state(
            self._level,
            self._state,
        )

    def restart(self) -> None:
        self._state = self._create_initial_state()

    def is_solved(self) -> bool:
        return (
            len(self._state.proved_verdicts)
            == len(self._level.cells)
        )

    def get_level_id(self) -> str:
        return self._level.id