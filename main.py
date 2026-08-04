# main.py
from game.level_loader import load_level
from game.level_validator import validate_level
from game.game_engine import GameEngine
from logic.semantic_evaluator import evaluate_clue

def main() -> None:
    level = load_level("data/levels/level_01.json")
    validate_level(level)

    assignment = {
        cell_id: verdict.value == "CRIMINAL"
        for cell_id, verdict
        in level.hidden_solution.items()
    }

    print(f"Loaded level: {level.title}")
    print(f"Grid size: {level.size}x{level.size}")
    print(f"Cells: {len(level.cells)}")
    print(f"Clues: {len(level.clues)}")
    print()

    for clue in level.clues.values():
        result = evaluate_clue(
            clue,
            assignment,
            level.cells,
        )

        print(
            f"{clue.id}: {result} | "
            f"{clue.display_text}"
        )
    engine = GameEngine(level)
    public_state = engine.get_public_state()

    print()
    print("PUBLIC STATE")
    print(f"Level: {public_state.level_id}")

    print("Revealed clues:")
    for clue in public_state.revealed_clues:
        print(f"- {clue.id}: {clue.display_text}")

    print("Proved verdicts:")
    for cell_id, verdict in public_state.proved_verdicts.items():
        print(f"- {cell_id}: {verdict.value}")

    print(
        "Unresolved cells:",
        ", ".join(public_state.unresolved_cells),
    )

if __name__ == "__main__":
    main()