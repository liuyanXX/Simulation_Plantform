"""方案元空间(business objects)."""
from .organization import Organization, OrganizationTreeNode
from .employee import Employee, EmployeeTreeNode
from .role import Role
from .file import File, FileCategory, FileCategoryEn, _category_to_cn
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
    "Organization",
    "OrganizationTreeNode",
    "Employee",
    "EmployeeTreeNode",
    "Role",
    "File",
    "FileCategory",
    "FileCategoryEn",
    "_category_to_cn",
    "Solution",
    "SolutionBaseInfo",
    "SolutionKeyInfo",
    "SolutionDocInfo",
    "SolutionStatus",
    "RevisionRecord",
    "new_solution",
]
