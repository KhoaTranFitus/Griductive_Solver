# Griductive Data Format

Tài liệu này là hợp đồng dữ liệu chung giữa Level Loader, Validator, CNF
Encoder, Deductive Agent, Game Engine và GUI.

## 1. Quy ước chung

- Tất cả file JSON sử dụng UTF-8.
- Tọa độ ô có dạng `A1`, `B1`, `A2`, ...
- `row` và `column` bắt đầu từ 1.
- Thứ tự chuẩn của ô là row-major: tăng dần theo `(row, column)`.
- `CRIMINAL` tương ứng giá trị logic `True`.
- `INNOCENT` tương ứng giá trị logic `False`.
- Logic chỉ đọc dữ liệu có cấu trúc trong `data`; không phân tích
  `display_text`.

Ví dụ thứ tự chuẩn của bàn 3x3:

```text
A1, B1, C1, A2, B2, C2, A3, B3, C3
```

`load_level()` luôn sắp xếp `Level.cells` theo thứ tự này, kể cả khi mảng
`cells` trong JSON bị xáo trộn.

## 2. Character data

`data/characters.json` là một JSON list. Mỗi phần tử có dạng:

```json
{
  "id": "char_01",
  "name": "Alice",
  "gender": "female",
  "occupation": "Astronomer",
  "avatar_path": "assets/characters/char_01.png"
}
```

Các field bắt buộc:

- `id`: mã nhân vật duy nhất.
- `name`: tên hiển thị duy nhất.
- `gender`: `male` hoặc `female`.
- `occupation`: nghề nghiệp duy nhất.
- `avatar_path`: đường dẫn ảnh đại diện.

Character data không được chứa verdict, solution hoặc clue.

## 3. Level JSON

Mỗi level là một JSON object:

```json
{
  "id": "level_01",
  "title": "First Investigation",
  "size": 3,
  "cells": [],
  "initial_revealed": ["A1"],
  "solution": {},
  "clues": []
}
```

### Field của level

- `id`: mã level.
- `title`: tiêu đề hiển thị.
- `size`: chỉ nhận `3`, `4` hoặc `5`.
- `cells`: phải có đúng `size * size` phần tử.
- `initial_revealed`: danh sách cell ID được mở khi bắt đầu.
- `solution`: ánh xạ từ mọi cell ID đến `CRIMINAL` hoặc `INNOCENT`.
- `clues`: danh sách clue của level.

`solution` là dữ liệu riêng tư. Không được đưa nó vào `PublicState`, truyền cho
Deductive Agent hoặc cho GUI truy cập.

## 4. Cell

```json
{
  "id": "B2",
  "row": 2,
  "column": 2,
  "character_id": "char_05",
  "clue_id": "clue_B2"
}
```

- `id`: cell ID duy nhất.
- `row`, `column`: vị trí duy nhất trên bàn.
- `character_id`: tham chiếu đến một character.
- `clue_id`: tham chiếu đến clue thuộc ô đó.

Các cell phải phủ đủ mọi vị trí của bàn. Cell ID, vị trí và character ID không
được trùng nhau trong cùng một level.

## 5. Clue chung

Mọi clue có cấu trúc:

```json
{
  "id": "clue_A1",
  "owner_cell": "A1",
  "type": "FACT",
  "data": {},
  "display_text": "Alice is innocent."
}
```

- `id`: clue ID duy nhất.
- `owner_cell`: ô sẽ làm clue này được công khai khi lật.
- `type`: loại clue.
- `data`: dữ liệu logic theo từng loại clue.
- `display_text`: chuỗi chỉ dùng để hiển thị.

## 6. Các loại clue

### 6.1 FACT

```json
{
  "type": "FACT",
  "data": {
    "person": "A1",
    "status": "INNOCENT"
  }
}
```

- `person` phải là cell ID hợp lệ.
- `status` chỉ được là `CRIMINAL` hoặc `INNOCENT`.
- `UNKNOWN` và `INCONSISTENT` không hợp lệ trong FACT.

### 6.2 SAME

