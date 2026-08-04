# core/exceptions.py
class GriductiveError(Exception):
    """Base exception for the Griductive project."""


class LevelLoadError(GriductiveError):
    """Raised when a level file cannot be loaded."""


class LevelValidationError(GriductiveError):
    """Raised when level data is invalid."""


class RegionResolutionError(GriductiveError):
    """Raised when a region cannot be resolved."""


class UnsupportedClueError(GriductiveError):
    """Raised when a clue type is unsupported."""


class SolverError(GriductiveError):
    """Raised when the SAT solver encounters an invalid state."""