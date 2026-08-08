# tests/test_encoder.py
import pytest

from game.level_loader import load_level
from core.enums import ClueType, Verdict
from core.models import Cell, Clue
from logic.semantic_evaluator import evaluate_clue
from logic.variable_map import VariableMap
from logic.cnf_encoder import (
    encode_clue, build_knowledge_base, encode_known_verdict
)


def _solution_to_bool_assignment(level):
    return {
        cell_id: verdict.value == "CRIMINAL"
        for cell_id, verdict
        in level.hidden_solution.items()
    }


def test_all_clues_are_true_for_hidden_solution():
    level = load_level("data/levels/level_01.json")
    assignment = _solution_to_bool_assignment(level)

    for clue in level.clues.values():
        assert evaluate_clue(
            clue,
            assignment,
            level.cells,
        ), f"Clue is false: {clue.id}"


# Helpers for tests
def make_cell(cid: str, r: int, c: int) -> Cell:
    return Cell(id=cid, row=r, column=c, character_id=f"char_{cid}", clue_id=f"clue_{cid}")

def make_cells() -> tuple[Cell, ...]:
    return (
        make_cell("C1", 3, 1),
        make_cell("A1", 1, 1),
        make_cell("B1", 2, 1),
        make_cell("B2", 2, 2),
        make_cell("A2", 1, 2),
    )

def test_variable_mapping_row_major():
    # Test 1: Variable mapping follows row-major order.
    cells = make_cells()
    vmap = VariableMap(cells)
    
    # Ordered by row then column: A1(1,1), A2(1,2), B1(2,1), B2(2,2), C1(3,1)
    assert vmap.get_variable("A1") == 1
    assert vmap.get_variable("A2") == 2
    assert vmap.get_variable("B1") == 3
    assert vmap.get_variable("B2") == 4
    assert vmap.get_variable("C1") == 5

def test_variable_mapping_deterministic():
    # Test 2: Variable mapping is deterministic.
    cells = make_cells()
    vmap1 = VariableMap(cells)
    vmap2 = VariableMap(tuple(reversed(cells)))
    
    for c in cells:
        assert vmap1.get_variable(c.id) == vmap2.get_variable(c.id)

def test_fact_criminal_positive_unit_clause():
    # Test 3: FACT CRIMINAL produces a positive unit clause.
    cells = make_cells()
    vmap = VariableMap(cells)
    clue = Clue(id="1", owner_cell="A1", type=ClueType.FACT, data={"person": "B1", "status": "CRIMINAL"}, display_text="")
    
    clauses = encode_clue(clue, cells, vmap)
    assert clauses == [[vmap.get_variable("B1")]]

def test_fact_innocent_negative_unit_clause():
    # Test 4: FACT INNOCENT produces a negative unit clause.
    cells = make_cells()
    vmap = VariableMap(cells)
    clue = Clue(id="1", owner_cell="A1", type=ClueType.FACT, data={"person": "B2", "status": "INNOCENT"}, display_text="")
    
    clauses = encode_clue(clue, cells, vmap)
    assert clauses == [[-vmap.get_variable("B2")]]

def test_same_produces_two_clauses():
    # Test 5: SAME produces exactly two correct clauses.
    cells = make_cells()
    vmap = VariableMap(cells)
    clue = Clue(id="1", owner_cell="A1", type=ClueType.SAME, data={"person1": "A1", "person2": "B1"}, display_text="")
    
    clauses = encode_clue(clue, cells, vmap)
    p1 = vmap.get_variable("A1")
    p2 = vmap.get_variable("B1")
    assert clauses == [[-p1, p2], [p1, -p2]]

def test_different_produces_two_clauses():
    # Test 6: DIFFERENT produces exactly two correct clauses.
    cells = make_cells()
    vmap = VariableMap(cells)
    clue = Clue(id="1", owner_cell="A1", type=ClueType.DIFFERENT, data={"person1": "A1", "person2": "B1"}, display_text="")
    
    clauses = encode_clue(clue, cells, vmap)
    p1 = vmap.get_variable("A1")
    p2 = vmap.get_variable("B1")
    assert clauses == [[p1, p2], [-p1, -p2]]

def test_at_most_boundary_and_normal():
    # Test 7: AT_MOST handles normal and boundary cases.
    cells = make_cells()
    vmap = VariableMap(cells)
    clue = Clue(id="1", owner_cell="A1", type=ClueType.AT_MOST, data={"k": 1, "region": {"type": "EXPLICIT", "cells": ["A1", "B1", "C1"]}}, display_text="")
    
    clauses = encode_clue(clue, cells, vmap)
    a1, b1, c1 = vmap.get_variable("A1"), vmap.get_variable("B1"), vmap.get_variable("C1")
    
    # Normal case: k=1, region size=3 -> subsets of size 2
    expected = [[-a1, -b1], [-a1, -c1], [-b1, -c1]]
    assert clauses == expected
    
    # Boundary k=0 -> subsets of size 1
    clue_0 = Clue(id="2", owner_cell="A1", type=ClueType.AT_MOST, data={"k": 0, "region": {"type": "EXPLICIT", "cells": ["A1", "B1", "C1"]}}, display_text="")
    assert encode_clue(clue_0, cells, vmap) == [[-a1], [-b1], [-c1]]
    
    # Boundary k=3 -> subsets of size 4 -> no clauses
    clue_3 = Clue(id="3", owner_cell="A1", type=ClueType.AT_MOST, data={"k": 3, "region": {"type": "EXPLICIT", "cells": ["A1", "B1", "C1"]}}, display_text="")
    assert encode_clue(clue_3, cells, vmap) == []

