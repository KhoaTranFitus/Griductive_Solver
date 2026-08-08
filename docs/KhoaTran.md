# MEMBER LEADER — ARCHITECTURE, GAME ENGINE, LEVEL DESIGN, INTEGRATION, AND PROJECT MANAGEMENT

## 1. Role

The team leader is responsible for defining the shared architecture, controlling common data formats, implementing the central Game Engine, designing the official puzzle levels, integrating all modules, reviewing pull requests, and ensuring that the final system satisfies the project requirements.

The leader is not expected to rewrite the work assigned to other members. The leader's main technical responsibility is to make the modules work together through stable interfaces.

## 2. Main responsibilities

The leader owns the following work areas:

```text
Project architecture
Shared enums and models
Level JSON format
Level loading and validation
Region resolution
GameState and PublicState
Game Engine
Official level design
Puzzle validity checks
Module integration
Git workflow and code review
Project documentation
Final testing
```

## 3. Assigned files and folders

Primary files:

```text
main.py
README.md
requirements.txt
.gitignore

core/enums.py
core/models.py
core/exceptions.py

game/level_loader.py
game/level_validator.py
game/game_state.py
game/public_state.py
game/game_engine.py

logic/region_resolver.py
logic/semantic_evaluator.py

data/levels/level_01.json
data/levels/level_02.json
data/levels/level_03.json
data/levels/level_04.json
data/levels/level_05.json
data/levels/level_06.json

tests/test_loader.py
tests/test_regions.py
tests/test_game_state.py
tests/test_engine.py
tests/test_levels.py

docs/architecture.md
docs/data_format.md
docs/task_assignment.md
docs/level_design.md
```

The leader may update other files during integration, but should coordinate with the member who owns that module.

## 4. Shared architectural conventions

### 4.1 Cell coordinate convention

Columns use letters and rows use numbers:

```text
A1 B1 C1
A2 B2 C2
A3 B3 C3
```

Rules:

- Columns are ordered from left to right.
- Rows are ordered from top to bottom.
- Internal row and column indices begin at 1.
- Cell ordering is row-major.

### 4.2 Verdict convention

```text
True  = CRIMINAL
False = INNOCENT
```

Public verdict values:

```text
CRIMINAL
INNOCENT
UNKNOWN
INCONSISTENT
```

### 4.3 CNF convention

```python
CNF = list[list[int]]
Assignment = dict[int, bool]
```

### 4.4 Structured clue convention

Clues must be stored as structured data. Natural-language text is display-only.

Correct:

```json
{
  "id": "clue_A1",
  "owner_cell": "A1",
  "type": "EXACTLY",
  "data": {
    "k": 1,
    "region": {
      "type": "ROW",
      "index": 1
    }
  },
  "display_text": "Exactly one person in row 1 is a criminal."
}
```

Incorrect:

```json
{
  "clue": "Exactly one person in row 1 is a criminal."
}
```

The logic system must never parse free-form clue text.

## 5. Shared enums and models

The leader defines and controls:

```text
Verdict
SubmissionResult
ClueType
RegionType
CardState

Character
Cell
Region
Clue
Level
PublicState
AgentMove
SolverStatistics
SolverResult
SubmissionResponse
```

Changes to shared classes must be discussed before implementation because they may affect all members.

## 6. Game Engine versus Logic Agent

### Game Engine owns

```text
complete level data
hidden solution
all clues
unrevealed clues
revealed cells
proved verdicts
game progress
```

### Logic Agent receives only

```text
board cells
revealed clues
proved verdicts
unresolved cells
```

The Logic Agent must not receive the full `Level` object if that exposes hidden information.

## 7. Required Game Engine interfaces

```python
class GameEngine:
    def get_public_state(self) -> PublicState:
        ...

    def submit_verdict(
        self,
        cell_id: str,
        verdict: Verdict,
    ) -> SubmissionResponse:
        ...

    def restart(self) -> None:
        ...

    def is_solved(self) -> bool:
        ...
```

The GUI and Logic Agent must use these public interfaces rather than reading private fields.

## 8. Current leader implementation tasks

### Task 1 — Core project structure

Create and maintain the agreed folder structure.

Ensure package files are named:

```text
__init__.py
```

not:

```text
init.py
```

### Task 2 — Core enums and models

Implement the shared classes and values used by all members.

Requirements:

- Use explicit types.
- Use dataclasses where appropriate.
- Keep hidden verdicts out of `Character`.
- Keep hidden solution and unrevealed clues out of `PublicState`.

### Task 3 — Level Loader

Implement:

```python
def load_level(file_path: str) -> Level:
    ...
```

Responsibilities:

- Read JSON.
- Convert string values into enums.
- Create dataclass objects.
- Report missing or invalid fields clearly.
- Preserve deterministic cell order.

