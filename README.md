# GriductiveSolver

GriductiveSolver is a desktop logic game in which every suspect occupies a
cell and reveals a clue. A dependency-free SAT solver converts visible clues
to CNF and accepts a verdict only when it follows from public information.

The repository includes six authored levels: two 3x3, two 4x4, and two 5x5
boards. Levels 5 and 6 have deterministic full-chain deduction tests.

## Features

- CustomTkinter interface with manual verdicts, hints, and auto-solve.
- Public-knowledge boundary: the agent cannot inspect the hidden solution.
- Encoders for facts, cardinality, parity, count comparison, connectivity, and
  neighbor-count properties.
- Dependency-free deterministic DPLL solver with assumptions and statistics.
- Level validation against the hidden solution.
- CSV experiments for runtime, SAT calls, clauses, uniqueness, and status.
- Background auto-solve work that does not block the GUI event loop.

## Requirements

- Python 3.11 or newer
- `customtkinter>=5.2.0`
- `Pillow>=10.0.0`
- `pytest` for tests

## Installation and launch

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Run commands from the repository root because level and asset paths are
relative to it.

## Tests

```powershell
python -m pip install pytest
python -m pytest -q
```

Run the hard-level regression separately with:

```powershell
python -m pytest tests/test_hard_level_chains.py -q
```

## Experiments

```powershell
python experiments/run_experiments.py
```

This writes `results/experiments.csv`. Deduction and uniqueness use separate
solver instances, keeping their metrics independent.

## Project structure

```text
core/         shared models, enums, and exceptions
data/         character metadata and authored levels
game/         loading, validation, public state, and engine rules
logic/        region resolution, CNF, DPLL, and deduction
gui/          CustomTkinter application and components
experiments/  repeatable catalog benchmark
results/      generated experiment CSV
tests/        unit, equivalence, and full-chain tests
docs/         architecture and data contracts
```

## Solver flow

1. The engine builds a `PublicState` with revealed clues and proved verdicts.
2. The encoder converts that public knowledge to CNF.
3. Entailment solves the CNF under innocent and criminal assumptions.
4. A verdict is returned only when the opposite assumption is unsatisfiable.
5. Revealing the cell exposes its clue and begins the next step.

Generic truth-table encodings are limited to 14 distinct variables because
their cost is exponential (`2^n`). Larger constraints need a smaller region or
a dedicated polynomial-size encoder. Current authored levels use at most 10.

## Level authoring

Levels in `data/levels` must pass `validate_level()`. A board must cover every
position, own one clue and hidden verdict per cell, and contain only clues true
under its hidden solution. Production levels must also be solvable from public
information without guessing.

See [data format](docs/data_format.md) and
[architecture](docs/architecture.md) for complete contracts.
