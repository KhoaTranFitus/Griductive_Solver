# GriductiveSolver Architecture

## Layers

```text
main.py
  -> game.level_loader + game.level_validator
  -> game.game_engine
       -> game.public_state
       -> logic.deductive_agent
            -> logic.cnf_encoder
            -> logic.entailment -> logic.dpll
  -> gui.app -> gui.game_screen
```

- `core`: shared domain models, enums, and exceptions.
- `data`: authored JSON; no executable game behavior.
- `game`: trusted application boundary. It validates private level data but
  exposes only `PublicState` to the agent and GUI.
- `logic`: region semantics, CNF, SAT, entailment, and uniqueness checks.
- `gui`: presentation and interaction through the `GameEngine` API.
- `experiments`: reproducible measurements over the catalog.

## Trust boundary

`Level` contains every clue and the hidden solution. `PublicState` contains
only cells, revealed clues, proved verdicts, and unresolved IDs. The
`DeductiveAgent` accepts `PublicState`, never `Level`, so a move is derived from
visible information rather than private game data.

## Deduction pipeline

1. `GameEngine` creates the current `PublicState`.
2. `VariableMap` assigns stable row-major integers to cells.
3. `build_knowledge_base()` encodes revealed clues and proved verdicts.
4. Entailment calls DPLL with temporary positive and negative assumptions.
5. `DeductiveAgent` returns the first forced move in row-major order.
6. `GameEngine` reveals exactly that cell and its clue.

Auto-solve does not recompute a move while applying it. `GameScreen` performs
the expensive hint search on a daemon worker and polls the result from Tk's
event thread; all widget changes remain on the event thread.

## CNF size policy

Cardinality clues use combination encodings. Complex predicates use
`_encode_truth_constraint()`, which excludes every invalid assignment and is
`O(2^n)` in the number of distinct involved cells. It has a ceiling of 14
variables; the current catalog uses at most 10. A larger constraint needs a
dedicated encoder with auxiliary variables instead of a higher ceiling.

## Verification

- Unit tests cover loading, regions, encoders, DPLL, entailment, and engine.
- Semantic-equivalence tests compare direct clue evaluation with CNF.
- `test_hard_level_chains.py` locks complete Level 5–6 solve sequences.
- Experiments record CNF size, SAT statistics, runtime, uniqueness, and final
  deduction status in `results/experiments.csv`.