def test_at_least_boundary_and_normal():
    # Test 8: AT_LEAST handles normal and boundary cases.
    cells = make_cells()
    vmap = VariableMap(cells)
    
    clue = Clue(id="1", owner_cell="A1", type=ClueType.AT_LEAST, data={"k": 2, "region": {"type": "EXPLICIT", "cells": ["A1", "B1", "C1"]}}, display_text="")
    clauses = encode_clue(clue, cells, vmap)
    a1, b1, c1 = vmap.get_variable("A1"), vmap.get_variable("B1"), vmap.get_variable("C1")
    
    # Normal case: k=2, size=3 -> sum(not Ci) <= 3 - 2 = 1 -> subsets of size 1+1=2 of positive variables
    expected = [[a1, b1], [a1, c1], [b1, c1]]
    assert clauses == expected
    
    # Boundary k=0 -> no clauses
    clue_0 = Clue(id="2", owner_cell="A1", type=ClueType.AT_LEAST, data={"k": 0, "region": {"type": "EXPLICIT", "cells": ["A1", "B1", "C1"]}}, display_text="")
    assert encode_clue(clue_0, cells, vmap) == []
    
    # Boundary k=3 -> subsets of size 1 of positive variables
    clue_3 = Clue(id="3", owner_cell="A1", type=ClueType.AT_LEAST, data={"k": 3, "region": {"type": "EXPLICIT", "cells": ["A1", "B1", "C1"]}}, display_text="")
    assert encode_clue(clue_3, cells, vmap) == [[a1], [b1], [c1]]

def test_exactly_equals_at_least_plus_at_most():
    # Test 9: EXACTLY equals AT_LEAST plus AT_MOST.
    cells = make_cells()
    vmap = VariableMap(cells)
    
    clue_exact = Clue(id="1", owner_cell="A1", type=ClueType.EXACTLY, data={"k": 1, "region": {"type": "EXPLICIT", "cells": ["A1", "B1", "C1"]}}, display_text="")
    clue_least = Clue(id="2", owner_cell="A1", type=ClueType.AT_LEAST, data={"k": 1, "region": {"type": "EXPLICIT", "cells": ["A1", "B1", "C1"]}}, display_text="")
    clue_most = Clue(id="3", owner_cell="A1", type=ClueType.AT_MOST, data={"k": 1, "region": {"type": "EXPLICIT", "cells": ["A1", "B1", "C1"]}}, display_text="")
    
    clauses_exact = encode_clue(clue_exact, cells, vmap)
    clauses_least = encode_clue(clue_least, cells, vmap)
    clauses_most = encode_clue(clue_most, cells, vmap)
    
    assert clauses_exact == clauses_least + clauses_most

def test_proved_verdicts_unit_clauses():
    # Test 10: Proved verdicts are encoded as unit clauses.
    cells = make_cells()
    vmap = VariableMap(cells)
    
    c1 = encode_known_verdict("A1", Verdict.CRIMINAL, vmap)
    assert c1 == [vmap.get_variable("A1")]
    
    c2 = encode_known_verdict("B1", Verdict.INNOCENT, vmap)
    assert c2 == [-vmap.get_variable("B1")]

def test_knowledge_base_contains_only_revealed_clues():
    # Test 11: The Knowledge Base contains only revealed clues.
    cells = make_cells()
    vmap = VariableMap(cells)
    
    clue1 = Clue(id="c1", owner_cell="A1", type=ClueType.FACT, data={"person": "A1", "status": "CRIMINAL"}, display_text="")
    clue2 = Clue(id="c2", owner_cell="B1", type=ClueType.FACT, data={"person": "B1", "status": "INNOCENT"}, display_text="")
    
    revealed_clues = (clue1,)
    proved_verdicts = {"A2": Verdict.CRIMINAL}
    
    kb = build_knowledge_base(revealed_clues, proved_verdicts, cells, vmap)
    
    a1 = vmap.get_variable("A1")
    a2 = vmap.get_variable("A2")
    
    # Should only contain clue1 and A2 verdict, not clue2
    assert kb == [[a1], [a2]]

def test_invalid_clue_data_raises_exception():
    # Test 12: Invalid clue data raises a clear exception.
    cells = make_cells()
    vmap = VariableMap(cells)
    
    # Invalid cell ID in FACT
    clue_bad_fact = Clue(id="1", owner_cell="A1", type=ClueType.FACT, data={"person": "Z99", "status": "CRIMINAL"}, display_text="")
    with pytest.raises(KeyError):
        encode_clue(clue_bad_fact, cells, vmap)
        
    # Invalid status in FACT
    clue_bad_status = Clue(id="2", owner_cell="A1", type=ClueType.FACT, data={"person": "A1", "status": "UNKNOWN"}, display_text="")
    with pytest.raises(ValueError):
        encode_clue(clue_bad_status, cells, vmap)
        
    # Invalid k in AT_MOST
    clue_bad_k = Clue(id="3", owner_cell="A1", type=ClueType.AT_MOST, data={"k": -1, "region": {"type": "EXPLICIT", "cells": ["A1"]}}, display_text="")
    with pytest.raises(ValueError):
        encode_clue(clue_bad_k, cells, vmap)