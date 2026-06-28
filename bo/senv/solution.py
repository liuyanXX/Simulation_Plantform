"""仿真虚空间 · 方案对象业务模型

在完整复制方案元空间 (bo.smeta.solution) 结构的同时, 增加:
  - simulation_task_id     仿真任务ID
  - simulation_task_batch  仿真任务批次号

三者联合唯一: (base.id, simulation_task_id, simulation_task_batch)
"""
from __future__ import annotations
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def _gen_id() -> str:
    return uuid.uuid4().hex


class SolutionStatus(str, Enum):
    """方案状态 (与方案元空间保持一致, 便于复制)。"""

    DRAFT = "草稿"
    REVIEWING = "评审中"
    APPROVED = "已批准"
    REJECTED = "已驳回"
    ARCHIVED = "已归档"
    RUNNING = "仿真中"
    FINISHED = "已完成"
    FAILED = "仿真失败"


class SolutionBaseInfo(BaseModel):
    """基础信息 (与方案元空间 SolutionBaseInfo 对齐)。"""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(default="", description="方案ID(UUID4 hex)")
    solution_name: str = Field(min_length=1, max_length=256)
    major_version: int = Field(default=1, ge=0)
    minor_version: int = Field(default=0, ge=0)
    status: str = Field(default=SolutionStatus.DRAFT.value, max_length=32)
    category: Optional[str] = Field(default=None, max_length=64)
    summary: Optional[str] = Field(default=None)


class SolutionKeyInfo(BaseModel):
    """关键信息 (与方案元空间 SolutionKeyInfo 对齐)。"""

    model_config = ConfigDict(populate_by_name=True)

    purpose: List[str] = Field(default_factory=list)
    objectives: List[str] = Field(default_factory=list)
    measures: List[str] = Field(default_factory=list)
    organizations: List[str] = Field(default_factory=list)
    personnel: List[str] = Field(default_factory=list)
    work_mechanism: Optional[str] = Field(default=None)
    work_content: Optional[str] = Field(default=None)
    constraints: List[str] = Field(default_factory=list)
    risk_list: List[str] = Field(default_factory=list)
    issue_list: List[str] = Field(default_factory=list)
    notes: Optional[str] = Field(default=None)


class SolutionDocInfo(BaseModel):
    """文档信息 (File.id 列表)。"""

    model_config = ConfigDict(populate_by_name=True)

    main_docs: List[str] = Field(default_factory=list)
    attachments: List[str] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)


class RevisionRecord(BaseModel):
    """单条修订记录。"""

    model_config = ConfigDict(populate_by_name=True)

    revision_no: int = Field(ge=1)
    modifier: str = Field(min_length=1, max_length=64)
    modified_at: str = Field(default_factory=_now_iso)
    change_summary: str = Field(min_length=1)


class Solution(BaseModel):
    """仿真虚空间方案对象 (四信息段 + 仿真任务两字段)。"""

    model_config = ConfigDict(populate_by_name=True)

    base: SolutionBaseInfo = Field(default_factory=SolutionBaseInfo)
    key: SolutionKeyInfo = Field(default_factory=SolutionKeyInfo)
    doc: SolutionDocInfo = Field(default_factory=SolutionDocInfo)
    revisions: List[RevisionRecord] = Field(default_factory=list)
    simulation_task_id: str = Field(
        default="",
        min_length=1,
        description="仿真任务ID, 联合唯一键之一",
    )
    simulation_task_batch: str = Field(
        default="",
        min_length=1,
        description="仿真任务批次号, 联合唯一键之一",
    )
    created_at: str = Field(default_factory=_now_iso)
    updated_at: str = Field(default_factory=_now_iso)

    @property
    def id(self) -> str:
        return self.base.id

    @property
    def solution_name(self) -> str:
        return self.base.solution_name

    @property
    def version_label(self) -> str:
        return f"v{self.base.major_version}.{self.base.minor_version}"

    def unique_key(self) -> str:
        return f"{self.base.id}|{self.simulation_task_id}|{self.simulation_task_batch}"

    def to_flat_dict(self, include_revisions: bool = True) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        data.update(self.base.model_dump())
        data.update({f"key_{k}": v for k, v in self.key.model_dump().items()})
        data.update({f"doc_{k}": v for k, v in self.doc.model_dump().items()})
        data["simulation_task_id"] = self.simulation_task_id
        data["simulation_task_batch"] = self.simulation_task_batch
        data["created_at"] = self.created_at
        data["updated_at"] = self.updated_at
        if include_revisions:
            data["revisions"] = [r.model_dump() for r in self.revisions]
        return data

    def add_revision(self, modifier: str, change_summary: str) -> None:
        self.revisions.append(
            RevisionRecord(
                revision_no=len(self.revisions) + 1,
                modifier=modifier,
                modified_at=_now_iso(),
                change_summary=change_summary,
            )
        )
        self.updated_at = _now_iso()

    def bump_major(self, modifier: str, change_summary: str = "主版本号递增") -> None:
        self.base.major_version += 1
        self.base.minor_version = 0
        self.add_revision(modifier, f"{change_summary} ({self.version_label})")

    def bump_minor(self, modifier: str, change_summary: str = "次版本号递增") -> None:
        self.base.minor_version += 1
        self.add_revision(modifier, f"{change_summary} ({self.version_label})")


def new_solution(
    solution_name: str,
    simulation_task_id: str,
    simulation_task_batch: str,
    modifier: str = "system",
    summary: Optional[str] = None,
    category: Optional[str] = None,
) -> Solution:
    """快捷构造 (自动分配方案 ID + 初始修订)。"""
    s = Solution(
        base=SolutionBaseInfo(
            id=_gen_id(),
            solution_name=solution_name.strip(),
            major_version=1,
            minor_version=0,
            status=SolutionStatus.DRAFT.value,
            summary=summary,
            category=category,
        ),
        simulation_task_id=simulation_task_id,
        simulation_task_batch=simulation_task_batch,
    )
    s.add_revision(modifier, "创建仿真虚空间方案")
    return s
