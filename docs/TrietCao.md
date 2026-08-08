# MEMBER 1 — LOGICAL REPRESENTATION AND CNF ENCODER

## 1. Role

Member 1 is responsible for converting the structured clues of the Griductive game into propositional logic and Conjunctive Normal Form (CNF). This module is the bridge between the puzzle data and the DPLL SAT solver.

The implementation must work with the common classes and conventions defined by the team leader. It must not use hidden solutions or unrevealed clues when building the current Knowledge Base.

## 2. Assigned files

Primary files:

```text
logic/variable_map.py
logic/cnf_encoder.py
tests/test_encoder.py
```

Additional test file that may be created:

```text
tests/test_cnf_semantic_equivalence.py
```

Member 1 should not modify shared files such as `core/models.py`, `core/enums.py`, or the level JSON format without discussing the change with the team leader first.

## 3. Input conventions

### 3.1 Propositional meaning

For every cell or character `i`:

```text
Ci = True   means the character is CRIMINAL
Ci = False  means the character is INNOCENT
```

### 3.2 CNF representation

CNF is represented as:

```python
list[list[int]]
```

Example:

```python
[
    [1, -2],
    [-1, 3],
    [2],
]
```

A positive integer represents a positive literal. A negative integer represents its negation.

### 3.3 Required interface

```python
class VariableMap:
    def __init__(self, cells):
        ...

    def get_variable(self, cell_id: str) -> int:
        ...

    def get_cell_id(self, variable: int) -> str:
        ...
```

```python
def encode_clue(
    clue,
    cells,
    variable_map,
) -> list[list[int]]:
    ...
```

```python
def build_knowledge_base(
    revealed_clues,
    proved_verdicts,
    cells,
    variable_map,
) -> list[list[int]]:
    ...
```

## 4. Detailed tasks

### Task 1 — Deterministic variable mapping

Create a stable mapping from cell IDs to primary propositional variables.

For a 3×3 board, the mapping must follow row-major order:

```text
A1 -> 1
B1 -> 2
C1 -> 3
A2 -> 4
B2 -> 5
C2 -> 6
A3 -> 7
B3 -> 8
C3 -> 9
```

Requirements:

- The same level always produces the same mapping.
- Cell IDs must not be duplicated.
- Unknown cell IDs must raise a clear error.
- Primary variables must start from 1.
- Auxiliary variables, if introduced later, must be separated from primary variables.

### Task 2 — Encode FACT

Examples:

```text
FACT(A1, CRIMINAL) -> [[A1]]
FACT(A1, INNOCENT) -> [[-A1]]
```

The status `UNKNOWN` or `INCONSISTENT` is invalid inside a FACT clue.

### Task 3 — Encode SAME

Logical meaning:

```text
CA <-> CB
```

CNF:

```text
(¬CA ∨ CB) ∧ (CA ∨ ¬CB)
```

Expected output:

```python
[
    [-a, b],
    [a, -b],
]
```

### Task 4 — Encode DIFFERENT

Logical meaning:

```text
CA XOR CB
```

CNF:

```text
(CA ∨ CB) ∧ (¬CA ∨ ¬CB)
```

Expected output:

```python
[
    [a, b],
    [-a, -b],
]
```

### Task 5 — Encode AT_MOST

For a region `R`:

```text
sum(Ci for i in R) <= k
```

A direct combinatorial encoding is acceptable because the puzzle regions are small.

For `AT_MOST(1, [A, B, C])`, every pair cannot be criminal together:

```python
[
    [-a, -b],
    [-a, -c],
    [-b, -c],
]
```

General rule:

- Generate every subset of size `k + 1`.
- Add a clause containing the negation of all variables in that subset.

Boundary cases:

```text
AT_MOST(|R|) -> no clauses
AT_MOST(0)   -> one negative unit clause for each variable
```

### Task 6 — Encode AT_LEAST

For a region `R`:

```text
sum(Ci for i in R) >= k
```

It may be encoded by applying AT_MOST to the negated variables:

```text
sum(¬Ci for i in R) <= |R| - k
```

Boundary cases:

```text
AT_LEAST(0)   -> no clauses
AT_LEAST(|R|) -> one positive unit clause for each variable
```

### Task 7 — Encode EXACTLY

Use:

```text
EXACTLY(k, R) = AT_LEAST(k, R) ∧ AT_MOST(k, R)
```

The resulting clauses are the concatenation of the two encodings.

