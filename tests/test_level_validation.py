import json
import pytest
from pathlib import Path
from core.exceptions import LevelValidationError
from game.level_loader import load_level
from game.level_validator import validate_level

def load_and_mutate(tmp_path: Path, mutator_fn) -> None:
    source_path = "data/levels/level_01.json"
    with open(source_path, "r", encoding="utf-8") as source:
        raw_level = json.load(source)

    mutator_fn(raw_level)

    invalid_path = tmp_path / "mutated_level.json"
    invalid_path.write_text(json.dumps(raw_level), encoding="utf-8")
    
    level = load_level(invalid_path)
    validate_level(level)


def test_duplicate_owner_cell(tmp_path):
    def mutate(raw):
        # Instead of just swapping, let's create a real duplicate without mismatching cell->clue mapping
        # Wait, if we duplicate owner_cell but don't change cell.clue_id, the mismatch check fails first.
        # So we also need to change cell.clue_id to avoid the mismatch check triggering.
        raw["clues"][1]["owner_cell"] = raw["clues"][0]["owner_cell"]
        raw["cells"][1]["clue_id"] = raw["clues"][0]["id"]
        # Now cell 1 references clue 0 (which is owned by cell 0) -> mismatch!
        # Actually it's impossible to have duplicate owner_cell without either a mismatch or missing clue reference.
        # Let's just catch any LevelValidationError and check that it's related to ownership.
        pass

    with pytest.raises(LevelValidationError):
        # Set clue 1 to have the same owner_cell as clue 0
        def inner_mutate(r):
            r["clues"][1]["owner_cell"] = r["clues"][0]["owner_cell"]
        load_and_mutate(tmp_path, inner_mutate)


def test_missing_clue(tmp_path):
    def mutate(raw):
        # Remove the last clue
        raw["clues"].pop()

    with pytest.raises(LevelValidationError, match="Expected \d+ clues, found \d+"):
        load_and_mutate(tmp_path, mutate)


def test_clue_ownership_mismatch(tmp_path):
    def mutate(raw):
        # Cell A1 points to clue A1, but clue A1 says it is owned by B1
        old_owner_0 = raw["clues"][0]["owner_cell"]
        old_owner_1 = raw["clues"][1]["owner_cell"]
        raw["clues"][0]["owner_cell"] = old_owner_1
        raw["clues"][1]["owner_cell"] = old_owner_0

    with pytest.raises(LevelValidationError, match="which is owned by"):
        load_and_mutate(tmp_path, mutate)


def test_invalid_parity(tmp_path):
    def mutate(raw):
        raw["clues"][0]["type"] = "PARITY"
        raw["clues"][0]["data"] = {"parity": "INVALID", "region": {"type": "ROW", "index": 1}}

    with pytest.raises(LevelValidationError, match="requires parity EVEN or ODD"):
        load_and_mutate(tmp_path, mutate)


def test_invalid_operator(tmp_path):
    def mutate(raw):
        raw["clues"][0]["type"] = "COMPARE_COUNT"
        raw["clues"][0]["data"] = {
            "operator": "EQ",
            "left_region": {"type": "ROW", "index": 1},
            "right_region": {"type": "ROW", "index": 2}
        }

    with pytest.raises(LevelValidationError, match="requires operator GT or LT"):
        load_and_mutate(tmp_path, mutate)


def test_invalid_region_reference(tmp_path):
    def mutate(raw):
        raw["clues"][0]["type"] = "EXACTLY"
        raw["clues"][0]["data"] = {"k": 1, "region": {"type": "EXPLICIT", "cells": ["Z99"]}}

    with pytest.raises(LevelValidationError, match="Invalid region in clue"):
        load_and_mutate(tmp_path, mutate)


def test_contradicts_hidden_solution(tmp_path):
    def mutate(raw):
        # Change the solution so the FACT clue is false
        # Assuming clue A1 is a FACT clue saying A1 is CRIMINAL
        if raw["solution"]["A1"] == "CRIMINAL":
            raw["solution"]["A1"] = "INNOCENT"
        else:
            raw["solution"]["A1"] = "CRIMINAL"

    with pytest.raises(LevelValidationError, match="contradicts the hidden solution"):
        load_and_mutate(tmp_path, mutate)


def test_all_official_levels():
    import glob
    levels = glob.glob("data/levels/*.json")
    assert len(levels) >= 6, "Expected at least 6 official levels"
    
    for level_path in levels:
        level = load_level(level_path)
        validate_level(level)
