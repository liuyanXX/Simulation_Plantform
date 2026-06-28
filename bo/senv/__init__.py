"""仿真虚空间(business objects)."""
from .solution import (
    Solution,
    SolutionBaseInfo,
    SolutionKeyInfo,
    SolutionDocInfo,
    SolutionStatus,
    RevisionRecord,
    new_solution,
)

__all__ = [
    "Solution",
    "SolutionBaseInfo",
    "SolutionKeyInfo",
    "SolutionDocInfo",
    "SolutionStatus",
    "RevisionRecord",
    "new_solution",
]
