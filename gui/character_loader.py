"""Load public character metadata used only by the presentation layer."""

import json
from pathlib import Path
from typing import Any

from core.exceptions import CharacterLoadError
from core.models import Character


def load_characters(file_path: str | Path) -> dict[str, Character]:
    """Return display-only character metadata keyed by character ID."""
    path = Path(file_path)
    try:
        with path.open("r", encoding="utf-8") as source:
            raw_characters: Any = json.load(source)
    except (OSError, json.JSONDecodeError) as exc:
        raise CharacterLoadError(
            f"Cannot load character data from {path}: {exc}"
        ) from exc

    if not isinstance(raw_characters, list):
        raise CharacterLoadError("Character data root must be a JSON list.")

    catalog: dict[str, Character] = {}
    names: set[str] = set()
    occupations: set[str] = set()

    for raw in raw_characters:
        if not isinstance(raw, dict):
            raise CharacterLoadError("Every character must be a JSON object.")
        try:
            character = Character(
                id=str(raw["id"]),
                name=str(raw["name"]),
                gender=str(raw["gender"]),
                occupation=str(raw["occupation"]),
                avatar_path=str(raw["avatar_path"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise CharacterLoadError(f"Invalid character data: {raw}") from exc

        if character.gender not in {"male", "female"}:
            raise CharacterLoadError(
                f"Invalid gender for character {character.id}."
            )
        if character.id in catalog:
            raise CharacterLoadError(f"Duplicate character ID: {character.id}")
        if character.name in names:
            raise CharacterLoadError(
                f"Duplicate character name: {character.name}"
            )
        if character.occupation in occupations:
            raise CharacterLoadError(
                f"Duplicate occupation: {character.occupation}"
            )

        catalog[character.id] = character
        names.add(character.name)
        occupations.add(character.occupation)

    return catalog
