from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
from enum import Enum


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskType(str, Enum):
    NORMAL = "normal"
    START = "start"
    END = "end"
    HALT = "halt"


class Task(BaseModel):
    task_id: str = Field(description="任务唯一标识")
    task_name: str = Field(description="任务名称（人类可读）")
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
    output_target_role: str = Field(description="输出物目标角色（实际触发的下一任务的执行角色）")
    next_task_info: Optional[Dict[str, Any]] = Field(default=None, description="下一步任务信息")
    is_completed: bool = Field(default=False, description="任务是否完成")
    task_source: Optional[str] = Field(default=None, description="任务来源（触发本任务的上一任务ID）")
    task_destinations: List[str] = Field(default_factory=list, description="任务去向（本任务完成后可能触发的所有任务ID列表）")
    task_type: TaskType = Field(default=TaskType.NORMAL, description="任务类型")

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

    def update_task(self, **kwargs) -> None:
        valid_fields = self.model_fields.keys()
        for key, value in kwargs.items():
            if key not in valid_fields:
                raise ValueError(f"属性 '{key}' 不是 Task 类的有效字段")
        
        for key, value in kwargs.items():
            setattr(self, key, value)

    def save(self) -> bool:
        """
        保存任务到数据库（新增或更新）
        
        数据库配置从 db_config.json 文件读取。
        
        :return: 保存成功返回True
        """
        from data_storage_services.sql_db_services.task_service import TaskService
        
        service = TaskService()
        try:
            if service.exists(self.task_id):
                service.update(self)
            else:
                service.create(self)
            return True
        finally:
            service.disconnect()

    def delete(self) -> int:
        """
        从数据库删除任务
        
        数据库配置从 db_config.json 文件读取。
        
        :return: 删除的记录数
        """
        from data_storage_services.sql_db_services.task_service import TaskService
        
        service = TaskService()
        try:
            return service.delete(self.task_id)
        finally:
            service.disconnect()

    @classmethod
    def get_by_id(cls, task_id: str) -> Optional['Task']:
        """
        按任务ID查询任务
        
        数据库配置从 db_config.json 文件读取。
        
        :param task_id: 任务ID
        :return: 任务对象，未找到返回None
        """
        from data_storage_services.sql_db_services.task_service import TaskService
        
        service = TaskService()
        try:
            return service.read(task_id)
        finally:
            service.disconnect()

    @classmethod
    def get_by_name(cls, task_name: str) -> List['Task']:
        """
        按任务名称查询任务
        
        数据库配置从 db_config.json 文件读取。
        
        :param task_name: 任务名称
        :return: 任务列表
        """
        from data_storage_services.sql_db_services.task_service import TaskService
        
        service = TaskService()
        try:
            return service.read_all(where={"task_name": task_name})
        finally:
            service.disconnect()

    @classmethod
    def query(cls, where: Dict[str, Any] = None, order_by: str = None, 
              limit: int = None) -> List['Task']:
        """
        按条件查询任务
        
        数据库配置从 db_config.json 文件读取。
        
        :param where: 查询条件，如 {"execute_role": "DEV", "priority": "high"}
        :param order_by: 排序字段
        :param limit: 返回数量限制
        :return: 任务列表
        """
        from data_storage_services.sql_db_services.task_service import TaskService
        
        service = TaskService()
        try:
            return service.read_all(where=where, order_by=order_by, limit=limit)
        finally:
            service.disconnect()

    @classmethod
    def get_all(cls, order_by: str = None, limit: int = None) -> List['Task']:
        """
        全量查询任务
        
        数据库配置从 db_config.json 文件读取。
        
        :param order_by: 排序字段
        :param limit: 返回数量限制
        :return: 任务列表
        """
        from data_storage_services.sql_db_services.task_service import TaskService
        
        service = TaskService()
        try:
            return service.read_all(order_by=order_by, limit=limit)
        finally:
            service.disconnect()

    @classmethod
    def exists(cls, task_id: str) -> bool:
        """
        检查任务是否存在
        
        数据库配置从 db_config.json 文件读取。
        
        :param task_id: 任务ID
        :return: 存在返回True
        """
        from data_storage_services.sql_db_services.task_service import TaskService
        
        service = TaskService()
        try:
            return service.exists(task_id)
        finally:
            service.disconnect()

    @classmethod
    def count(cls, where: Dict[str, Any] = None) -> int:
        """
        统计任务数量
        
        数据库配置从 db_config.json 文件读取。
        
        :param where: 查询条件
        :return: 任务数量
        """
        from data_storage_services.sql_db_services.task_service import TaskService
        
        service = TaskService()
        try:
            return service.count(where=where)
        finally:
            service.disconnect()


