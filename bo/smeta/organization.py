"""方案元空间 · 组织对象业务模型

方案元空间组织对象 = 系统空间组织对象的完整结构复制 +
                    扩展 solution_id / solution_version 两个属性,
                    用于唯一标识该组织对象所属的方案对象。
"""
from __future__ import annotations
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


class Organization(BaseModel):
    """方案元空间 · Organization 持久化业务对象 (对应表 smeta_organization)。"""

    model_config = ConfigDict(from_attributes=True, extra="allow")

    id: Optional[int] = None
    solution_id: str
    solution_version: str
    org_code: str
    org_name: str
    org_type: str = "ORG"
    description: Optional[str] = None
    parent_id: Optional[int] = None
    parent_name: Optional[str] = None
    sort_order: int = 0
    status: str = "active"
    extra_info: Optional[str] = None
    created_at: str = Field(
        default_factory=lambda: datetime.now().replace(microsecond=0).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now().replace(microsecond=0).isoformat()
    )

    def to_dict(self, include_id: bool = True) -> Dict[str, Any]:
        data = self.model_dump()
        if not include_id:
            data.pop("id", None)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Organization":
        return cls(**{k: v for k, v in data.items() if k != "extra_info"})


class OrganizationTreeNode(BaseModel):
    """方案元空间 · 运行时组织树节点(含 children)。"""

    model_config = ConfigDict(from_attributes=True, extra="allow")

    id: int
    solution_id: str
    solution_version: str
    org_code: str
    org_name: str
    org_type: str = "ORG"
    description: Optional[str] = None
    parent_id: Optional[int] = None
    parent_name: Optional[str] = None
    sort_order: int = 0
    status: str = "active"
    extra_info: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    children: List["OrganizationTreeNode"] = Field(default_factory=list)

    @classmethod
    def from_org(
        cls,
        org: Organization,
        children: Optional[List["OrganizationTreeNode"]] = None,
    ) -> "OrganizationTreeNode":
        extra_info_parsed: Optional[Dict[str, Any]] = None
        if isinstance(org.extra_info, str) and org.extra_info.strip():
            try:
                extra_info_parsed = json.loads(org.extra_info)
            except Exception:
                extra_info_parsed = {"raw": org.extra_info}
        elif isinstance(org.extra_info, dict):
            extra_info_parsed = org.extra_info
        return cls(
            id=org.id if org.id is not None else 0,
            solution_id=org.solution_id,
            solution_version=org.solution_version,
            org_code=org.org_code,
            org_name=org.org_name,
            org_type=org.org_type,
            description=org.description,
            parent_id=org.parent_id,
            parent_name=org.parent_name,
            sort_order=org.sort_order,
            status=org.status,
            extra_info=extra_info_parsed,
            created_at=org.created_at,
            updated_at=org.updated_at,
            children=children or [],
        )

    def to_dict(self, include_children: bool = True) -> Dict[str, Any]:
        data = self.model_dump()
        if not include_children:
            data.pop("children", None)
        return data

    def to_json(self, indent: int = 2, include_children: bool = True) -> str:
        return json.dumps(
            self.to_dict(include_children=include_children),
            ensure_ascii=False,
            indent=indent,
        )

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        header = f"{pad}[{self.org_type}] {self.org_code} - {self.org_name}"
        if self.solution_id:
            header += f"  (sol={self.solution_id}@{self.solution_version})"
        lines = [header]
        for ch in self.children:
            lines.append(ch.pretty(indent + 1))
        return "\n".join(lines)

    def count_nodes(self) -> int:
        return 1 + sum(c.count_nodes() for c in self.children)

    def depth(self) -> int:
        if not self.children:
            return 0
        return 1 + max(c.depth() for c in self.children)

    def find_by_id(self, org_id: int) -> Optional["OrganizationTreeNode"]:
        if self.id == org_id:
            return self
        for c in self.children:
            found = c.find_by_id(org_id)
            if found is not None:
                return found
        return None

    def find_by_code(self, org_code: str) -> Optional["OrganizationTreeNode"]:
        if self.org_code == org_code:
            return self
        for c in self.children:
            found = c.find_by_code(org_code)
            if found is not None:
                return found
        return None

    def add_child(self, child) -> "OrganizationTreeNode":
        if isinstance(child, Organization):
            node = OrganizationTreeNode.from_org(child)
        elif isinstance(child, OrganizationTreeNode):
            node = child
        elif isinstance(child, dict):
            node = OrganizationTreeNode.from_org(Organization(**child))
        else:
            raise TypeError(f"Unsupported child type: {type(child)}")
        node.parent_id = self.id
        node.parent_name = self.org_name
        if node not in self.children:
            self.children.append(node)
            self.children.sort(key=lambda n: (n.sort_order, n.id))
        return node

    def remove_child(self, org_id: int) -> bool:
        before = len(self.children)
        self.children = [c for c in self.children if c.id != org_id]
        return len(self.children) < before


OrganizationTreeNode.model_rebuild()
