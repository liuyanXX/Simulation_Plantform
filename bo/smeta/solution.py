"""方案元空间 · 方案对象业务模型

方案对象由 4 个信息段组合而成:
  - 基础信息 (SolutionBaseInfo)  -> 方案当前状态快照
  - 关键信息 (SolutionKeyInfo)   -> 目的/目标/举措/组织/人员/限制/风险/问题等
  - 文档信息 (SolutionDocInfo)    -> 主文档/附件文档/参考文档 (File.id 列表)
  - 修订信息 (RevisionRecord)     -> 每条修订一条记录, 完整轨迹

SQLite 无原生数组, 所以 Service 层将 List[str]/List[int] 自动序列化到 TEXT 列(JSON)。
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
    """方案状态 (业务枚举, 可自由扩展)。"""

    DRAFT = "草稿"
    REVIEWING = "评审中"
    APPROVED = "已批准"
    REJECTED = "已驳回"
    ARCHIVED = "已归档"


class SolutionBaseInfo(BaseModel):
    """基础信息。"""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(default="", description="方案ID(UUID4 hex, 业务唯一)")
    solution_name: str = Field(min_length=1, max_length=256, description="方案名称(业务唯一)")
    major_version: int = Field(default=1, ge=0, description="主版本号 (递增)")
    minor_version: int = Field(default=0, ge=0, description="次版本号 (递增)")
    status: str = Field(default=SolutionStatus.DRAFT.value, max_length=32)
    category: Optional[str] = Field(default=None, max_length=64, description="方案类别/领域, 可选")
    summary: Optional[str] = Field(default=None, description="方案摘要, 可选")


class SolutionKeyInfo(BaseModel):
    """关键信息 (全部可选, 便于渐进式填充)。"""

    model_config = ConfigDict(populate_by_name=True)

    purpose: List[str] = Field(default_factory=list, description="目的(列表)")
    objectives: List[str] = Field(default_factory=list, description="目标(列表)")
    measures: List[str] = Field(default_factory=list, description="举措(列表)")
    organizations: List[str] = Field(default_factory=list, description="组织(列表)")
    personnel: List[str] = Field(default_factory=list, description="人员(列表)")
    work_mechanism: Optional[str] = Field(default=None, description="工作机制描述(长文本)")
    work_content: Optional[str] = Field(default=None, description="工作内容描述(长文本)")
    constraints: List[str] = Field(default_factory=list, description="限制条件(列表)")
    risk_list: List[str] = Field(default_factory=list, description="风险清单(列表)")
    issue_list: List[str] = Field(default_factory=list, description="问题清单(列表)")
    notes: Optional[str] = Field(default=None, description="其它说明(长文本)")


class SolutionDocInfo(BaseModel):
    """文档信息 (File.id 列表)。"""

    model_config = ConfigDict(populate_by_name=True)

    main_docs: List[str] = Field(default_factory=list, description="主文档 File.id 列表")
    attachments: List[str] = Field(default_factory=list, description="附件文档 File.id 列表")
    references: List[str] = Field(default_factory=list, description="参考文档 File.id 列表")


class RevisionRecord(BaseModel):
    """单条修订记录 (Service 层追加式维护)。"""

    model_config = ConfigDict(populate_by_name=True)

    revision_no: int = Field(ge=1, description="修订序号, 从 1 开始递增")
    modifier: str = Field(min_length=1, max_length=64, description="创建/修改人")
    modified_at: str = Field(default_factory=_now_iso, description="创建/修改时间 ISO")
    change_summary: str = Field(min_length=1, description="创建/修改内容(描述)")


class Solution(BaseModel):
    """方案对象 (四个信息段组合)。"""

    model_config = ConfigDict(populate_by_name=True)

    base: SolutionBaseInfo = Field(default_factory=SolutionBaseInfo)
    key: SolutionKeyInfo = Field(default_factory=SolutionKeyInfo)
    doc: SolutionDocInfo = Field(default_factory=SolutionDocInfo)
    revisions: List[RevisionRecord] = Field(default_factory=list)
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

    def to_flat_dict(self, include_revisions: bool = True) -> Dict[str, Any]:
        """展平字典, 便于 Service 层读写 DB (JSON 字段在 Service 层处理)。"""
        data: Dict[str, Any] = {}
        data.update(self.base.model_dump())
        data.update({f"key_{k}": v for k, v in self.key.model_dump().items()})
        data.update({f"doc_{k}": v for k, v in self.doc.model_dump().items()})
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
    modifier: str = "system",
    summary: Optional[str] = None,
    category: Optional[str] = None,
) -> Solution:
    """快捷构造 (自动分配 ID + 初始修订记录)。"""
    s = Solution(
        base=SolutionBaseInfo(
            id=_gen_id(),
            solution_name=solution_name.strip(),
            major_version=1,
            minor_version=0,
            status=SolutionStatus.DRAFT.value,
            summary=summary,
            category=category,
        )
    )
    s.add_revision(modifier, "创建方案")
    return s