class StartTask(Task):
    """
    开始任务类
    
    代表任务流的起点任务，具有以下特点：
    - 不再有上一任务（task_source必须为None）
    - 是任务流的入口点
    - 可以触发后续任务
    
    示例用法：
        start_task = StartTask(
            task_id="START001",
            task_name="流程开始",
            expected_start_time=datetime.now(),
            expected_end_time=datetime.now(),
            content="流程开始节点",
            execute_role="SYSTEM",
            resource_consumption=0.0,
            priority="low",
            output_target_role="DEV",
            task_destinations=["T001", "T002"]
        )
    """
    
    @model_validator(mode='after')
    def validate_start_task(self) -> 'StartTask':
        if self.task_source is not None:
            raise ValueError("StartTask 不能有上一任务，task_source 必须为 None")
        
        self.task_type = TaskType.START
        
        return self


class EndTask(Task):
    """
    结束任务类
    
    代表任务流的正常终点任务，具有以下特点：
    - 不再有下一任务
    - task_destinations 必须为空列表
    - next_task_info 必须为 None
    - output_target_role 必须为空字符串
    - 标志任务流的正常结束
    
    示例用法：
        end_task = EndTask(
            task_id="END001",
            task_name="流程结束",
            expected_start_time=datetime.now(),
            expected_end_time=datetime.now(),
            content="流程结束节点",
            execute_role="SYSTEM",
            resource_consumption=0.0,
            priority="low",
            task_source="T003"
        )
    """
    
    @model_validator(mode='after')
    def validate_end_task(self) -> 'EndTask':
        if self.task_destinations:
            raise ValueError("EndTask 不能有下一任务，task_destinations 必须为空列表")
        
        if self.next_task_info is not None:
            raise ValueError("EndTask 不能有后续任务信息，next_task_info 必须为 None")
        
        if self.output_target_role != "":
            raise ValueError("EndTask 不能有输出目标角色，output_target_role 必须为空字符串")
        
        self.task_type = TaskType.END
        
        return self


class HaltTask(Task):
    """
    中断任务类
    
    代表任务流的异常中断点任务，具有以下特点：
    - 不再有下一任务
    - task_destinations 必须为空列表
    - next_task_info 必须为 None
    - output_target_role 必须为空字符串
    - 标志任务流的异常中断，通常用于错误处理或流程终止
    
    示例用法：
        halt_task = HaltTask(
            task_id="HALT001",
            task_name="流程中断",
            expected_start_time=datetime.now(),
            expected_end_time=datetime.now(),
            content="流程异常中断节点",
            execute_role="SYSTEM",
            resource_consumption=0.0,
            priority="high",
            task_source="T002"
        )
    """
    
    @model_validator(mode='after')
    def validate_halt_task(self) -> 'HaltTask':
        if self.task_destinations:
            raise ValueError("HaltTask 不能有下一任务，task_destinations 必须为空列表")
        
        if self.next_task_info is not None:
            raise ValueError("HaltTask 不能有后续任务信息，next_task_info 必须为 None")
        
        if self.output_target_role != "":
            raise ValueError("HaltTask 不能有输出目标角色，output_target_role 必须为空字符串")
        
        self.task_type = TaskType.HALT
        
        return self


Task.model_rebuild()
StartTask.model_rebuild()
EndTask.model_rebuild()
HaltTask.model_rebuild()