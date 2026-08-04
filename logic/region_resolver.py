# logic/region_resolver.py
from core.enums import RegionType
from core.exceptions import RegionResolutionError
from core.models import Cell, Region

def _sort_cells(cells: list[Cell]) -> list[Cell]:
    return sorted(
        cells,
        key=lambda cell: (cell.row, cell.column),
    )

def _resolve_row(
    index: int,
    cells: tuple[Cell, ...],
) -> list[str]:
    result = [
        cell
        for cell in cells
        if cell.row == index
    ]

    return [
        cell.id
        for cell in _sort_cells(result)
    ]

def _resolve_column(
    index: int,
    cells: tuple[Cell, ...],
) -> list[str]:
    result = [
        cell
        for cell in cells
        if cell.column == index
    ]

    return [
        cell.id
        for cell in _sort_cells(result)
    ]

def _resolve_neighbors(
    target_cell_id: str,
    cells: tuple[Cell, ...],
) -> list[str]:
    target = next(
        (
            cell
            for cell in cells
            if cell.id == target_cell_id
        ),
        None,
    )

    if target is None:
        raise RegionResolutionError(
            f"Unknown target cell: {target_cell_id}"
        )

    neighbors = []

    for cell in cells:
        if cell.id == target.id:
            continue

        row_distance = abs(cell.row - target.row)
        column_distance = abs(cell.column - target.column)

        if row_distance <= 1 and column_distance <= 1:
            neighbors.append(cell)

    return [
        cell.id
        for cell in _sort_cells(neighbors)
    ]

def _resolve_explicit(
    requested_ids: list[str],
    cells: tuple[Cell, ...],
) -> list[str]:
    existing_ids = {
        cell.id
        for cell in cells
    }

    result: list[str] = []
    seen: set[str] = set()

    for cell_id in requested_ids:
        if cell_id not in existing_ids:
            raise RegionResolutionError(
                f"Unknown cell in explicit region: {cell_id}"
            )

        if cell_id in seen:
            raise RegionResolutionError(
                f"Duplicate cell in explicit region: {cell_id}"
            )

        seen.add(cell_id)
        result.append(cell_id)

    return result

def _resolve_intersection(
    raw_regions: list[dict],
    cells: tuple[Cell, ...],
) -> list[str]:
    if len(raw_regions) < 2:
        raise RegionResolutionError(
            "INTERSECTION requires at least two regions."
        )

    resolved_sets: list[set[str]] = []

    for raw_region in raw_regions:
        child_region = Region(
            type=RegionType(raw_region["type"]),
            parameters={
                key: value
                for key, value in raw_region.items()
                if key != "type"
            },
        )

        resolved_sets.append(
            set(resolve_region(child_region, cells))
        )

    common_ids = set.intersection(*resolved_sets)

    cell_map = {
        cell.id: cell
        for cell in cells
    }

    return sorted(
        common_ids,
        key=lambda cell_id: (
            cell_map[cell_id].row,
            cell_map[cell_id].column,
        ),
    )

def resolve_region(
    region: Region,
    cells: tuple[Cell, ...],
) -> list[str]:
    if region.type == RegionType.ROW:
        index = region.parameters.get("index")

        if not isinstance(index, int):
            raise RegionResolutionError(
                "ROW region requires integer 'index'."
            )

        result = _resolve_row(index, cells)

    elif region.type == RegionType.COLUMN:
        index = region.parameters.get("index")

        if not isinstance(index, int):
            raise RegionResolutionError(
                "COLUMN region requires integer 'index'."
            )

        result = _resolve_column(index, cells)

    elif region.type == RegionType.NEIGHBORS:
        target_cell = region.parameters.get("cell")

        if not isinstance(target_cell, str):
            raise RegionResolutionError(
                "NEIGHBORS region requires string 'cell'."
            )

        result = _resolve_neighbors(target_cell, cells)

    elif region.type == RegionType.EXPLICIT:
        requested_ids = region.parameters.get("cells")

        if not isinstance(requested_ids, list):
            raise RegionResolutionError(
                "EXPLICIT region requires list 'cells'."
            )

        result = _resolve_explicit(requested_ids, cells)

    elif region.type == RegionType.INTERSECTION:
        raw_regions = region.parameters.get("regions")

        if not isinstance(raw_regions, list):
            raise RegionResolutionError(
                "INTERSECTION requires list 'regions'."
            )

        result = _resolve_intersection(raw_regions, cells)

    else:
        raise RegionResolutionError(
            f"Unsupported region type: {region.type}"
        )

    if not result:
        raise RegionResolutionError(
            f"Region resolves to no cells: {region}"
        )

    return result

def parse_region(raw_region: dict) -> Region:
    if not isinstance(raw_region, dict):
        raise RegionResolutionError(
            "Region must be a dictionary."
        )

    try:
        region_type = RegionType(raw_region["type"])
    except KeyError as exc:
        raise RegionResolutionError(
            "Region is missing 'type'."
        ) from exc
    except ValueError as exc:
        raise RegionResolutionError(
            f"Unsupported region type: {raw_region.get('type')}"
        ) from exc

    parameters = {
        key: value
        for key, value in raw_region.items()
        if key != "type"
    }

    return Region(
        type=region_type,
        parameters=parameters,
    )