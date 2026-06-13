from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
import json
from enum import Enum


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Task(BaseModel):
    task_id: str = Field(description="任务唯一标识")
    expected_start_time: datetime = Field(description="期望开始时间")
    expected_end_time: datetime = Field(description="期望结束时间")
    scheduled_start_time: Optional[datetime] = Field(default=None, description="排期开始时间")
    scheduled_end_time: Optional[datetime] = Field(default=None, description="排期结束时间")
    actual_start_time: Optional[datetime] = Field(default=None, description="实际开始时间")
    actual_end_time: Optional[datetime] = Field(default=None, description="实际结束时间")
    content: str = Field(description="工作内容")
    execute_role: str = Field(description="执行角色")
    resource_consumption: float = Field(description="资源消耗（工时）")
    priority: Priority = Field(description="优先级")
    output_target_role: str = Field(description="输出物目标角色")
    next_task_info: Optional[Dict[str, Any]] = Field(default=None, description="下一步任务信息")
    is_completed: bool = Field(default=False, description="任务是否完成")

    @field_validator('priority')
    @classmethod
    def priority_must_be_valid(cls, v: Priority) -> Priority:
        if v not in [Priority.HIGH, Priority.MEDIUM, Priority.LOW]:
            raise ValueError('priority must be high, medium, or low')
        return v

    @field_validator('expected_start_time', 'expected_end_time', mode='before')
    @classmethod
    def parse_datetime(cls, v: Any) -> datetime:
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00').replace(' ', 'T'))
        return v

    def to_json(self) -> str:
        return json.dumps(self.model_dump(mode='json'), ensure_ascii=False, indent=2)
