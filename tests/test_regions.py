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


def test_neighbors_accepts_new_person_key():
    level = load_level("data/levels/level_01.json")
    region = Region(RegionType.NEIGHBORS, {"person": "A1"})
    assert resolve_region(region, level.cells) == ["B1", "A2", "B2"]


def test_neighbors_accepts_center_key():
    level = load_level("data/levels/level_01.json")
    region = Region(RegionType.NEIGHBORS, {"center": "A1"})
    assert resolve_region(region, level.cells) == ["B1", "A2", "B2"]


def test_edges_region():
    level = load_level("data/levels/level_01.json")
    region = Region(RegionType.EDGES)
    assert resolve_region(region, level.cells) == [
        "A1", "B1", "C1", "A2", "C2", "A3", "B3", "C3",
    ]


def test_left_of_region():
    level = load_level("data/levels/level_01.json")
    region = Region(RegionType.LEFT_OF, {"person": "C1"})
    assert resolve_region(region, level.cells) == ["A1", "B1"]


def test_left_of_accepts_target_key():
    level = load_level("data/levels/level_01.json")
    region = Region(RegionType.LEFT_OF, {"target": "C1"})
    assert resolve_region(region, level.cells) == ["A1", "B1"]


def test_union_region_removes_duplicates_and_keeps_board_order():
    level = load_level("data/levels/level_01.json")
    region = Region(RegionType.UNION, {
        "regions": [
            {"type": "ROW", "index": 1},
            {"type": "COLUMN", "index": 1},
        ]
    })
    assert resolve_region(region, level.cells) == ["A1", "B1", "C1", "A2", "A3"]


def test_below_region_accepts_target_key():
    level = load_level("data/levels/level_01.json")
    region = Region(RegionType.BELOW, {"target": "B1"})
    assert resolve_region(region, level.cells) == ["B2", "B3"]
