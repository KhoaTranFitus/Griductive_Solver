# game/public_state.py
from core.models import Level, PublicState
from game.game_state import GameState


def build_public_state(
    level: Level,
    game_state: GameState,
) -> PublicState:
    cells_by_id = {cell.id: cell for cell in level.cells}
    ordered_revealed = list(game_state.reveal_order)
    ordered_revealed.extend(
        cell.id
        for cell in level.cells
        if cell.id in game_state.revealed_cells
        and cell.id not in set(ordered_revealed)
    )
    revealed_clues = tuple(
        level.get_clue(cells_by_id[cell_id].clue_id)
        for cell_id in ordered_revealed
    )

    unresolved_cells = tuple(
        cell.id
        for cell in level.cells
        if cell.id not in game_state.proved_verdicts
    )

    return PublicState(
        level_id=level.id,
        size=level.size,
        cells=level.cells,
        revealed_clues=revealed_clues,
        proved_verdicts=dict(game_state.proved_verdicts),
        unresolved_cells=unresolved_cells,
    )
