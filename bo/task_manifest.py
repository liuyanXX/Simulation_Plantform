"""任务清单模块

定义 TaskManifest 类，用于管理一组任务流组。
"""
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict, Any
import json
from datetime import datetime


class TaskManifest(BaseModel):
    """
    任务清单类
    
    表示一个任务清单，包含一组任务流组，用于整体管理和执行多个任务流。
    
    :param manifest_id: 清单唯一标识
    :param manifest_name: 清单名称（人类可读）
    :param flow_groups: 任务流组列表
    :param description: 清单描述
    :param created_at: 创建时间
    :param updated_at: 更新时间
    :param status: 清单状态（draft: 草稿, active: 激活, completed: 完成, archived: 归档）
    
    示例用法：
        manifest = TaskManifest(
            manifest_id="MANIFEST001",
            manifest_name="项目发布流程清单",
            flow_groups=[flow1, flow2, flow3],
            description="包含项目发布所需的所有流程"
        )
        
        # 获取清单摘要
        summary = manifest.get_manifest_summary()
        
        # 导出为JSON
        json_str = manifest.to_json()
    """
    manifest_id: str = Field(description="清单唯一标识")
    manifest_name: str = Field(description="清单名称（人类可读）")
    flow_groups: List['TaskFlowGroup'] = Field(default_factory=list, description="任务流组列表")
    description: Optional[str] = Field(default=None, description="清单描述")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    status: str = Field(default="draft", description="清单状态（draft/active/completed/archived）")
    
    @model_validator(mode='after')
    def validate_status(self) -> 'TaskManifest':
        """验证清单状态"""
        valid_statuses = ["draft", "active", "completed", "archived"]
        if self.status not in valid_statuses:
            raise ValueError(f"状态必须是 {valid_statuses} 之一")
        return self
    
    def add_flow_group(self, flow_group: 'TaskFlowGroup') -> None:
        """
        添加任务流组到清单
        
        :param flow_group: 要添加的任务流组对象
        :raises ValueError: 如果任务流组ID已存在
        """
        # 检查任务流组ID是否已存在
        if any(f.flow_id == flow_group.flow_id for f in self.flow_groups):
            raise ValueError(f"任务流组ID {flow_group.flow_id} 已存在于清单中")
        
        self.flow_groups.append(flow_group)
        self.updated_at = datetime.now()
    
    def remove_flow_group(self, flow_id: str) -> None:
        """
        从清单中移除任务流组
        
        :param flow_id: 要移除的任务流组ID
        :raises ValueError: 如果任务流组不存在
        """
        flow_index = None
        for i, flow in enumerate(self.flow_groups):
            if flow.flow_id == flow_id:
                flow_index = i
                break
        
        if flow_index is None:
            raise ValueError(f"未找到任务流组: {flow_id}")
        
        del self.flow_groups[flow_index]
        self.updated_at = datetime.now()
    
    def get_flow_group(self, flow_id: str) -> Optional['TaskFlowGroup']:
        """
        获取指定的任务流组
        
        :param flow_id: 任务流组ID
        :return: 任务流组对象，如果未找到返回None
        """
        for flow in self.flow_groups:
            if flow.flow_id == flow_id:
                return flow
        return None
    
    def get_total_task_count(self) -> int:
        """获取清单中所有任务的总数"""
        return sum(flow.get_flow_length() for flow in self.flow_groups)
    
    def get_flow_group_summaries(self) -> List[Dict[str, Any]]:
        """获取所有任务流组的摘要信息"""
        return [flow.get_flow_summary() for flow in self.flow_groups]
    
    def get_manifest_summary(self) -> Dict[str, Any]:
        """获取清单摘要信息"""
        summaries = self.get_flow_group_summaries()
        
        return {
            "manifest_id": self.manifest_id,
            "manifest_name": self.manifest_name,
            "description": self.description,
            "flow_group_count": len(self.flow_groups),
            "total_task_count": self.get_total_task_count(),
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "flow_groups": summaries
        }
    
    def activate(self) -> None:
        """激活清单"""
        self.status = "active"
        self.updated_at = datetime.now()
    
    def complete(self) -> None:
        """标记清单为完成"""
        self.status = "completed"
        self.updated_at = datetime.now()
    
    def archive(self) -> None:
        """归档清单"""
        self.status = "archived"
        self.updated_at = datetime.now()
    
    def to_json(self) -> str:
        """导出清单为JSON格式"""
        return json.dumps(self.model_dump(mode='json'), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TaskManifest':
        """
        从JSON字符串加载清单
        
        :param json_str: JSON格式的字符串
        :return: TaskManifest 对象
        """
        data = json.loads(json_str)
        
        # 先处理 flow_groups 中的每个任务流组
        if 'flow_groups' in data:
            processed_flow_groups = []
            for flow_group_data in data['flow_groups']:
                # 使用 TaskFlowGroup 的 from_json 方法处理
                flow_group_json = json.dumps(flow_group_data)
                flow_group = TaskFlowGroup.from_json(flow_group_json)
                processed_flow_groups.append(flow_group)
            data['flow_groups'] = processed_flow_groups
        
        return cls(**data)
    
    def save_to_file(self, file_path: str) -> None:
        """
        保存清单到文件
        
        :param file_path: 文件路径
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
    
    @classmethod
    def load_from_file(cls, file_path: str) -> 'TaskManifest':
        """
        从文件加载清单
        
        :param file_path: 文件路径
        :return: TaskManifest 对象
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            json_str = f.read()
        return cls.from_json(json_str)
    
    def __str__(self) -> str:
        """返回清单的字符串表示"""
        return f"TaskManifest(manifest_id={self.manifest_id}, manifest_name={self.manifest_name}, flow_groups={len(self.flow_groups)}个)"


# 延迟导入避免循环依赖，然后更新类型提示引用
from .task_flow_group import TaskFlowGroup
TaskManifest.update_forward_refs()