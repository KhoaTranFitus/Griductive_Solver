# tests/test_characters.py
"""Comprehensive validation for the character data catalog.

Required checks per specification:
  - characters.json exists
  - JSON root is a list
  - exactly 25 characters
  - all required fields exist (id, name, gender, occupation, avatar_path)
  - all IDs are unique
  - all names are unique
  - all occupations are unique
  - gender values are valid (male/female)
  - all avatar paths reference existing files
"""

import json
from pathlib import Path

import pytest

from core.exceptions import CharacterLoadError
from gui.character_loader import load_characters

CHARACTER_FILE = Path("data/characters.json")


# ──────────────────────────────────────────────
#  Raw JSON structure tests
# ──────────────────────────────────────────────

class TestCharacterFileStructure:
    """Tests that validate the raw JSON file structure."""

    def test_characters_json_exists(self):
        assert CHARACTER_FILE.exists(), f"{CHARACTER_FILE} does not exist"

    def test_json_root_is_list(self):
        with CHARACTER_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, list), "JSON root must be a list"

    def test_exactly_25_characters(self):
        with CHARACTER_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) == 25, f"Expected 25 characters, got {len(data)}"

    def test_all_required_fields_present(self):
        required_fields = {"id", "name", "gender", "occupation", "avatar_path"}
        with CHARACTER_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        for i, item in enumerate(data):
            missing = required_fields - set(item.keys())
            assert not missing, (
                f"Character at index {i} is missing fields: {missing}"
            )

    def test_all_ids_unique(self):
        with CHARACTER_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        ids = [item["id"] for item in data]
        assert len(ids) == len(set(ids)), f"Duplicate IDs found: {ids}"

    def test_all_names_unique(self):
        with CHARACTER_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        names = [item["name"] for item in data]
        assert len(names) == len(set(names)), f"Duplicate names found: {names}"

    def test_all_occupations_unique(self):
        with CHARACTER_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        occupations = [item["occupation"] for item in data]
        assert len(occupations) == len(set(occupations)), (
            f"Duplicate occupations found: {occupations}"
        )

    def test_gender_values_valid(self):
        with CHARACTER_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            assert item["gender"] in {"male", "female"}, (
                f"Invalid gender '{item['gender']}' for {item['id']}"
            )

    def test_names_not_blank(self):
        with CHARACTER_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            assert item["name"].strip(), (
                f"Blank name for {item['id']}"
            )

    def test_occupations_not_blank(self):
        with CHARACTER_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            assert item["occupation"].strip(), (
                f"Blank occupation for {item['id']}"
            )

    def test_avatar_paths_not_blank(self):
        with CHARACTER_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            assert item["avatar_path"].strip(), (
                f"Blank avatar_path for {item['id']}"
            )

    def test_no_forbidden_fields(self):
        """Character data must not include verdict/criminal/innocent/solution/clue."""
        forbidden = {"verdict", "criminal", "innocent", "solution", "clue"}
        with CHARACTER_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            found = forbidden & set(item.keys())
            assert not found, (
                f"Character {item['id']} has forbidden fields: {found}"
            )


# ──────────────────────────────────────────────
#  Avatar file existence tests
# ──────────────────────────────────────────────

class TestAvatarFiles:
    """Tests that validate avatar file existence."""

    def test_all_avatar_files_exist(self):
        with CHARACTER_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            avatar = Path(item["avatar_path"])
            assert avatar.exists(), (
                f"Avatar file missing for {item['id']}: {item['avatar_path']}"
            )


# ──────────────────────────────────────────────
#  Character loader integration tests
# ──────────────────────────────────────────────

class TestCharacterLoader:
    """Tests that validate the character_loader module."""

    def test_load_character_catalog(self):
        catalog = load_characters(CHARACTER_FILE)
        assert len(catalog) == 25
        assert catalog["char_01"].name == "Alice"
        assert catalog["char_01"].gender == "female"
        assert catalog["char_25"].name == "Zoe"
        assert catalog["char_25"].occupation == "Detective"

    def test_all_ids_in_catalog(self):
        catalog = load_characters(CHARACTER_FILE)
        for i in range(1, 26):
            cid = f"char_{i:02d}"
            assert cid in catalog, f"Missing character ID: {cid}"

    def test_character_loader_rejects_duplicate_ids(self, tmp_path):
        path = tmp_path / "characters.json"
        path.write_text(
            """[
              {"id":"x","name":"A","gender":"female","occupation":"One","avatar_path":"a.png"},
              {"id":"x","name":"B","gender":"male","occupation":"Two","avatar_path":"b.png"}
            ]""",
            encoding="utf-8",
        )
        with pytest.raises(CharacterLoadError, match="Duplicate character ID"):
            load_characters(path)

    def test_character_loader_rejects_invalid_gender(self, tmp_path):
        path = tmp_path / "characters.json"
        path.write_text(
            """[
              {"id":"x","name":"A","gender":"other","occupation":"One","avatar_path":"a.png"}
            ]""",
            encoding="utf-8",
        )
        with pytest.raises(CharacterLoadError, match="Invalid gender"):
            load_characters(path)

    def test_character_loader_rejects_duplicate_names(self, tmp_path):
        path = tmp_path / "characters.json"
        path.write_text(
            """[
              {"id":"a","name":"Same","gender":"female","occupation":"One","avatar_path":"a.png"},
              {"id":"b","name":"Same","gender":"male","occupation":"Two","avatar_path":"b.png"}
            ]""",
            encoding="utf-8",
        )
        with pytest.raises(CharacterLoadError, match="Duplicate character name"):
            load_characters(path)

    def test_character_loader_rejects_duplicate_occupations(self, tmp_path):
        path = tmp_path / "characters.json"
        path.write_text(
            """[
              {"id":"a","name":"Alice","gender":"female","occupation":"Job","avatar_path":"a.png"},
              {"id":"b","name":"Bob","gender":"male","occupation":"Job","avatar_path":"b.png"}
            ]""",
            encoding="utf-8",
        )
        with pytest.raises(CharacterLoadError, match="Duplicate occupation"):
            load_characters(path)

    def test_character_loader_rejects_non_list_root(self, tmp_path):
        path = tmp_path / "characters.json"
        path.write_text('{"key": "value"}', encoding="utf-8")
        with pytest.raises(CharacterLoadError, match="JSON list"):
            load_characters(path)
