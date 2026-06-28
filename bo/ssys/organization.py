"""Organization 业务对象 (系统空间 · 组织对象)

使用 Pydantic 规范约束。持久化存储于 ssys_organization 表。
"""
from __future__ import annotations
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict


class Organization(BaseModel):
    """系统空间·组织对象 (Organization)。

    用于描述仿真平台系统空间中的一棵组织树中的单个组织节点。
    持久化表名: ssys_organization。

    示例:
        root = Organization(
            org_name="仿真平台总公司",
            org_code="ROOT",
            org_type="COMPANY",
        )
        child = Organization(
            org_name="仿真研发部",
            org_code="RD",
            org_type="DEPARTMENT",
            parent_id=None,
        )
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: Optional[int] = Field(
        default=None,
        description="组织主键ID(数据库自增唯一)",
    )
    org_code: str = Field(
        description="组织编码(业务唯一标识, 建议大写+下划线, 如 'RD_CENTER')",
        min_length=1,
        max_length=64,
    )
    org_name: str = Field(
        description="组织名称",
        min_length=1,
        max_length=128,
    )
    org_type: str = Field(
        default="ORG",
        description="组织类型(COMPANY/DEPARTMENT/TEAM/GROUP/ORG)",
        max_length=32,
    )
    description: Optional[str] = Field(
        default=None,
        description="组织说明",
    )
    parent_id: Optional[int] = Field(
        default=None,
        description="父组织ID(自关联, 顶级组织为 NULL)",
    )
    parent_name: Optional[str] = Field(
        default=None,
        description="父组织名称(冗余字段, 便于前端/API直接展示)",
    )
    sort_order: int = Field(
        default=0,
        description="同级排序序号(越小越靠前)",
    )
    status: str = Field(
        default="active",
        description="状态(active/disabled/archived)",
        max_length=16,
    )
    extra_info: Optional[Dict[str, Any]] = Field(
        default=None,
        description="扩展信息(JSON对象, 存储额外业务属性)",
    )
    created_at: Optional[str] = Field(default=None, description="创建时间(ISO)")
    updated_at: Optional[str] = Field(default=None, description="更新时间(ISO)")

    @field_validator("org_code")
    @classmethod
    def _validate_org_code(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("org_code 不能为空")
        return v

    @field_validator("org_name")
    @classmethod
    def _validate_org_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("org_name 不能为空")
        return v

    @classmethod
    def now_iso(cls) -> str:
        return datetime.now().replace(microsecond=0).isoformat()

    def touch_created(self) -> None:
        if not self.created_at:
            self.created_at = self.now_iso()
        self.updated_at = self.now_iso()

    def touch_updated(self) -> None:
        self.updated_at = self.now_iso()

    # ---------- 树形内存辅助方法 ----------

    def describe(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "org_code": self.org_code,
            "org_name": self.org_name,
            "org_type": self.org_type,
            "parent_id": self.parent_id,
            "parent_name": self.parent_name,
            "status": self.status,
            "sort_order": self.sort_order,
        }

    def __str__(self) -> str:
        return f"Organization(id={self.id}, org_code={self.org_code}, org_name={self.org_name})"


class OrganizationTreeNode(BaseModel):
    """运行时组织树节点。

    由 SsysOrganizationService.build_organization_tree() 或 build_full_tree() 从
    数据库中把 ssys_organization 表扁平记录组装成一棵完整的内存树。

    这是 Pydantic 模型, 支持 to_json() / dict() 序列化给前端直接渲染。
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: int
    org_code: str
    org_name: str
    org_type: str = "ORG"
    description: Optional[str] = None
    parent_id: Optional[int] = None
    parent_name: Optional[str] = None
    sort_order: int = 0
    status: str = "active"
    extra_info: Optional[Dict[str, Any]] = None
    children: List["OrganizationTreeNode"] = Field(default_factory=list, description="下级组织列表")

    @classmethod
    def from_org(cls, org: Organization, children: Optional[List["OrganizationTreeNode"]] = None) -> "OrganizationTreeNode":
        return cls(
            id=int(org.id),
            org_code=org.org_code,
            org_name=org.org_name,
            org_type=org.org_type,
            description=org.description,
            parent_id=org.parent_id,
            parent_name=org.parent_name,
            sort_order=org.sort_order,
            status=org.status,
            extra_info=org.extra_info,
            children=children or [],
        )

    def to_dict(self, include_children: bool = True) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "id": self.id,
            "org_code": self.org_code,
            "org_name": self.org_name,
            "org_type": self.org_type,
            "description": self.description,
            "parent_id": self.parent_id,
            "parent_name": self.parent_name,
            "sort_order": self.sort_order,
            "status": self.status,
            "extra_info": self.extra_info,
        }
        if include_children:
            data["children"] = [c.to_dict(include_children) for c in self.children]
        return data

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def count_nodes(self) -> int:
        count = 1
        for child in self.children:
            count += child.count_nodes()
        return count

    def find_by_id(self, org_id: int) -> Optional["OrganizationTreeNode"]:
        if self.id == org_id:
            return self
        for child in self.children:
            hit = child.find_by_id(org_id)
            if hit:
                return hit
        return None

    def find_by_code(self, org_code: str) -> Optional["OrganizationTreeNode"]:
        if self.org_code == org_code:
            return self
        for child in self.children:
            hit = child.find_by_code(org_code)
            if hit:
                return hit
        return None

    def depth(self) -> int:
        if not self.children:
            return 1
        return 1 + max(c.depth() for c in self.children)

    def pretty(self, indent: int = 0) -> str:
        prefix = "  " * indent
        head = f"{prefix}- [{self.org_type}] {self.org_name} ({self.org_code}, #{self.id})"
        lines = [head]
        for child in self.children:
            lines.append(child.pretty(indent + 1))
        return "\n".join(lines)


OrganizationTreeNode.model_rebuild()
