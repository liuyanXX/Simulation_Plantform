"""拆分行为对象类

记录对一个方案的一次拆分行为，包括拆分策略、拆分过程日志、拆分结果概要等。
"""
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class DecompositionStrategy(str, Enum):
    AUTO = "auto"
    MANUAL = "manual"
    HYBRID = "hybrid"


class DecompositionBehaviorStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DecompositionBehavior(BaseModel):
    """
    拆分行为对象类

    表示一次针对结构化方案的拆分操作。
    """
    behavior_id: str = Field(description="拆分行为唯一标识")
    solution_id: str = Field(description="被拆分的方案ID")
    solution_name: Optional[str] = Field(default=None, description="被拆分的方案名称（冗余）")
    strategy: DecompositionStrategy = Field(
        default=DecompositionStrategy.AUTO,
        description="拆分策略：auto / manual / hybrid"
    )
    status: DecompositionBehaviorStatus = Field(
        default=DecompositionBehaviorStatus.COMPLETED,
        description="拆分状态"
    )
    organizations: Optional[List[Dict[str, Any]]] = Field(default=None, description="仿真组织列表")
    personnel: Optional[List[Dict[str, Any]]] = Field(default=None, description="仿真人员列表")
    roles: Optional[List[Dict[str, Any]]] = Field(default=None, description="仿真角色列表")
    task_manifest_id: Optional[str] = Field(default=None, description="生成的任务清单ID")
    tasks_graph_id: Optional[str] = Field(default=None, description="生成的任务图谱ID")
    flow_groups: Optional[List[Dict[str, Any]]] = Field(default=None, description="任务流组列表")
    tasks: Optional[List[Dict[str, Any]]] = Field(default=None, description="任务列表")
    process_log: Optional[str] = Field(default=None, description="拆分过程日志（文本）")
    result_summary: Optional[str] = Field(default=None, description="拆分结果概要")
    created_by: Optional[str] = Field(default=None, description="执行人")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    def to_json(self) -> Dict[str, Any]:
        data = self.model_dump(mode="json")
        data["strategy"] = self.strategy.value if isinstance(self.strategy, DecompositionStrategy) else self.strategy
        data["status"] = self.status.value if isinstance(self.status, DecompositionBehaviorStatus) else self.status
        return data

    def set_organizations(self, orgs: list) -> None:
        self.organizations = orgs

    def set_personnel(self, personnel: list) -> None:
        self.personnel = personnel

    def set_roles(self, roles: list) -> None:
        self.roles = roles

    def set_flow_groups(self, groups: list) -> None:
        self.flow_groups = groups

    def set_tasks(self, tasks: list) -> None:
        self.tasks = tasks

    def append_process_log(self, line: str) -> None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.process_log:
            self.process_log += f"\n[{ts}] {line}"
        else:
            self.process_log = f"[{ts}] {line}"
