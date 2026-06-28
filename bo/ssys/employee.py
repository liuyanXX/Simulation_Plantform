"""Employee 业务对象 (系统空间 · 人员对象)。

使用 Pydantic 规范约束, 持久化存储于 ssys_employee 表。
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


class Employee(BaseModel):
    """系统空间 · 人员对象 (Employee)。

    归属组织 ID (org_id) 应对应系统空间组织对象 (ssys_organization) 的主键 ID。
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[int] = Field(default=None, description="人员唯一主键ID(数据库自增)")
    emp_code: str = Field(min_length=1, max_length=64, description="人员编码(业务唯一)")
    emp_name: str = Field(min_length=1, max_length=64, description="姓名")
    position: Optional[str] = Field(default=None, max_length=64, description="职位/岗位")
    org_id: Optional[int] = Field(default=None, description="归属组织ID(对应 ssys_organization.id)")
    org_name: Optional[str] = Field(default=None, description="归属组织名称(冗余字段,便于直接展示)")
    email: Optional[str] = Field(default=None, max_length=128, description="邮箱")
    phone: Optional[str] = Field(default=None, max_length=32, description="联系电话")
    status: str = Field(default="active", max_length=16, description="状态: active/disabled")
    extra_info: Optional[str] = Field(default=None, description="扩展信息(JSON TEXT)")
    created_at: str = Field(default_factory=_now_iso, description="创建时间(ISO)")
    updated_at: str = Field(default_factory=_now_iso, description="更新时间(ISO)")

    @field_validator("emp_code", "emp_name")
    @classmethod
    def _trim_str(cls, v: str) -> str:
        return v.strip()

    @field_validator("status")
    @classmethod
    def _valid_status(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in {"active", "disabled", "archived", "resigned"}:
            raise ValueError(f"status must be active/disabled/archived/resigned, got '{v}'")
        return v

    def to_dict(self, include_id: bool = True) -> Dict[str, Any]:
        data = self.model_dump()
        if not include_id:
            data.pop("id", None)
        return data


class EmployeeTreeNode(BaseModel):
    """按归属组织构建的 Employee 运行时树视图 (可选)。"""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    org_id: int
    org_name: str
    employees: List[Employee] = Field(default_factory=list)
    children: List["EmployeeTreeNode"] = Field(default_factory=list)


EmployeeTreeNode.model_rebuild()
