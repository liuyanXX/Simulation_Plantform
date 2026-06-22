"""任务清单服务类

提供任务清单对象的数据库CRUD操作服务。
"""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from .base_service import SQLDatabaseService
from .task_flow_group_service import TaskFlowGroupService
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from bo.task_manifest import TaskManifest


class TaskManifestService(SQLDatabaseService[TaskManifest]):
    """
    任务清单服务类
    
    提供任务清单对象的数据库CRUD操作服务。
    """
    
    def __init__(self, db_type: str = "sqlite", db_config: Dict[str, Any] = None):
        super().__init__(db_type, db_config)
        self._flow_group_service = None
    
    @property
    def flow_group_service(self) -> TaskFlowGroupService:
        """获取任务流组服务"""
        if self._flow_group_service is None:
            self._flow_group_service = TaskFlowGroupService(db_type=self.db_type, db_config=self.db_config)
        return self._flow_group_service
    
    def _get_table_name(self) -> str:
        return "task_manifests"
    
    def _get_id_field(self) -> str:
        return "manifest_id"
    
    def _get_id_value(self, obj: TaskManifest) -> str:
        return obj.manifest_id
    
    def _to_db_dict(self, obj: TaskManifest) -> Dict[str, Any]:
        """将任务清单对象转换为数据库字典"""
        return {
            "manifest_id": obj.manifest_id,
            "manifest_name": obj.manifest_name,
            "description": obj.description,
            "solution_id": getattr(obj, '_solution_id', None),
            "status": obj.status,
            "created_at": obj.created_at.isoformat() if isinstance(obj.created_at, datetime) else obj.created_at,
            "updated_at": obj.updated_at.isoformat() if isinstance(obj.updated_at, datetime) else obj.updated_at
        }
    
    def _from_db_dict(self, data: Dict[str, Any]) -> TaskManifest:
        """将数据库字典转换为任务清单对象"""
        def parse_datetime(value):
            if value is None:
                return None
            if isinstance(value, str):
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            return value
        
        # 任务流组列表需要单独加载
        manifest = TaskManifest(
            manifest_id=data["manifest_id"],
            manifest_name=data["manifest_name"],
            description=data.get("description"),
            flow_groups=[],
            created_at=parse_datetime(data.get("created_at")) or datetime.now(),
            updated_at=parse_datetime(data.get("updated_at")) or datetime.now(),
            status=data.get("status", "draft")
        )
        setattr(manifest, '_solution_id', data.get("solution_id"))
        return manifest
    
    def read_with_flow_groups(self, manifest_id: str) -> Optional[TaskManifest]:
        """
        读取任务清单及其所有任务流组
        
        :param manifest_id: 任务清单ID
        :return: 任务清单对象（包含任务流组列表）
        """
        manifest = self.read(manifest_id)
        if manifest:
            flow_groups = self.flow_group_service.get_by_manifest(manifest_id)
            manifest.flow_groups = flow_groups
        return manifest
    
    def create_with_flow_groups(self, manifest: TaskManifest, solution_id: str = None) -> bool:
        """
        创建任务清单及其所有任务流组
        
        :param manifest: 任务清单对象
        :param solution_id: 方案ID
        :return: 成功返回True
        """
        try:
            # 保存任务清单
            setattr(manifest, '_solution_id', solution_id)
            self.create(manifest)
            
            # 保存所有任务流组
            for flow_group in manifest.flow_groups:
                self.flow_group_service.create_with_tasks(flow_group, manifest_id=manifest.manifest_id)
            
            return True
        except Exception as e:
            self.logger.error(f"创建任务清单失败: {e}")
            raise
    
    def delete_with_flow_groups(self, manifest_id: str) -> int:
        """
        删除任务清单及其所有任务流组
        
        :param manifest_id: 任务清单ID
        :return: 删除的任务流组数量
        """
        try:
            # 删除所有关联任务流组
            flow_groups = self.flow_group_service.get_by_manifest(manifest_id)
            flow_count = 0
            for flow_group in flow_groups:
                self.flow_group_service.delete_with_tasks(flow_group.flow_id)
                flow_count += 1
            
            # 删除任务清单
            self.delete(manifest_id)
            
            return flow_count
        except Exception as e:
            self.logger.error(f"删除任务清单失败: {e}")
            raise
    
    def get_by_solution(self, solution_id: str) -> List[TaskManifest]:
        """
        按方案查询任务清单
        
        :param solution_id: 方案ID
        :return: 任务清单列表
        """
        return self.read_all(where={"solution_id": solution_id})
    
    def get_by_status(self, status: str) -> List[TaskManifest]:
        """
        按状态查询任务清单
        
        :param status: 状态
        :return: 任务清单列表
        """
        return self.read_all(where={"status": status})


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试任务清单服务
    service = TaskManifestService()
    
    # 创建测试任务清单
    from bo.task_flow_group import TaskFlowGroup
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
    
    manifest = TaskManifest(
        manifest_id="MANIFEST001",
        manifest_name="测试清单",
        flow_groups=[flow_group]
    )
    
    # 保存
    service.create_with_flow_groups(manifest)
    print(f"创建任务清单: {manifest.manifest_id}")
    
    # 读取
    loaded = service.read_with_flow_groups("MANIFEST001")
    print(f"读取任务清单: {loaded}")
    
    # 删除
    service.delete_with_flow_groups("MANIFEST001")
    print("删除任务清单成功")
    
    service.disconnect()
