# MEMBER 2 — DPLL SAT SOLVER, ENTAILMENT, AND DEDUCTIVE AGENT

## 1. Role

Member 2 is responsible for implementing the main artificial intelligence algorithm of the project: a DPLL SAT solver and the deductive agent built on top of it.

The agent must derive only logically forced verdicts. It must never guess and must never inspect the hidden solution or unrevealed clues.

## 2. Assigned files

Primary files:

```text
logic/dpll.py
logic/entailment.py
logic/deductive_agent.py
tests/test_dpll.py
tests/test_entailment.py
```

Optional supporting files, after agreement with the team leader:

```text
logic/solver_statistics.py
logic/solver_result.py
tests/test_agent.py
```

Do not change the CNF representation or common models without discussing the change with the team leader and Member 1.

## 3. Required interfaces

### DPLL solver

```python
def solve(
    clauses: list[list[int]],
    assumptions: list[int] | None = None,
):
    ...
```

The result must contain:

```text
satisfiable
complete assignment when SAT
decisions
propagations
backtracks
runtime
```

### Entailment classification

```python
def classify_character(
    clauses,
    variable_id,
    solver,
):
    ...
```

### Deductive agent

```python
class DeductiveAgent:
    def classify_all(self, public_state):
        ...

    def choose_next_move(self, public_state):
        ...
```

The exact constructor dependencies should be discussed with the team leader. The agent will normally need a CNF encoder, variable map, and DPLL solver.

## 4. DPLL representation

Input CNF:

```python
list[list[int]]
```

Assignment:

```python
dict[int, bool]
```

Example:

```python
clauses = [
    [1, 2],
    [-1, 3],
    [-2, -3],
]
```

## 5. Detailed DPLL tasks

### Task 1 — Literal evaluation

Create helpers to determine whether a literal is:

```text
True
False
Unassigned
```

For literal `-3`:

- It is true when variable 3 is assigned `False`.
- It is false when variable 3 is assigned `True`.
- It is unassigned when variable 3 has no value.

### Task 2 — Clause status

A clause may be:

```text
SATISFIED
UNRESOLVED
UNIT
CONFLICT
```

Requirements:

- A clause is satisfied if at least one literal is true.
- A clause is a conflict if all literals are false.
- A clause is unit if all but one literal are false and the remaining literal is unassigned.

### Task 3 — Conflict detection

Stop the current branch immediately when any clause becomes false under the current assignment.

### Task 4 — Unit propagation

Repeatedly find and assign unit literals until:

```text
no unit clause remains
or
a conflict is detected
```

Each forced assignment must increase the propagation counter.

Contradictory unit requirements must produce UNSAT for that branch.

### Task 5 — Deterministic variable selection

Choose the next unassigned variable deterministically.

The minimum acceptable rule is:

```text
choose the smallest variable ID that appears in an unresolved clause
```

The same CNF must lead to the same branching order in repeated runs.

### Task 6 — Recursive branching

For the selected variable:

```text
try True
if the branch fails, backtrack
try False
```

Each chosen branch value increases the decision counter.

### Task 7 — Backtracking

When a branch reaches conflict:

- Discard that branch's temporary assignments.
- Restore the previous assignment.
- Increase the backtrack counter.
- Explore the alternative value.

Avoid mutating a shared assignment in a way that leaks changes between branches.

### Task 8 — SAT and UNSAT termination

Return SAT when all clauses are satisfied.

Return UNSAT when both branches for a required decision fail.

### Task 9 — Complete assignment

When SAT is found, return values for all variables relevant to the formula.

If a variable is not constrained after the clauses are satisfied, assign it deterministically, such as `False`, so the returned assignment is complete.

### Task 10 — Assumptions

Support temporary assumptions:

```python
solver.solve(clauses, assumptions=[-5])
```

An assumption is equivalent to a temporary unit clause but must not permanently change the original Knowledge Base.

The input clauses must remain unchanged after a solver call.

### Task 11 — Runtime and statistics