### Task 4 — Level Validator

Validate:

```text
size is 3, 4, or 5
number of cells is size²
cell IDs are unique
character IDs are unique inside a level
clue IDs are unique
every board position exists exactly once
every cell references an existing clue
solution contains every cell exactly once
initially revealed cells exist
regions reference valid cells
0 <= k <= region size
FACT status is valid
SAME and DIFFERENT use two distinct cells
```

### Task 5 — Region Resolver

Support:

```text
ROW
COLUMN
NEIGHBORS
EXPLICIT
INTERSECTION
```

Neighbors include horizontal, vertical, and diagonal touching cells, excluding the center cell.

The resolver must return cell IDs in deterministic row-major order.

### Task 6 — Direct semantic evaluator foundation

Maintain the direct evaluator interface:

```python
def evaluate_clue(
    clue,
    assignment,
    cells,
) -> bool:
    ...
```

It must evaluate clues without calling the CNF encoder or SAT solver.

### Task 7 — GameState

Maintain:

```text
revealed_cells
proved_verdicts
selected_cell
solved
```

A cell can only be revealed with a proved `CRIMINAL` or `INNOCENT` verdict.

### Task 8 — PublicState builder

Build a safe public view containing:

```text
level ID
grid size
cells
revealed clues
proved verdicts
unresolved cells
```

It must not include:

```text
hidden solution
all clues
unrevealed clue content
```

### Task 9 — Game Engine skeleton

Before agent integration, implement:

```text
initial state creation
get_public_state
restart
is_solved
```

After Member 1 and Member 2 complete their modules, implement `submit_verdict`.

## 9. `submit_verdict` integration requirements

Expected behavior:

### Accepted verdict

If the submitted verdict is logically entailed:

```text
return ACCEPTED
record the proved verdict
reveal the card
reveal its clue
update the public state
```

### Not provable

If both possible statuses remain satisfiable:

```text
return NOT_PROVABLE
do not reveal the card
do not change the game state
```

### Contradicted

If the opposite status is logically forced:

```text
return CONTRADICTED
do not reveal the card
do not change the game state
```

### Inconsistent

If the current Knowledge Base is unsatisfiable:

```text
return INCONSISTENT
do not continue normal deduction
```

The Game Engine may use the hidden solution to validate accepted game data internally, but the logical acceptance decision must be based on entailment from public information.

## 10. Official level set

The project should contain six official levels:

| Level | Grid | Intended difficulty |
|---|---:|---|
| level_01 | 3×3 | Easy |
| level_02 | 3×3 | Easy–Medium |
| level_03 | 4×4 | Medium |
| level_04 | 4×4 | Medium–Hard |
| level_05 | 5×5 | Hard |
| level_06 | 5×5 | Stress Test |

The level count may be adjusted if the team later decides to include additional test puzzles, but these six levels are the current minimum target.

## 11. General rules for every level

Every level must contain:

```text
N² cells
N² distinct characters
one hidden verdict for every cell
one clue owned by every cell
at least one initially revealed card
structured clue data
display text for every clue
```

Every revealed clue is true regardless of the owner's status.

Names and occupations have no logical meaning unless explicitly referenced by a clue.

## 12. Required clue language

The complete project must support:

```text
FACT
SAME
DIFFERENT
EXACTLY
AT_LEAST
AT_MOST
```

It must also support at least two extensions.

Recommended extensions:

```text
PARITY
INTERSECTION region
```

Alternative extensions may be adopted if they are correctly implemented and documented.

## 13. Required region language

Core regions:

```text
ROW
COLUMN
NEIGHBORS
EXPLICIT
```

Recommended advanced region:

```text
INTERSECTION
```

Possible future extensions:

```text
COMMON_NEIGHBORS
BOUNDARY
CORNERS
```

## 14. Level validity conditions

A level is accepted only when all conditions below hold:

1. Every clue is true under the hidden solution.
2. The complete clue set is satisfiable.
3. The complete clue set has exactly one complete primary-variable solution.
4. The initial public Knowledge Base is satisfiable.
5. At least one unresolved verdict is logically forced initially.
6. After every accepted reveal, another forced move exists until completion.
7. The agent can solve the level without guessing.
8. No clue references a missing cell.
9. Every counting parameter satisfies `0 <= k <= region size`.
10. Rejected submissions do not alter the game state.

A unique solution alone is not enough. The progressive reveal path must also be solvable without guessing.

## 15. Level difficulty guidelines

### Level 1 — 3×3 Easy

Use mainly:

```text
FACT
SAME
DIFFERENT
small EXACTLY clues
```

Guidelines:

