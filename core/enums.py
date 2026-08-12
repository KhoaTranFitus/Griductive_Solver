# core/enums.py
from enum import Enum


class Verdict(str, Enum):
    """
    Kết luận cuối cùng của Logic Agent đối với một nhân vật.
    - CRIMINAL: Chứng minh được là tội phạm.
    - INNOCENT: Chứng minh được là vô tội.
    - UNKNOWN: Chưa thể suy ra từ KB hiện tại.
    - INCONSISTENT: Knowledge Base bị mâu thuẫn.
    """

    CRIMINAL = "CRIMINAL"
    INNOCENT = "INNOCENT"
    UNKNOWN = "UNKNOWN"
    INCONSISTENT = "INCONSISTENT"


class SubmissionResult(str, Enum):
    """
    Kết quả khi người chơi hoặc Agent gửi một verdict.
    - ACCEPTED: Verdict được chứng minh và chấp nhận.
    - NOT_PROVABLE: Chưa đủ thông tin để chứng minh.
    - CONTRADICTED: Verdict trái với điều KB suy ra.
    - INCONSISTENT: KB hiện tại không còn thỏa mãn.
    """

    ACCEPTED = "ACCEPTED"
    NOT_PROVABLE = "NOT_PROVABLE"
    CONTRADICTED = "CONTRADICTED"
    INCONSISTENT = "INCONSISTENT"


class DeductionStatus(str, Enum):
    """Terminal outcome of a public-knowledge deduction run."""

    SOLVED = "SOLVED"
    STUCK = "STUCK"
    INCONSISTENT = "INCONSISTENT"


class ClueType(str, Enum):
    """
    Các loại clue (manh mối) được hỗ trợ trong trò chơi.
    - FACT: Khẳng định trạng thái của một người.
    - SAME: Hai người có cùng trạng thái.
    - DIFFERENT: Hai người có trạng thái khác nhau.
    - EXACTLY: Chính xác k người trong vùng là Criminal.
    - AT_LEAST: Ít nhất k người trong vùng là Criminal.
    - AT_MOST: Nhiều nhất k người trong vùng là Criminal.
    - PARITY: (Extension) Ràng buộc chẵn/lẻ số Criminal.
    """

    FACT = "FACT"
    SAME = "SAME"
    DIFFERENT = "DIFFERENT"
    EXACTLY = "EXACTLY"
    AT_LEAST = "AT_LEAST"
    AT_MOST = "AT_MOST"

    # Extension dự kiến (thêm ít nhất 2 cái)
    PARITY = "PARITY"

    COMPARE_COUNT = "COMPARE_COUNT"
    EQUAL_COUNT = "EQUAL_COUNT"

    CONNECTED = "CONNECTED"


class CountOperator(str, Enum):
    """Comparison used by COMPARE_COUNT clues."""

    GT = "GT"
    LT = "LT"


class Parity(str, Enum):
    """Required parity used by PARITY clues."""

    EVEN = "EVEN"
    ODD = "ODD"

class RegionType(str, Enum):
    """
    Xác định vùng mà một clue áp dụng.
    - ROW: Một hàng.
    - COLUMN: Một cột.
    - NEIGHBORS: Các ô lân cận.
    - EXPLICIT: Danh sách ô được chỉ định.
    - INTERSECTION: (Extension) Giao của nhiều vùng.
    """

    ROW = "ROW"
    COLUMN = "COLUMN"
    NEIGHBORS = "NEIGHBORS"
    EXPLICIT = "EXPLICIT"

    # Extension region
    INTERSECTION = "INTERSECTION"


class CardState(str, Enum):
    """
    Trạng thái hiển thị của một lá bài trên bàn chơi.
    - FACE_DOWN: Chưa lật, clue bị ẩn.
    - FACE_UP: Đã lật, clue được công khai.
    """
    FACE_DOWN = "FACE_DOWN"
    FACE_UP = "FACE_UP"
