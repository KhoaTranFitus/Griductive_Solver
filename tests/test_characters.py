import pytest

from core.exceptions import CharacterLoadError
from gui.character_loader import load_characters


def test_load_character_catalog():
    catalog = load_characters("data/characters.json")

    assert catalog["char_01"].name == "Alice"
    assert catalog["char_01"].gender == "female"


def test_character_loader_rejects_duplicate_ids(tmp_path):
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