- Two or three cards may be initially revealed.
- Most deduction steps should use one clue directly.
- Do not require extension clues.
- Avoid long indirect chains.
- Use this level for basic gameplay demonstration.

### Level 2 — 3×3 Easy–Medium

Use:

```text
all six core clue types
neighbors
explicit regions
```

Guidelines:

- One or two cards initially revealed.
- Include at least one step that combines a clue with previous verdicts.
- Include at least one neighbor clue.
- Avoid excessive FACT clues.

### Level 3 — 4×4 Medium

Use:

```text
all six core clue types
rows
columns
neighbors
explicit regions
```

Guidelines:

- Two initially revealed cards are recommended.
- Include several counting clues.
- Include deductions requiring more than one known fact.
- Ensure runtime remains suitable for frequent Hint checks.

### Level 4 — 4×4 Medium–Hard

Introduce at least one extension:

```text
PARITY
or
INTERSECTION
```

Guidelines:

- One or two initially revealed cards.
- Include indirect reasoning.
- Include at least one advanced region or extension clue.
- Verify that the hint system can still identify a forced target.

### Level 5 — 5×5 Hard

Use:

```text
all six core clue types
at least one extension
multiple region types
several counting constraints
```

Guidelines:

- Two initially revealed cards are recommended.
- Limit direct FACT clues.
- Include corner, edge, and center neighbor clues.
- Use this level to test GUI scaling and solver performance.

### Level 6 — 5×5 Stress Test

Use:

```text
all supported clue types
both extensions
larger regions
longer progressive deduction sequence
```

Guidelines:

- It may begin with only one revealed card if a forced move exists.
- Use it to measure clauses, SAT calls, decisions, propagations, backtracks, and runtime.
- It must still be logically valid and no-guess solvable.
- Timeouts or failures must be reported rather than hidden.

## 16. Suggested clue distribution across the puzzle set

These are planning targets, not strict mathematical requirements:

| Clue type | Suggested total count |
|---|---:|
| FACT | 5–8 |
| SAME | 5–8 |
| DIFFERENT | 5–8 |
| EXACTLY | 10 or more |
| AT_LEAST | 6 or more |
| AT_MOST | 6 or more |
| Extension 1 | 3 or more |
| Extension 2 | 3 or more |

The final distribution may change based on puzzle quality.

## 17. Level creation workflow

For each level:

### Step 1 — Choose board size

Select:

```text
3×3
4×4
or
5×5
```

### Step 2 — Assign characters

Use distinct characters from `characters.json`.

### Step 3 — Create hidden solution

Assign every cell:

```text
CRIMINAL
or
INNOCENT
```

Avoid trivial distributions unless intentionally used for an easy level.

### Step 4 — Create candidate clues

Every clue must be true under the hidden solution.

Use a mix of:

```text
binary clues
counting clues
different regions
extensions where appropriate
```

### Step 5 — Choose initially revealed cards

Start with a small public clue set that guarantees at least one forced verdict.

### Step 6 — Run semantic validation

For every clue:

```python
assert evaluate_clue(
    clue,
    hidden_assignment,
    level.cells,
)
```

### Step 7 — Encode the complete clue set

Use Member 1's CNF encoder.

### Step 8 — Check satisfiability

The complete clue set must be SAT.

### Step 9 — Check uniqueness

Recommended method:

1. Find the first complete primary-variable model.
2. Add a blocking clause for that model.
3. Solve again.
4. The second query must be UNSAT.

### Step 10 — Check progressive solvability

Simulate:

```text
initial public state
-> find forced move
-> reveal accepted card and clue
-> rebuild Knowledge Base
-> repeat
```

The simulation must end in `SOLVED`, not `STUCK`.

### Step 11 — Review difficulty

Check:

```text
number of initial clues
number of deduction steps
number of direct FACT clues
region sizes
SAT-call count
runtime
```

### Step 12 — Save official JSON

Only validated levels should be committed as official project levels.

## 18. Level JSON ownership rules

The leader is the main owner of official level files.

Other members may suggest or draft clues, but changes to official level JSON should be reviewed by the leader to prevent inconsistent data and merge conflicts.

## 19. Integration responsibilities

### Integrate Member 1

Verify:

```text
VariableMap uses the agreed row-major order
CNF Encoder uses the agreed structured clues
Knowledge Base contains only public clues and proved verdicts
```

### Integrate Member 2

Verify:

```text
DPLL accepts the agreed CNF format
Assumptions do not mutate the original Knowledge Base
Entailment returns the agreed Verdict enum
Agent receives only PublicState
```

### Integrate Member 3

Verify:

```text
GUI uses Game Engine public methods
GUI does not read hidden solution
Character IDs match level data
Avatar paths are valid
Face-down cards do not display hidden clues
```

## 20. Git and branch management

Recommended branches:

```text
main
develop
feature/core-engine
feature/cnf-encoder
feature/dpll-agent
feature/gui-assets
```

Rules:

- No direct pushes to `main`.
- Features are merged into `develop`.
- Pull requests require passing tests.
- Shared interface changes require team discussion.
- `main` is updated only at stable milestones.

## 21. Pull request review checklist

Before merging:

```text
Does the code follow shared interfaces?
Do all existing tests still pass?
Are new tests included?
Does the module avoid hidden-data access?
Are error messages clear?
Is input data left unmodified where required?
Are names and file locations consistent?
Is the code documented enough for another member to understand?
```

## 22. Project documentation responsibilities

Maintain:

### `docs/architecture.md`

Describe:

```text
module boundaries
data flow
Game Engine versus Logic Agent
public interfaces
CNF representation
```

### `docs/data_format.md`

Describe:

```text
characters.json
level JSON
clue structure
region structure
coordinate convention
```

### `docs/task_assignment.md`

Record:

```text
member responsibilities
assigned files
completion status
major contributions
```

### `docs/level_design.md`

Record for every official level:

```text
grid size
difficulty
clue types used
extensions used
initially revealed cards
validation status
unique-solution status
progressive-solver status
```

## 23. Testing responsibilities

The leader maintains integration tests for:

```text
level loading
level validation
region resolution
public-state privacy
initial game state
restart
accepted verdict integration
NOT_PROVABLE behavior
CONTRADICTED behavior
INCONSISTENT behavior
progressive auto-solving
official level validation
```

## 24. Experiments and metrics

Coordinate automated collection of:

```text
primary variables
auxiliary variables
CNF clauses
SAT calls
decisions
propagations
backtracks
deduction steps
reveal waves
runtime
status
```

All official levels should use the same experiment runner.

Failures and timeouts must remain in the results.

## 25. Milestones

### Milestone 1 — Shared foundation

```text
models
enums
loader
validator
region resolver
semantic evaluator
GameState
PublicState
Game Engine skeleton
```

### Milestone 2 — Core logic integration

```text
CNF Encoder
DPLL
entailment
Deductive Agent
submit_verdict
```

### Milestone 3 — Playable prototype

```text
one validated 3×3 level
manual play
verdict rejection
progressive reveal
basic GUI
```

### Milestone 4 — Complete puzzle set

```text
two 3×3 levels
two 4×4 levels
two 5×5 levels
two extensions
uniqueness checks
progressive solvability checks
```

### Milestone 5 — Final system

```text
Hint
Auto Solve
deduction trace
experiments
report data
demo-ready GUI
```

## 26. Definition of Done

The leader's task is complete when:

- Shared architecture and interfaces are stable.
- Game Engine and PublicState enforce hidden-data separation.
- All member modules are integrated successfully.
- Six official levels are present.
- Every official level has true clues, a unique solution, and a no-guess progressive solution.
- Manual gameplay works.
- Unsupported guesses return the correct result.
- Hint and Auto Solve use public knowledge only.
- All tests pass.
- Experiments can be run automatically.
- Documentation and README are current.
- The stable project is merged into `main`.

## 27. Deliverables

```text
core/
game/
logic/region_resolver.py
logic/semantic_evaluator.py
data/levels/level_01.json ... level_06.json
tests/test_loader.py
tests/test_regions.py
tests/test_game_state.py
tests/test_engine.py
tests/test_levels.py
docs/architecture.md
docs/data_format.md
docs/task_assignment.md
docs/level_design.md
README.md
```

Branch suggestion:

```text
feature/core-engine
```

## 28. Công việc bổ sung — Separate Uniqueness Checker

Phụ trách xây dựng bộ kiểm tra nghiệm duy nhất độc lập cho từng level.

File dự kiến:

```text
game/level_analyzer.py
tests/test_level_analyzer.py
```

Công việc cần thực hiện:

- Xây dựng full Knowledge Base từ toàn bộ clue của level.
- Giải lần thứ nhất để lấy một complete assignment.
- Tạo blocking clause loại bỏ nghiệm vừa tìm được.
- Giải lần thứ hai để phân biệt `UNIQUE`, `MULTIPLE` và `UNSAT`.
- Không dùng hidden solution để quyết định tính duy nhất.
- Trả về hai assignment khác nhau khi level có nhiều nghiệm để hỗ trợ debug.
- Kiểm tra đầy đủ sáu level chính thức.
- Phối hợp kết quả uniqueness với Experiment Runner.

Definition of Done:

```text
Có API kiểm tra uniqueness độc lập.
Phân biệt đúng UNIQUE, MULTIPLE và UNSAT.
Cả sáu level chính thức trả về UNIQUE.
Có test cho cả ba trạng thái.
```