### Task 8 — Encode known verdicts

Previously proved statuses must be added as unit clauses:

```text
A1 = CRIMINAL -> [A1]
A1 = INNOCENT -> [-A1]
```

Only proved statuses are added. Unresolved characters are not added.

### Task 9 — Build the current Knowledge Base

The Knowledge Base at deduction step `t` must contain only:

```text
CNF(revealed clues)
AND
unit clauses for proved verdicts
```

It must not contain:

```text
hidden_solution
unrevealed clues
guessed verdicts
```

Expected process:

```python
clauses = []

for clue in revealed_clues:
    clauses.extend(
        encode_clue(clue, cells, variable_map)
    )

for cell_id, verdict in proved_verdicts.items():
    clauses.append(
        encode_known_verdict(cell_id, verdict, variable_map)
    )
```

### Task 10 — Report encoding statistics

Provide at least:

```text
number of primary variables
number of auxiliary variables
number of clauses
```

If direct combinatorial encoding is used, the auxiliary variable count may remain zero.

## 5. Required tests

The following tests must be included:

1. Variable mapping follows row-major order.
2. Variable mapping is deterministic.
3. FACT CRIMINAL produces a positive unit clause.
4. FACT INNOCENT produces a negative unit clause.
5. SAME produces exactly two correct clauses.
6. DIFFERENT produces exactly two correct clauses.
7. AT_MOST handles normal and boundary cases.
8. AT_LEAST handles normal and boundary cases.
9. EXACTLY equals AT_LEAST plus AT_MOST.
10. Proved verdicts are encoded as unit clauses.
11. The Knowledge Base contains only revealed clues.
12. Invalid clue data raises a clear exception.

## 6. Semantic equivalence test

For each small clue:

1. Enumerate all complete assignments of the referenced variables.
2. Evaluate the clue using `semantic_evaluator.py`.
3. Check whether the same assignment satisfies the generated CNF.
4. Assert that the two results are identical.

This test is especially important for counting clues.

## 7. Definition of Done

The task is complete when:

- All six required clue types are encoded.
- Variable mapping is deterministic.
- Current Knowledge Base is built only from public information.
- All encoder tests pass.
- Semantic evaluator and CNF agree on all tested assignments.
- No external SAT library is used.
- The branch can be merged without modifying the agreed shared interfaces.

## 8. Deliverables

```text
logic/variable_map.py
logic/cnf_encoder.py
tests/test_encoder.py
tests/test_cnf_semantic_equivalence.py
```

Branch suggestion:

```text
feature/cnf-encoder
```

## 9. Công việc bổ sung — Hoàn thiện Level Loader và Validator

Phụ trách tăng độ chặt chẽ của dữ liệu đầu vào trước khi CNF encoder xử lý.
Các thay đổi ở module dùng chung cần được Khoa Trần review.

File liên quan:

```text
game/level_loader.py
game/level_validator.py
tests/test_loader.py
tests/test_level_validation.py
```

Công việc cần thực hiện:

- Phát hiện clue ID trùng trước khi chuyển danh sách clue thành dictionary.
- Kiểm tra kiểu của `cells`, `clues`, `solution` và `initial_revealed`.
- Báo lỗi rõ field và file gây lỗi.
- Kiểm tra số clue bằng số cell.
- Mỗi cell phải sở hữu đúng một clue.
- Không có hai clue dùng cùng `owner_cell`.
- `cell.clue_id` phải trỏ tới clue có `owner_cell` bằng chính cell đó.
- Kiểm tra mọi cell ID và region được clue tham chiếu.
- Kiểm tra counting status chỉ là `CRIMINAL` hoặc `INNOCENT`.
- Kiểm tra `PARITY`, comparison operator và connectivity hợp lệ.
- Kiểm tra clue đúng với hidden solution bằng direct semantic evaluator.
- Không gọi GUI hoặc Logic Agent từ validator.

Test cần bổ sung:

```text
duplicate clue ID
duplicate owner_cell
cell thiếu clue hoặc clue thừa
cell trỏ tới clue của cell khác
status/parity/operator/connectivity không hợp lệ
region rỗng hoặc tham chiếu cell không tồn tại
clue sai so với hidden solution
sáu level chính thức đều hợp lệ
```

Definition of Done:

```text
Loader không làm mất duplicate clue.
Validator phát hiện đầy đủ lỗi ownership và reference.
Mọi clue chính thức đúng với hidden solution.
Toàn bộ test pass.
```