Record:

```text
decisions
propagations
backtracks
runtime_ms
```

Statistics must be reset for each independent call to `solve`.

## 6. Entailment classification

A satisfying model is only one possible assignment. A character can be called Criminal or Innocent only when the verdict holds in every model of the current Knowledge Base.

For variable `Ci`:

### Inconsistency check

```text
If KB is UNSAT:
    return INCONSISTENT
```

### Criminal check

Temporarily assume the character is Innocent:

```text
KB ∧ ¬Ci
```

If this is UNSAT:

```text
KB entails Ci
return CRIMINAL
```

### Innocent check

Temporarily assume the character is Criminal:

```text
KB ∧ Ci
```

If this is UNSAT:

```text
KB entails ¬Ci
return INNOCENT
```

### Unknown

If both assumptions remain satisfiable:

```text
return UNKNOWN
```

## 7. Deductive Agent tasks

### Task 1 — Receive public information only

The agent may use:

```text
cells
revealed_clues
proved_verdicts
unresolved_cells
```

The agent must not receive or inspect:

```text
hidden_solution
unrevealed clues
correct label of an unresolved card
```

### Task 2 — Build or request the current Knowledge Base

The agent should use the common CNF encoder rather than constructing clue formulas manually.

### Task 3 — Classify all unresolved cells

Return a dictionary such as:

```python
{
    "B1": Verdict.CRIMINAL,
    "C1": Verdict.UNKNOWN,
    "A2": Verdict.INNOCENT,
}
```

### Task 4 — Choose the next move deterministically

Only choose:

```text
CRIMINAL
or
INNOCENT
```

Never choose an `UNKNOWN` cell.

If several cells are forced, choose the first one in row-major order.

If no cell is forced, return `None`.

### Task 5 — Handle inconsistent Knowledge Base

If the current Knowledge Base is inconsistent, report `INCONSISTENT` rather than attempting to choose a normal move.

### Task 6 — Prepare for deduction trace

Return or expose enough information for later integration:

```text
target cell
tested assumptions
SAT/UNSAT results
final verdict
solver statistics
```

A complete trace format can be finalized during integration.

## 8. Required DPLL tests

At minimum:

### SAT by unit propagation

```python
[[1], [-1, 2]]
```

Expected:

```text
SAT
1 = True
2 = True
```

### Immediate UNSAT

```python
[[1], [-1]]
```

Expected:

```text
UNSAT
```

### SAT requiring branching

Use a formula with no initial unit clauses.

### UNSAT requiring branching and backtracking

Use a formula where both values of a selected variable eventually conflict.

### Assumption test

```python
clauses = [[1, 2]]
assumptions = [-1]
```

Expected: SAT with variable 2 true.

### Input immutability

Verify that `clauses` is unchanged after `solve`.

### Determinism

Repeated calls on the same formula must produce the same decision order and result.

## 9. Required entailment tests

For:

```python
KB = [
    [1, 2],
    [-1, 2],
]
```

Expected:

```text
Variable 2 -> CRIMINAL
Variable 1 -> UNKNOWN
```

Also test:

```text
forced innocent
unknown
inconsistent KB
already proved status if supported by the final design
```

## 10. Definition of Done

The task is complete when:

- DPLL correctly returns SAT or UNSAT.
- Unit propagation, conflict detection, branching, and backtracking are implemented manually.
- Variable selection is deterministic.
- SAT results contain a complete assignment.
- Assumptions work without changing the original Knowledge Base.
- Solver statistics are recorded.
- Entailment returns CRIMINAL, INNOCENT, UNKNOWN, or INCONSISTENT correctly.
- The agent never chooses UNKNOWN and never reads hidden data.
- All assigned tests pass.

## 11. Deliverables

```text
logic/dpll.py
logic/entailment.py
logic/deductive_agent.py
tests/test_dpll.py
tests/test_entailment.py
tests/test_agent.py
```

Branch suggestion:

```text
feature/dpll-agent
```
