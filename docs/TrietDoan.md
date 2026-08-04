# MEMBER 3 — GUI, CHARACTER DATA, OCCUPATIONS, AND AVATAR ASSETS

## 1. Role

Member 3 is responsible for the visual part of the project and the reusable character asset library.

This role contains two related work packages:

1. Prepare 25 characters, 25 occupations, and 25 matching avatar files.
2. Build the graphical interface that displays the board and communicates with the Game Engine through public interfaces.

The GUI must not inspect hidden solutions or unrevealed clues.

## 2. Assigned files and folders

```text
gui/app.py
gui/game_screen.py
gui/components.py
data/characters.json
assets/characters/
assets/icons/
tests/test_characters.py
```

The member may create additional GUI files if necessary, but should avoid changing shared logic or game files.

## 3. Character data requirements

### 3.1 Number of characters

Prepare exactly 25 reusable characters because the largest required board is 5×5.

Recommended distribution:

```text
13 female and 12 male
or
12 female and 13 male
```

### 3.2 Uniqueness

The following must be unique:

```text
character ID
display name
occupation
avatar file
```

### 3.3 Logical meaning

Names, genders, occupations, and avatars are display information only. They do not imply Criminal or Innocent status.

Do not add these fields to character data:

```text
verdict
criminal
innocent
solution
clue
```

Those values belong to level and game-state data.

## 4. Proposed character list

The list may be adjusted after discussion with the team leader, but IDs and file naming must remain consistent.

| ID | Name | Gender | Occupation |
|---|---|---|---|
| char_01 | Alice | female | Astronomer |
| char_02 | Benjamin | male | Baker |
| char_03 | Clara | female | Chemist |
| char_04 | Daniel | male | Dentist |
| char_05 | Emma | female | Engineer |
| char_06 | Felix | male | Farmer |
| char_07 | Grace | female | Geologist |
| char_08 | Henry | male | Historian |
| char_09 | Iris | female | Interpreter |
| char_10 | Julian | male | Journalist |
| char_11 | Katherine | female | Lawyer |
| char_12 | Liam | male | Librarian |
| char_13 | Mia | female | Musician |
| char_14 | Noah | male | Nurse |
| char_15 | Olivia | female | Photographer |
| char_16 | Peter | male | Programmer |
| char_17 | Quinn | female | Researcher |
| char_18 | Ryan | male | Sailor |
| char_19 | Sophia | female | Teacher |
| char_20 | Thomas | male | Veterinarian |
| char_21 | Uma | female | Writer |
| char_22 | Victor | male | Architect |
| char_23 | Wendy | female | Designer |
| char_24 | Xavier | male | Mechanic |
| char_25 | Zoe | female | Detective |

## 5. `characters.json` format

Each item must follow:

```json
{
  "id": "char_01",
  "name": "Alice",
  "gender": "female",
  "occupation": "Astronomer",
  "avatar_path": "assets/characters/char_01.png"
}
```

The final file must be a JSON list containing 25 items.

## 6. Avatar requirements

### 6.1 File standard

```text
Format: PNG
Aspect ratio: 1:1
Recommended size: 256×256 or 512×512
File names: char_01.png through char_25.png
Location: assets/characters/
```

### 6.2 Visual consistency

All avatars should use a consistent:

```text
art style
background style
crop
camera angle
lighting level
resolution
```

Recommended framing:

```text
head-and-shoulders portrait
centered face
clear silhouette
no text
no watermark
```

### 6.3 Profession visibility

It is helpful, but not mandatory, for clothing or small visual details to suggest the occupation. The avatar should not contain written job labels.

### 6.4 Copyright and source tracking

Use only assets that the team is permitted to use.

For externally sourced assets:

- Record the source.
- Record the creator if available.
- Record the license.
- Keep attribution notes for the report.

Do not use random copyrighted portraits, celebrity photos, or images with visible watermarks.

### 6.5 Early-stage fallback

During the first 2–3 days:

- At least 9 unique avatars must be available for the 3×3 test level.
- The remaining characters may temporarily use a placeholder.
- Before final delivery, all 25 characters must have their own avatar.

## 7. Character data validation

Create:

```text
tests/test_characters.py
```

Required checks:

```text
characters.json exists
JSON root is a list
exactly 25 characters
all required fields exist
all IDs are unique
all names are unique
all occupations are unique
gender values are valid
all avatar paths are valid before final delivery
```

Suggested test:

