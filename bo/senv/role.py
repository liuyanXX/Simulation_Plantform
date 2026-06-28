"""仿真虚空间 · 角色对象业务模型

仿真虚空间 Role = 系统空间 Role 的完整结构复制 +
扩展 task_id(仿真任务ID) / batch_no(仿真任务批次号) 两个属性，
用于唯一标识当前角色对象所属的仿真任务。
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


class Role(BaseModel):
    """仿真虚空间 · Role 持久化业务对象 (对应表 senv_role)。"""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[int] = Field(default=None, description="自增主键ID")
    task_id: str = Field(description="仿真任务ID")
    batch_no: str = Field(description="仿真任务批次号")
    role_code: str = Field(min_length=1, max_length=64, description="角色编码(任务批次内唯一)")
    role_name: str = Field(min_length=1, max_length=64, description="角色名称")
    description: Optional[str] = Field(default=None, description="角色描述")
    status: str = Field(default="active", max_length=16, description="状态: active/disabled/archived")
    extra_info: Optional[str] = Field(default=None, description="扩展信息(JSON TEXT)")
    created_at: str = Field(default_factory=_now_iso, description="创建时间(ISO)")
    updated_at: str = Field(default_factory=_now_iso, description="更新时间(ISO)")

    @field_validator("role_code", "role_name", "task_id", "batch_no")
    @classmethod
    def _trim_str(cls, v: str) -> str:
        return v.strip()

    @field_validator("status")
    @classmethod
    def _valid_status(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in {"active", "disabled", "archived"}:
            raise ValueError(
                f"status must be active/disabled/archived, got '{v}'"
            )
        return v

    def to_dict(self, include_id: bool = True) -> Dict[str, Any]:
        data = self.model_dump()
        if not include_id:
            data.pop("id", None)
        return data