```json
{
  "type": "SAME",
  "data": {
    "person1": "A1",
    "person2": "B1"
  }
}
```

`person1` và `person2` phải là hai cell ID hợp lệ, khác nhau. Hai người có cùng
verdict.

### 6.3 DIFFERENT

```json
{
  "type": "DIFFERENT",
  "data": {
    "person1": "A1",
    "person2": "B1"
  }
}
```

`person1` và `person2` phải là hai cell ID hợp lệ, khác nhau. Hai người có
verdict trái ngược.

### 6.4 EXACTLY

```json
{
  "type": "EXACTLY",
  "data": {
    "k": 1,
    "region": {
      "type": "ROW",
      "index": 1
    }
  }
}
```

Region phải có chính xác `k` người CRIMINAL.

### 6.5 AT_LEAST

```json
{
  "type": "AT_LEAST",
  "data": {
    "k": 1,
    "region": {
      "type": "COLUMN",
      "index": 1
    }
  }
}
```

Region phải có ít nhất `k` người CRIMINAL.

### 6.6 AT_MOST

```json
{
  "type": "AT_MOST",
  "data": {
    "k": 2,
    "region": {
      "type": "NEIGHBORS",
      "cell": "B2"
    }
  }
}
```

Region được có nhiều nhất `k` người CRIMINAL.

Đối với ba counting clue, `k` phải là integer thỏa:

```text
0 <= k <= số cell được resolve từ region
```

### 6.7 PARITY extension

```json
{
  "type": "PARITY",
  "data": {
    "parity": "EVEN",
    "region": {
      "type": "COLUMN",
      "index": 2
    }
  }
}
```

`parity` nhận `EVEN` hoặc `ODD`. Đây là extension; module mới chỉ hỗ trợ sáu
clue cơ bản có thể báo lỗi rõ ràng cho tới khi extension được tích hợp.

## 7. Region

Region trong level JSON sử dụng cấu trúc phẳng. Các tham số nằm cùng cấp với
`type`; không sử dụng object `parameters` trong JSON. `parse_region()` sẽ gom
các field còn lại vào `Region.parameters` khi chạy.

### 7.1 ROW

```json
{
  "type": "ROW",
  "index": 2
}
```

### 7.2 COLUMN

```json
{
  "type": "COLUMN",
  "index": 3
}
```

### 7.3 NEIGHBORS

```json
{
  "type": "NEIGHBORS",
  "cell": "B2"
}
```

Bao gồm tối đa tám ô xung quanh `cell`, kể cả đường chéo, nhưng không bao gồm
chính ô trung tâm.

### 7.4 EXPLICIT

```json
{
  "type": "EXPLICIT",
  "cells": ["A1", "B2", "C3"]
}
```

Mọi ID phải hợp lệ và không được lặp trong danh sách.

### 7.5 INTERSECTION extension

```json
{
  "type": "INTERSECTION",
  "regions": [
    {"type": "ROW", "index": 2},
    {"type": "COLUMN", "index": 2}
  ]
}
```

Phải có ít nhất hai region con. Kết quả là giao của các region và được trả về
theo thứ tự row-major.

## 8. PublicState

Game Engine chỉ công khai các field:

```text
level_id: str
size: int
cells: tuple[Cell, ...]
revealed_clues: tuple[Clue, ...]
proved_verdicts: dict[str, Verdict]
unresolved_cells: tuple[str, ...]
```

- `revealed_clues` chỉ chứa clue của các card đã lật.
- `proved_verdicts` chỉ chứa verdict đã được chứng minh và chấp nhận.
- `unresolved_cells` theo thứ tự row-major.
- `PublicState` không chứa hidden solution hoặc unrevealed clues.

## 9. CNF contract

CNF sử dụng:

```python
list[list[int]]
```

- Literal dương nghĩa là CRIMINAL.
- Literal âm nghĩa là INNOCENT.
- Primary variable bắt đầu từ 1.
- Cell được gán variable theo thứ tự row-major.
- Cell ID không tồn tại phải gây ra lỗi rõ ràng.

Ví dụ:

```python
[
    [1, -2],
    [-1, 3],
    [2],
]
```
