# logic/variable_map.py
from core.models import Cell

class VariableMap:
    def __init__(self, cells: tuple[Cell, ...]):
        # Sort cells in row-major order: increasing by (row, column)
        sorted_cells = sorted(cells, key=lambda cell: (cell.row, cell.column))
        
        self._cell_id_to_var: dict[str, int] = {}
        self._var_to_cell_id: dict[int, str] = {}
        
        seen_ids = set()
        for idx, cell in enumerate(sorted_cells, start=1):
            if cell.id in seen_ids:
                raise ValueError(f"Duplicate cell ID found: {cell.id}")
            seen_ids.add(cell.id)
            
            self._cell_id_to_var[cell.id] = idx
            self._var_to_cell_id[idx] = cell.id
            
    def get_variable(self, cell_id: str) -> int:
        """Get the propositional variable corresponding to a cell ID."""
        if cell_id not in self._cell_id_to_var:
            raise KeyError(f"Unknown cell ID: {cell_id}")
        return self._cell_id_to_var[cell_id]

    def get_cell_id(self, variable: int) -> str:
        """Get the cell ID corresponding to a propositional variable."""
        if variable not in self._var_to_cell_id:
            raise KeyError(f"Unknown variable: {variable}")
        return self._var_to_cell_id[variable]
