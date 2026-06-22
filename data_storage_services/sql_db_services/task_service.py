"""任务服务类

提供任务对象的数据库CRUD操作服务。
"""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from .base_service import SQLDatabaseService
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from bo.task import Task, StartTask, EndTask, HaltTask, Priority, TaskType


class TaskService(SQLDatabaseService[Task]):
    """
    任务服务类
    
    提供任务对象的数据库CRUD操作服务。
    """
    
    def _get_table_name(self) -> str:
        return "tasks"
    
    def _get_id_field(self) -> str:
        return "task_id"
    
    def _get_id_value(self, obj: Task) -> str:
        return obj.task_id
    
    def _to_db_dict(self, obj: Task) -> Dict[str, Any]:
        """将任务对象转换为数据库字典"""
        return {
            "task_id": obj.task_id,
            "task_name": obj.task_name,
            "task_type": obj.task_type.value if hasattr(obj, 'task_type') else TaskType.NORMAL.value,
            "expected_start_time": obj.expected_start_time.isoformat() if isinstance(obj.expected_start_time, datetime) else obj.expected_start_time,
            "expected_end_time": obj.expected_end_time.isoformat() if isinstance(obj.expected_end_time, datetime) else obj.expected_end_time,
            "scheduled_start_time": obj.scheduled_start_time.isoformat() if obj.scheduled_start_time else None,
            "scheduled_end_time": obj.scheduled_end_time.isoformat() if obj.scheduled_end_time else None,
            "actual_start_time": obj.actual_start_time.isoformat() if obj.actual_start_time else None,
            "actual_end_time": obj.actual_end_time.isoformat() if obj.actual_end_time else None,
            "content": obj.content,
            "execute_role": obj.execute_role,
            "resource_consumption": obj.resource_consumption,
            "priority": obj.priority.value if isinstance(obj.priority, Priority) else obj.priority,
            "output_target_role": obj.output_target_role or "",
            "next_task_info": json.dumps(obj.next_task_info, ensure_ascii=False) if obj.next_task_info else None,
            "is_completed": 1 if obj.is_completed else 0,
            "task_source": obj.task_source,
            "task_destinations": json.dumps(obj.task_destinations, ensure_ascii=False) if obj.task_destinations else None,
            "flow_group_id": getattr(obj, '_flow_group_id', None),
            "graph_id": getattr(obj, '_graph_id', None),
            "manifest_id": getattr(obj, '_manifest_id', None)
        }
    
    def _from_db_dict(self, data: Dict[str, Any]) -> Task:
        """将数据库字典转换为任务对象"""
        def parse_json(value, default=None):
            if value is None:
                return default or []
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except:
                    return value
            return value
        
        def parse_datetime(value):
            if value is None:
                return None
            if isinstance(value, str):
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            return value
        
        task_type = TaskType(data.get("task_type", "normal"))
        
        # 根据任务类型创建对应的任务对象
        common_params = {
            "task_id": data["task_id"],
            "task_name": data["task_name"],
            "expected_start_time": parse_datetime(data["expected_start_time"]),
            "expected_end_time": parse_datetime(data["expected_end_time"]),
            "scheduled_start_time": parse_datetime(data.get("scheduled_start_time")),
            "scheduled_end_time": parse_datetime(data.get("scheduled_end_time")),
            "actual_start_time": parse_datetime(data.get("actual_start_time")),
            "actual_end_time": parse_datetime(data.get("actual_end_time")),
            "content": data["content"],
            "execute_role": data["execute_role"],
            "resource_consumption": data["resource_consumption"],
            "priority": Priority(data["priority"]) if data.get("priority") else Priority.MEDIUM,
            "output_target_role": data.get("output_target_role", ""),
            "next_task_info": parse_json(data.get("next_task_info")),
            "is_completed": bool(data.get("is_completed", 0)),
            "task_source": data.get("task_source"),
            "task_destinations": parse_json(data.get("task_destinations"), [])
        }
        
        if task_type == TaskType.START:
            return StartTask(**common_params)
        elif task_type == TaskType.END:
            return EndTask(**common_params)
        elif task_type == TaskType.HALT:
            return HaltTask(**common_params)
        else:
            return Task(**common_params)
    
    def get_by_flow_group(self, flow_group_id: str) -> List[Task]:
        """
        按任务流组查询任务
        
        :param flow_group_id: 任务流组ID
        :return: 任务列表
        """
        return self.read_all(where={"flow_group_id": flow_group_id})
    
    def get_by_graph(self, graph_id: str) -> List[Task]:
        """
        按任务图谱查询任务
        
        :param graph_id: 任务图谱ID
        :return: 任务列表
        """
        return self.read_all(where={"graph_id": graph_id})
    
    def get_by_manifest(self, manifest_id: str) -> List[Task]:
        """
        按任务清单查询任务
        
        :param manifest_id: 任务清单ID
        :return: 任务列表
        """
        return self.read_all(where={"manifest_id": manifest_id})
    
    def get_by_execute_role(self, role: str) -> List[Task]:
        """
        按执行角色查询任务
        
        :param role: 执行角色
        :return: 任务列表
        """
        return self.read_all(where={"execute_role": role})
    
    def get_pending_tasks(self) -> List[Task]:
        """
        获取未完成的任务
        
        :return: 未完成任务列表
        """
        return self.read_all(where={"is_completed": 0})
    
    def get_completed_tasks(self) -> List[Task]:
        """
        获取已完成的任务
        
        :return: 已完成任务列表
        """
        return self.read_all(where={"is_completed": 1})


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试任务服务
    service = TaskService()
    
    # 创建测试任务
    task = Task(
        task_id="TASK001",
        task_name="测试任务",
        expected_start_time=datetime.now(),
        expected_end_time=datetime.now(),
        content="这是一个测试任务",
        execute_role="DEV",
        resource_consumption=2.0,
        priority=Priority.HIGH,
        output_target_role="TEST"
    )
    
    # 保存
    service.create(task)
    print(f"创建任务: {task.task_id}")
    
    # 读取
    loaded = service.read("TASK001")
    print(f"读取任务: {loaded}")
    
    # 删除
    service.delete("TASK001")
    print("删除任务成功")
    
    service.disconnect()
