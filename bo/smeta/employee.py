"""方案元空间 · 人员对象业务模型

方案元空间 Employee = 系统空间 Employee 的完整结构复制 +
扩展 solution_id / solution_version 两个属性，
用于唯一标识当前人员对象所属的方案对象。
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


class Employee(BaseModel):
    """方案元空间 · Employee 持久化业务对象 (对应表 smeta_employee)。"""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[int] = Field(default=None, description="自增主键ID")
    solution_id: str = Field(description="方案ID")
    solution_version: str = Field(description="方案版本号")
    emp_code: str = Field(min_length=1, max_length=64, description="人员编码(方案内唯一)")
    emp_name: str = Field(min_length=1, max_length=64, description="姓名")
    position: Optional[str] = Field(default=None, max_length=64, description="职位/岗位")
    org_id: Optional[int] = Field(default=None, description="归属组织ID(对应 smeta_organization.id)")
    org_name: Optional[str] = Field(default=None, description="归属组织名称(冗余,便于展示)")
    email: Optional[str] = Field(default=None, max_length=128, description="邮箱")
    phone: Optional[str] = Field(default=None, max_length=32, description="联系电话")
    status: str = Field(default="active", max_length=16, description="状态: active/disabled/archived/resigned")
    extra_info: Optional[str] = Field(default=None, description="扩展信息(JSON TEXT)")
    created_at: str = Field(default_factory=_now_iso, description="创建时间(ISO)")
    updated_at: str = Field(default_factory=_now_iso, description="更新时间(ISO)")

    @field_validator("emp_code", "emp_name", "solution_id", "solution_version")
    @classmethod
    def _trim_str(cls, v: str) -> str:
        return v.strip()

    @field_validator("status")
    @classmethod
    def _valid_status(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in {"active", "disabled", "archived", "resigned"}:
            raise ValueError(
                f"status must be active/disabled/archived/resigned, got '{v}'"
            )
        return v

    def to_dict(self, include_id: bool = True) -> Dict[str, Any]:
        data = self.model_dump()
        if not include_id:
            data.pop("id", None)
        return data


class EmployeeTreeNode(BaseModel):
    """方案元空间 · 按归属组织分组的运行时员工视图 (可选)。"""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    org_id: int
    org_name: str
    employees: List[Employee] = Field(default_factory=list)
    children: List["EmployeeTreeNode"] = Field(default_factory=list)


EmployeeTreeNode.model_rebuild()