```python
import json
from pathlib import Path


def test_character_data():
    path = Path("data/characters.json")

    with path.open("r", encoding="utf-8") as file:
        characters = json.load(file)

    assert isinstance(characters, list)
    assert len(characters) == 25

    ids = [item["id"] for item in characters]
    names = [item["name"] for item in characters]
    occupations = [item["occupation"] for item in characters]

    assert len(ids) == len(set(ids))
    assert len(names) == len(set(names))
    assert len(occupations) == len(set(occupations))

    for item in characters:
        assert item["gender"] in {"male", "female"}
        assert item["name"].strip()
        assert item["occupation"].strip()
        assert item["avatar_path"].strip()
```

The existence check for every avatar may be enabled when all 25 files are ready.

## 8. GUI framework

Use the GUI framework selected by the team.

Possible options:

```text
Pygame
CustomTkinter
PySide6
```

Do not change the framework after implementation begins without discussing it with the team leader.

## 9. Required GUI screens

### 9.1 Application entry

`gui/app.py` should:

- Initialize the framework.
- Create the main window.
- Load or receive the Game Engine.
- Display the game screen.
- Start the application event loop.

### 9.2 Game screen

`gui/game_screen.py` should contain:

```text
board/grid area
clue or information panel
control buttons
message/status area
```

The layout must remain usable for:

```text
3×3
4×4
5×5
```

### 9.3 Reusable components

`gui/components.py` should define reusable components such as:

```text
CharacterCard
ControlPanel
CluePanel
StatusMessage
```

These may later be split into separate files.

## 10. CharacterCard requirements

Every card must be able to display:

```text
cell coordinate
avatar
character name
occupation
known verdict when revealed
clue text when revealed
face-up or face-down state
selection state
highlight state
```

Recommended interface:

```python
class CharacterCard:
    def set_data(self, cell, character, is_revealed, verdict, clue):
        ...

    def set_selected(self, selected: bool):
        ...

    def set_highlighted(self, highlighted: bool):
        ...

    def render(self):
        ...
```

Exact framework-specific details may differ.

## 11. Face-down and face-up behavior

### Face-down card

Display:

```text
coordinate
avatar or hidden-style avatar
name
occupation
unknown status
no hidden clue text
```

### Face-up card

Display:

```text
coordinate
avatar
name
occupation
CRIMINAL or INNOCENT
revealed clue
```

The GUI must never show a clue belonging to an unresolved face-down card.

## 12. Required controls

Create visible controls for:

```text
CRIMINAL
INNOCENT
RESTART
HINT
AUTO SOLVE
LOAD
```

In the first version, Hint and Auto Solve may use placeholder callbacks until the agent integration is complete.

## 13. Required Game Engine interfaces

The GUI may call:

```python
engine.get_public_state()
engine.restart()
engine.is_solved()
```

After integration:

```python
engine.submit_verdict(cell_id, verdict)
```

The GUI must not access:

```python
engine._level.hidden_solution
engine._state directly
unrevealed clues
```

## 14. Manual interaction flow

Expected flow:

```text
User selects a character card
User clicks CRIMINAL or INNOCENT
GUI calls GameEngine.submit_verdict(...)
GUI receives a SubmissionResponse
GUI updates message area
If accepted, GUI refreshes PublicState and reveals the card
```

Expected result messages:

```text
ACCEPTED
NOT_PROVABLE
CONTRADICTED
INCONSISTENT
```

## 15. Early-stage mock mode

Before `submit_verdict` is integrated, the GUI may:

- Render the initial `PublicState`.
- Allow card selection.
- Display controls.
- Use temporary mock responses for visual testing.

Mock code must be clearly marked and removed or disabled after integration.

## 16. Required GUI tests or checks

Automated GUI testing is optional in the first stage, but the member must manually verify:

1. The application opens without error.
2. The 3×3 test level fits in the window.
3. All nine cards are visible.
4. Character names and occupations match `characters.json`.
5. Only the initially revealed clue is visible.
6. Face-down cards do not expose hidden clues.
7. Selecting different cards updates the selection state.
8. Buttons do not crash the application.
9. Restart refreshes the public state after integration.
10. The layout can be adapted to 4×4 and 5×5.

## 17. Definition of Done

The task is complete when:

- `characters.json` contains 25 valid characters.
- Names, IDs, and occupations are unique.
- At least nine avatars are available for the first prototype.
- All 25 avatars are available before final delivery.
- Avatar naming and dimensions follow the agreed standard.
- The GUI displays the 3×3 board from PublicState.
- Cards correctly distinguish face-up and face-down states.
- Main buttons are visible.
- The GUI does not read hidden game data.
- Character-data tests pass.
- The branch can be integrated with the Game Engine interface.

## 18. Deliverables

```text
data/characters.json
assets/characters/char_01.png ... char_25.png
gui/app.py
gui/game_screen.py
gui/components.py
tests/test_characters.py
```

Branch suggestion:

```text
feature/gui-assets
```
