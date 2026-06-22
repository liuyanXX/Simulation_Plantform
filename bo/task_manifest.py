"""任务清单模块

定义 TaskManifest 类，用于管理任务清单对象。
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
import json

from pydantic import BaseModel, Field, model_validator


class ManifestStatus(str, Enum):
    """任务清单状态枚举"""
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TaskManifest(BaseModel):
    """
    任务清单类
    
    表示一个完整的任务清单，包含多个任务流组。
    
    :param manifest_id: 任务清单唯一标识
    :param manifest_name: 任务清单名称
    :param flow_groups: 任务流组列表
    :param description: 任务清单描述
    :param status: 任务清单状态
    :param created_at: 创建时间
    :param updated_at: 更新时间
    """
    manifest_id: str = Field(description="任务清单唯一标识")
    manifest_name: str = Field(description="任务清单名称")
    flow_groups: List['TaskFlowGroup'] = Field(default_factory=list, description="任务流组列表")
    description: Optional[str] = Field(default=None, description="任务清单描述")
    status: ManifestStatus = Field(default=ManifestStatus.DRAFT, description="任务清单状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    _solution_id: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_flow_groups(self) -> 'TaskManifest':
        """验证任务流组的唯一性"""
        flow_ids = set()
        for flow_group in self.flow_groups:
            if flow_group.flow_id in flow_ids:
                raise ValueError(f"任务流组ID重复: {flow_group.flow_id}")
            flow_ids.add(flow_group.flow_id)
        return self
    
    def add_flow_group(self, flow_group: 'TaskFlowGroup') -> None:
        """
        添加任务流组到清单
        
        :param flow_group: 任务流组对象
        :raises ValueError: 如果任务流组ID重复
        """
        if flow_group.flow_id in [fg.flow_id for fg in self.flow_groups]:
            raise ValueError(f"任务流组ID已存在: {flow_group.flow_id}")
        
        self.flow_groups.append(flow_group)
        self.updated_at = datetime.now()
    
    def remove_flow_group(self, flow_id: str) -> None:
        """
        从清单中移除任务流组
        
        :param flow_id: 任务流组ID
        :raises ValueError: 如果任务流组不存在
        """
        for i, fg in enumerate(self.flow_groups):
            if fg.flow_id == flow_id:
                del self.flow_groups[i]
                self.updated_at = datetime.now()
                return
        
        raise ValueError(f"未找到任务流组: {flow_id}")
    
    def get_flow_group(self, flow_id: str) -> Optional['TaskFlowGroup']:
        """
        获取指定任务流组
        
        :param flow_id: 任务流组ID
        :return: 任务流组对象，如果未找到返回None
        """
        for fg in self.flow_groups:
            if fg.flow_id == flow_id:
                return fg
        return None
    
    def get_all_tasks(self) -> List['Task']:
        """获取清单中所有任务"""
        all_tasks = []
        for fg in self.flow_groups:
            all_tasks.extend(fg.tasks)
        return all_tasks
    
    def get_total_task_count(self) -> int:
        """获取总任务数量"""
        return sum(len(fg.tasks) for fg in self.flow_groups)
    
    def get_flow_group_count(self) -> int:
        """获取任务流组数量"""
        return len(self.flow_groups)
    
    def update_status(self, new_status: ManifestStatus) -> None:
        """
        更新任务清单状态
        
        :param new_status: 新状态
        """
        self.status = new_status
        self.updated_at = datetime.now()
    
    def to_json(self) -> str:
        """导出任务清单为JSON格式"""
        return json.dumps(self.model_dump(mode='json'), ensure_ascii=False, indent=2)
    
    def get_manifest_summary(self) -> Dict[str, Any]:
        """获取任务清单摘要信息"""
        return {
            "manifest_id": self.manifest_id,
            "manifest_name": self.manifest_name,
            "description": self.description,
            "status": self.status.value,
            "flow_group_count": self.get_flow_group_count(),
            "total_task_count": self.get_total_task_count(),
            "flow_group_ids": [fg.flow_id for fg in self.flow_groups],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    def save(self) -> bool:
        """
        保存任务清单到数据库（新增或更新）
        
        数据库配置从 db_config.json 文件读取。
        
        :return: 保存成功返回True
        """
        from data_storage_services.sql_db_services.task_manifest_service import TaskManifestService
        
        service = TaskManifestService()
        try:
            if service.exists(self.manifest_id):
                service.update(self)
            else:
                service.create_with_flow_groups(self, solution_id=self._solution_id)
            return True
        finally:
            service.disconnect()

    def delete(self) -> int:
        """
        从数据库删除任务清单及其所有任务流组和任务
        
        数据库配置从 db_config.json 文件读取。
        
        :return: 删除的任务流组数量
        """
        from data_storage_services.sql_db_services.task_manifest_service import TaskManifestService
        
        service = TaskManifestService()
        try:
            return service.delete_with_flow_groups(self.manifest_id)
        finally:
            service.disconnect()

    @classmethod
    def get_by_id(cls, manifest_id: str) -> Optional['TaskManifest']:
        """
        按任务清单ID查询任务清单（包含任务流组列表）
        
        数据库配置从 db_config.json 文件读取。
        
        :param manifest_id: 任务清单ID
        :return: 任务清单对象，未找到返回None
        """
        from data_storage_services.sql_db_services.task_manifest_service import TaskManifestService
        
        service = TaskManifestService()
        try:
            return service.read_with_flow_groups(manifest_id)
        finally:
            service.disconnect()

    @classmethod
    def query(cls, where: Dict[str, Any] = None, order_by: str = None, 
              limit: int = None) -> List['TaskManifest']:
        """
        按条件查询任务清单
        
        数据库配置从 db_config.json 文件读取。
        
        :param where: 查询条件，如 {"status": "active"}
        :param order_by: 排序字段
        :param limit: 返回数量限制
        :return: 任务清单列表
        """
        from data_storage_services.sql_db_services.task_manifest_service import TaskManifestService
        
        service = TaskManifestService()
        try:
            return service.read_all(where=where, order_by=order_by, limit=limit)
        finally:
            service.disconnect()

    @classmethod
    def get_all(cls, order_by: str = None, limit: int = None) -> List['TaskManifest']:
        """
        全量查询任务清单
        
        数据库配置从 db_config.json 文件读取。
        
        :param order_by: 排序字段
        :param limit: 返回数量限制
        :return: 任务清单列表
        """
        from data_storage_services.sql_db_services.task_manifest_service import TaskManifestService
        
        service = TaskManifestService()
        try:
            return service.read_all(order_by=order_by, limit=limit)
        finally:
            service.disconnect()

    @classmethod
    def exists(cls, manifest_id: str) -> bool:
        """
        检查任务清单是否存在
        
        数据库配置从 db_config.json 文件读取。
        
        :param manifest_id: 任务清单ID
        :return: 存在返回True
        """
        from data_storage_services.sql_db_services.task_manifest_service import TaskManifestService
        
        service = TaskManifestService()
        try:
            return service.exists(manifest_id)
        finally:
            service.disconnect()

    @classmethod
    def count(cls, where: Dict[str, Any] = None) -> int:
        """
        统计任务清单数量
        
        数据库配置从 db_config.json 文件读取。
        
        :param where: 查询条件
        :return: 任务清单数量
        """
        from data_storage_services.sql_db_services.task_manifest_service import TaskManifestService
        
        service = TaskManifestService()
        try:
            return service.count(where=where)
        finally:
            service.disconnect()

    @classmethod
    def from_json(cls, json_str: str) -> 'TaskManifest':
        """
        从JSON字符串加载任务清单
        
        :param json_str: JSON格式的字符串
        :return: TaskManifest 对象
        """
        from .task_flow_group import TaskFlowGroup
        
        data = json.loads(json_str)
        
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
        
        if 'flow_groups' in data:
            data['flow_groups'] = [TaskFlowGroup.from_json(json.dumps(fg)) for fg in data['flow_groups']]
        
        return cls(**data)


from .task_flow_group import TaskFlowGroup
from .task import Task
TaskManifest.update_forward_refs()