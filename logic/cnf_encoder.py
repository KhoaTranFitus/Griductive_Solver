# logic/cnf_encoder.py
import itertools

from core.enums import ClueType, Verdict
from core.exceptions import UnsupportedClueError
from core.models import Cell, Clue
from logic.region_resolver import parse_region, resolve_region
from logic.variable_map import VariableMap


def encode_fact(clue: Clue, variable_map: VariableMap) -> list[list[int]]:
    person = clue.data["person"]
    status = Verdict(clue.data["status"])
    var = variable_map.get_variable(person)
    
    if status == Verdict.CRIMINAL:
        return [[var]]
    elif status == Verdict.INNOCENT:
        return [[-var]]
    else:
        raise ValueError(f"FACT clue cannot use status {status}")


def encode_same(clue: Clue, variable_map: VariableMap) -> list[list[int]]:
    p1 = variable_map.get_variable(clue.data["person1"])
    p2 = variable_map.get_variable(clue.data["person2"])
    return [
        [-p1, p2],
        [p1, -p2],
    ]


def encode_different(clue: Clue, variable_map: VariableMap) -> list[list[int]]:
    p1 = variable_map.get_variable(clue.data["person1"])
    p2 = variable_map.get_variable(clue.data["person2"])
    return [
        [p1, p2],
        [-p1, -p2],
    ]


def encode_at_most(k: int, cell_ids: list[str], variable_map: VariableMap) -> list[list[int]]:
    if k >= len(cell_ids):
        return []
    if k < 0:
        raise ValueError(f"k cannot be negative: {k}")
    
    vars_list = [variable_map.get_variable(cell_id) for cell_id in cell_ids]
    clauses = []
    
    # Generate every subset of size k + 1
    for subset in itertools.combinations(vars_list, k + 1):
        # Add a clause containing the negation of all variables in that subset
        clause = [-v for v in subset]
        clauses.append(clause)
        
    return clauses


def encode_at_least(k: int, cell_ids: list[str], variable_map: VariableMap) -> list[list[int]]:
    if k <= 0:
        return []
    if k > len(cell_ids):
        raise ValueError(f"k cannot be greater than region size: {k} > {len(cell_ids)}")
        
    # sum(Ci) >= k is equivalent to sum(not Ci) <= |R| - k
    vars_list = [-variable_map.get_variable(cell_id) for cell_id in cell_ids]
    target_k = len(cell_ids) - k
    
    clauses = []
    for subset in itertools.combinations(vars_list, target_k + 1):
        # -v reverses the sign again, effectively making it positive
        clause = [-v for v in subset]
        clauses.append(clause)
        
    return clauses


def encode_exactly(k: int, cell_ids: list[str], variable_map: VariableMap) -> list[list[int]]:
    return encode_at_least(k, cell_ids, variable_map) + encode_at_most(k, cell_ids, variable_map)


def encode_clue(
    clue: Clue,
    cells: tuple[Cell, ...],
    variable_map: VariableMap,
) -> list[list[int]]:
    if clue.type == ClueType.FACT:
        return encode_fact(clue, variable_map)
        
    if clue.type == ClueType.SAME:
        return encode_same(clue, variable_map)
        
    if clue.type == ClueType.DIFFERENT:
        return encode_different(clue, variable_map)
        
    # Counting clues require region resolution
    if clue.type in (ClueType.AT_MOST, ClueType.AT_LEAST, ClueType.EXACTLY):
        region = parse_region(clue.data["region"])
        cell_ids = resolve_region(region, cells)
        k = clue.data["k"]
        
        if clue.type == ClueType.AT_MOST:
            return encode_at_most(k, cell_ids, variable_map)
        if clue.type == ClueType.AT_LEAST:
            return encode_at_least(k, cell_ids, variable_map)
        if clue.type == ClueType.EXACTLY:
            return encode_exactly(k, cell_ids, variable_map)
            
    raise UnsupportedClueError(f"Unsupported clue type: {clue.type}")


def encode_known_verdict(cell_id: str, verdict: Verdict, variable_map: VariableMap) -> list[int]:
    var = variable_map.get_variable(cell_id)
    if verdict == Verdict.CRIMINAL:
        return [var]
    elif verdict == Verdict.INNOCENT:
        return [-var]
    else:
        raise ValueError(f"Invalid proved verdict status: {verdict}")


def build_knowledge_base(
    revealed_clues: tuple[Clue, ...],
    proved_verdicts: dict[str, Verdict],
    cells: tuple[Cell, ...],
    variable_map: VariableMap,
) -> list[list[int]]:
    clauses = []
    
    for clue in revealed_clues:
        clauses.extend(encode_clue(clue, cells, variable_map))
        
    for cell_id, verdict in proved_verdicts.items():
        clauses.append(encode_known_verdict(cell_id, verdict, variable_map))
        
    return clauses


def get_encoding_statistics(
    kb: list[list[int]],
    variable_map: VariableMap,
) -> dict[str, int]:
    # pylint: disable=protected-access
    return {
        "primary_variables": len(variable_map._cell_id_to_var),
        "auxiliary_variables": 0,
        "clauses": len(kb),
    }
