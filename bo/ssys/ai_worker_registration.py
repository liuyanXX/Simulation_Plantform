"""智能员工注册业务对象 (系统空间 · 智能员工注册)

用于管理系统中可用的智能员工类型注册信息, 记录员工类型、全路径类名、
最大数量等配置, 持久化存储于 ssys_ai_worker_registry 表。

各模块可通过 AIWorkerRegistryService 提供的服务函数按类型/编码获取注册信息,
从而动态实例化对应的智能员工。
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


class AIWorkerRegistration(BaseModel):
    """系统空间 · 智能员工注册对象 (对应表 ssys_ai_worker_registry)。

    :ivar id: 注册记录唯一主键(数据库自增)
    :ivar worker_type: 智能员工类型标识(业务唯一), 如 SolutionUnderstandingWorker
    :ivar worker_name: 智能员工类型显示名称, 如 方案理解智能员工
    :ivar class_path: 具体的全路径类名, 如 bo.ssys.aiworker.xxx.ClassName
    :ivar max_count: 该类型智能员工的最大数量(0 表示不限制)
    :ivar description: 类型说明
    :ivar status: 状态 active/disabled
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[int] = Field(default=None, description="注册记录唯一主键ID(数据库自增)")
    worker_type: str = Field(min_length=1, max_length=128, description="智能员工类型标识(业务唯一)")
    worker_name: str = Field(min_length=1, max_length=128, description="智能员工类型显示名称")
    class_path: str = Field(min_length=1, max_length=512, description="具体的全路径类名(module.ClassName)")
    max_count: int = Field(default=0, ge=0, description="最大数量, 0 表示不限制")
    description: Optional[str] = Field(default=None, description="类型说明")
    status: str = Field(default="active", max_length=16, description="状态: active/disabled")
    extra_info: Optional[str] = Field(default=None, description="扩展信息(JSON TEXT)")
    created_at: str = Field(default_factory=_now_iso, description="创建时间(ISO)")
    updated_at: str = Field(default_factory=_now_iso, description="更新时间(ISO)")

    @field_validator("worker_type", "worker_name", "class_path")
    @classmethod
    def _trim_str(cls, v: str) -> str:
        return v.strip()

    @field_validator("status")
    @classmethod
    def _valid_status(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in {"active", "disabled"}:
            raise ValueError(f"status must be active/disabled, got '{v}'")
        return v

    def to_dict(self, include_id: bool = True) -> Dict[str, Any]:
        data = self.model_dump()
        if not include_id:
            data.pop("id", None)
        return data
