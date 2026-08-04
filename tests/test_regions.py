# tests/test_regions.py
from core.enums import RegionType
from core.models import Region
from game.level_loader import load_level
from logic.region_resolver import resolve_region


def test_row_region():
    level = load_level("data/levels/level_01.json")

    region = Region(
        type=RegionType.ROW,
        parameters={"index": 1},
    )

    assert resolve_region(region, level.cells) == [
        "A1",
        "B1",
        "C1",
    ]


def test_column_region():
    level = load_level("data/levels/level_01.json")

    region = Region(
        type=RegionType.COLUMN,
        parameters={"index": 2},
    )

    assert resolve_region(region, level.cells) == [
        "B1",
        "B2",
        "B3",
    ]


def test_center_neighbors():
    level = load_level("data/levels/level_01.json")

    region = Region(
        type=RegionType.NEIGHBORS,
        parameters={"cell": "B2"},
    )

    assert resolve_region(region, level.cells) == [
        "A1",
        "B1",
        "C1",
        "A2",
        "C2",
        "A3",
        "B3",
        "C3",
    ]


def test_corner_neighbors():
    level = load_level("data/levels/level_01.json")

    region = Region(
        type=RegionType.NEIGHBORS,
        parameters={"cell": "A1"},
    )

    assert resolve_region(region, level.cells) == [
        "B1",
        "A2",
        "B2",
    ]