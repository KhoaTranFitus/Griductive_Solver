# tests/test_cnf_semantic_equivalence.py
import itertools
import pytest

from core.enums import ClueType, Verdict
from core.models import Cell, Clue
from logic.semantic_evaluator import evaluate_clue
from logic.variable_map import VariableMap
from logic.cnf_encoder import encode_clue


def make_cell(cid: str, r: int, c: int) -> Cell:
    return Cell(id=cid, row=r, column=c, character_id=f"char_{cid}", clue_id=f"clue_{cid}")


def evaluate_cnf(clauses: list[list[int]], assignment: dict[str, bool], vmap: VariableMap) -> bool:
    """
    Evaluates a set of CNF clauses given a semantic assignment.
    assignment: e.g. {"A1": True, "B1": False}
    """
    if not clauses:
        return True
        
    for clause in clauses:
        clause_satisfied = False
        for literal in clause:
            # Positive literal means checking if variable is True
            # Negative literal means checking if variable is False
            var_index = abs(literal)
            cell_id = vmap.get_cell_id(var_index)
            is_criminal = assignment[cell_id]
            
            if (literal > 0 and is_criminal) or (literal < 0 and not is_criminal):
                clause_satisfied = True
                break
                
        if not clause_satisfied:
            return False
            
    return True


def check_equivalence(clue: Clue, cells: tuple[Cell, ...], involved_cell_ids: list[str]):
    vmap = VariableMap(cells)
    clauses = encode_clue(clue, cells, vmap)
    
    # Generate all possible 2^N binary assignments for the involved cells
    for assignment_tuple in itertools.product([True, False], repeat=len(involved_cell_ids)):
        assignment = dict(zip(involved_cell_ids, assignment_tuple))
        
        # semantic_evaluator requires a full assignment for all cells, so we pad the rest with False
        # (Though our test clues might only involve a subset, the semantic evaluator checks missing keys
        # against the full cell list).
        full_assignment = {cell.id: False for cell in cells}
        full_assignment.update(assignment)
        
        semantic_result = evaluate_clue(clue, full_assignment, cells)
        cnf_result = evaluate_cnf(clauses, full_assignment, vmap)
        
        assert semantic_result == cnf_result, (
            f"Equivalence failed for {clue.type} clue.\n"
            f"Assignment: {assignment}\n"
            f"Semantic: {semantic_result}, CNF: {cnf_result}\n"
            f"Clauses: {clauses}"
        )


def test_fact_equivalence():
    cells = (make_cell("A1", 1, 1),)
    clue = Clue(id="1", owner_cell="A1", type=ClueType.FACT, data={"person": "A1", "status": "CRIMINAL"}, display_text="")
    check_equivalence(clue, cells, ["A1"])
    
    clue_innocent = Clue(id="2", owner_cell="A1", type=ClueType.FACT, data={"person": "A1", "status": "INNOCENT"}, display_text="")
    check_equivalence(clue_innocent, cells, ["A1"])


def test_same_equivalence():
    cells = (make_cell("A1", 1, 1), make_cell("B1", 2, 1))
    clue = Clue(id="1", owner_cell="A1", type=ClueType.SAME, data={"person1": "A1", "person2": "B1"}, display_text="")
    check_equivalence(clue, cells, ["A1", "B1"])


def test_different_equivalence():
    cells = (make_cell("A1", 1, 1), make_cell("B1", 2, 1))
    clue = Clue(id="1", owner_cell="A1", type=ClueType.DIFFERENT, data={"person1": "A1", "person2": "B1"}, display_text="")
    check_equivalence(clue, cells, ["A1", "B1"])


def test_at_most_equivalence():
    cells = (make_cell("A1", 1, 1), make_cell("B1", 2, 1), make_cell("C1", 3, 1))
    for k in range(4): # k = 0, 1, 2, 3
        clue = Clue(id="1", owner_cell="A1", type=ClueType.AT_MOST, data={"k": k, "region": {"type": "EXPLICIT", "cells": ["A1", "B1", "C1"]}}, display_text="")
        check_equivalence(clue, cells, ["A1", "B1", "C1"])


def test_at_least_equivalence():
    cells = (make_cell("A1", 1, 1), make_cell("B1", 2, 1), make_cell("C1", 3, 1))
    for k in range(4): # k = 0, 1, 2, 3
        clue = Clue(id="1", owner_cell="A1", type=ClueType.AT_LEAST, data={"k": k, "region": {"type": "EXPLICIT", "cells": ["A1", "B1", "C1"]}}, display_text="")
        check_equivalence(clue, cells, ["A1", "B1", "C1"])


def test_exactly_equivalence():
    cells = (make_cell("A1", 1, 1), make_cell("B1", 2, 1), make_cell("C1", 3, 1))
    for k in range(4): # k = 0, 1, 2, 3
        clue = Clue(id="1", owner_cell="A1", type=ClueType.EXACTLY, data={"k": k, "region": {"type": "EXPLICIT", "cells": ["A1", "B1", "C1"]}}, display_text="")
        check_equivalence(clue, cells, ["A1", "B1", "C1"])


@pytest.mark.parametrize("status", ["CRIMINAL", "INNOCENT"])
def test_exactly_status_equivalence(status):
    cells = (make_cell("A1", 1, 1), make_cell("B1", 1, 2), make_cell("C1", 1, 3))
    clue = Clue("1", "A1", ClueType.EXACTLY, {
        "k": 2, "status": status,
        "region": {"type": "ROW", "index": 1},
    }, "")
    check_equivalence(clue, cells, ["A1", "B1", "C1"])


def test_parity_equivalence():
    cells = (make_cell("A1", 1, 1), make_cell("B1", 1, 2), make_cell("C1", 1, 3))
    clue = Clue("1", "A1", ClueType.PARITY, {
        "parity": "ODD", "status": "INNOCENT",
        "region": {"type": "ROW", "index": 1},
    }, "")
    check_equivalence(clue, cells, ["A1", "B1", "C1"])


@pytest.mark.parametrize("clue_type", [ClueType.EQUAL_COUNT, ClueType.COMPARE_COUNT])
def test_count_relation_equivalence(clue_type):
    cells = tuple(make_cell(f"{column}{row}", row, col) for row in (1, 2) for col, column in enumerate("AB", 1))
    data = {"status": "CRIMINAL"}
    if clue_type is ClueType.EQUAL_COUNT:
        data.update(region1={"type": "ROW", "index": 1}, region2={"type": "ROW", "index": 2})
    else:
        data.update(operator="GT", left_region={"type": "ROW", "index": 1}, right_region={"type": "ROW", "index": 2})
    clue = Clue("1", "A1", clue_type, data, "")
    check_equivalence(clue, cells, [cell.id for cell in cells])


def test_connected_equivalence():
    cells = tuple(make_cell(f"{column}{row}", row, col) for row in (1, 2) for col, column in enumerate("AB", 1))
    clue = Clue("1", "A1", ClueType.CONNECTED, {
        "status": "CRIMINAL", "connectivity": "ORTHOGONAL",
        "region": {"type": "EXPLICIT", "cells": [cell.id for cell in cells]},
    }, "")
    check_equivalence(clue, cells, [cell.id for cell in cells])
