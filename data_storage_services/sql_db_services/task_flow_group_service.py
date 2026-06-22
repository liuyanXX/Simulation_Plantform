"""任务流组服务类

提供任务流组对象的数据库CRUD操作服务。
"""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from .base_service import SQLDatabaseService
from .task_service import TaskService
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from bo.task_flow_group import TaskFlowGroup


class TaskFlowGroupService(SQLDatabaseService[TaskFlowGroup]):
    """
    任务流组服务类
    
    提供任务流组对象的数据库CRUD操作服务。
    """
    
    def __init__(self, db_type: str = "sqlite", db_config: Dict[str, Any] = None):
        super().__init__(db_type, db_config)
        self._task_service = None
    
    @property
    def task_service(self) -> TaskService:
        """获取任务服务"""
        if self._task_service is None:
            self._task_service = TaskService(db_type=self.db_type, db_config=self.db_config)
        return self._task_service
    
    def _get_table_name(self) -> str:
        return "task_flow_groups"
    
    def _get_id_field(self) -> str:
        return "flow_id"
    
    def _get_id_value(self, obj: TaskFlowGroup) -> str:
        return obj.flow_id
    
    def _to_db_dict(self, obj: TaskFlowGroup) -> Dict[str, Any]:
        """将任务流组对象转换为数据库字典"""
        return {
            "flow_id": obj.flow_id,
            "flow_name": obj.flow_name,
            "description": obj.description,
            "manifest_id": getattr(obj, '_manifest_id', None),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    def _from_db_dict(self, data: Dict[str, Any]) -> TaskFlowGroup:
        """将数据库字典转换为任务流组对象"""
        # 任务列表需要单独加载
        flow_group = TaskFlowGroup(
            flow_id=data["flow_id"],
            flow_name=data["flow_name"],
            description=data.get("description"),
            tasks=[]
        )
        # 标记manifest_id
        setattr(flow_group, '_manifest_id', data.get("manifest_id"))
        return flow_group
    
    def read_with_tasks(self, flow_id: str) -> Optional[TaskFlowGroup]:
        """
        读取任务流组及其所有任务
        
        :param flow_id: 任务流组ID
        :return: 任务流组对象（包含任务列表）
        """
        flow_group = self.read(flow_id)
        if flow_group:
            tasks = self.task_service.get_by_flow_group(flow_id)
            flow_group.tasks = tasks
        return flow_group
    
    def create_with_tasks(self, flow_group: TaskFlowGroup, manifest_id: str = None) -> bool:
        """
        创建任务流组及其所有任务
        
        :param flow_group: 任务流组对象
        :param manifest_id: 任务清单ID
        :return: 成功返回True
        """
        try:
            # 保存任务流组
            setattr(flow_group, '_manifest_id', manifest_id)
            self.create(flow_group)
            
            # 保存所有任务
            for task in flow_group.tasks:
                setattr(task, '_flow_group_id', flow_group.flow_id)
                if manifest_id:
                    setattr(task, '_manifest_id', manifest_id)
                self.task_service.create(task)
            
            return True
        except Exception as e:
            self.logger.error(f"创建任务流组失败: {e}")
            raise
    
    def delete_with_tasks(self, flow_id: str) -> int:
        """
        删除任务流组及其所有任务
        
        :param flow_id: 任务流组ID
        :return: 删除的任务数量
        """
        try:
            # 删除所有关联任务
            tasks = self.task_service.get_by_flow_group(flow_id)
            task_count = 0
            for task in tasks:
                self.task_service.delete(task.task_id)
                task_count += 1
            
            # 删除任务流组
            self.delete(flow_id)
            
            return task_count
        except Exception as e:
            self.logger.error(f"删除任务流组失败: {e}")
            raise
    
    def get_by_manifest(self, manifest_id: str) -> List[TaskFlowGroup]:
        """
        按任务清单查询任务流组
        
        :param manifest_id: 任务清单ID
        :return: 任务流组列表
        """
        return self.read_all(where={"manifest_id": manifest_id})


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试任务流组服务
    service = TaskFlowGroupService()
    
    # 创建测试任务流组
    from bo.task import StartTask, EndTask, Task, Priority
    from datetime import timedelta
    
    now = datetime.now()
    flow_group = TaskFlowGroup(
        flow_id="FLOW001",
        flow_name="测试流程",
        tasks=[
            StartTask(
                task_id="START001",
                task_name="开始",
                expected_start_time=now,
                expected_end_time=now,
                content="流程开始",
                execute_role="SYSTEM",
                resource_consumption=0.0,
                priority=Priority.LOW,
                output_target_role="DEV",
                task_destinations=["TASK001"]
            ),
            Task(
                task_id="TASK001",
                task_name="开发任务",
                expected_start_time=now,
                expected_end_time=now + timedelta(hours=4),
                content="开发功能",
                execute_role="DEV",
                resource_consumption=4.0,
                priority=Priority.HIGH,
                output_target_role="TEST",
                task_source="START001",
                task_destinations=["END001"]
            ),
            EndTask(
                task_id="END001",
                task_name="结束",
                expected_start_time=now + timedelta(hours=4),
                expected_end_time=now + timedelta(hours=4),
                content="流程结束",
                execute_role="SYSTEM",
                resource_consumption=0.0,
                priority=Priority.LOW,
                task_source="TASK001"
            )
        ]
    )
    
    # 保存
    service.create_with_tasks(flow_group)
    print(f"创建任务流组: {flow_group.flow_id}")
    
    # 读取
    loaded = service.read_with_tasks("FLOW001")
    print(f"读取任务流组: {loaded}")
    
    # 删除
    service.delete_with_tasks("FLOW001")
    print("删除任务流组成功")
    
    service.disconnect()
