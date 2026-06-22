"""任务图谱服务类

提供任务图谱对象的数据库CRUD操作服务。
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
from bo.tasks_graph import TasksGraph


class TasksGraphService(SQLDatabaseService[TasksGraph]):
    """
    任务图谱服务类
    
    提供任务图谱对象的数据库CRUD操作服务。
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
        return "tasks_graphs"
    
    def _get_id_field(self) -> str:
        return "graph_id"
    
    def _get_id_value(self, obj: TasksGraph) -> str:
        return obj.graph_id
    
    def _to_db_dict(self, obj: TasksGraph) -> Dict[str, Any]:
        """将任务图谱对象转换为数据库字典"""
        return {
            "graph_id": obj.graph_id,
            "graph_name": obj.graph_name,
            "description": obj.description,
            "manifest_id": getattr(obj, '_manifest_id', None),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    def _from_db_dict(self, data: Dict[str, Any]) -> TasksGraph:
        """将数据库字典转换为任务图谱对象"""
        # 任务列表需要单独加载
        graph = TasksGraph(
            graph_id=data["graph_id"],
            graph_name=data["graph_name"],
            description=data.get("description"),
            tasks=[]
        )
        setattr(graph, '_manifest_id', data.get("manifest_id"))
        return graph
    
    def read_with_tasks(self, graph_id: str) -> Optional[TasksGraph]:
        """
        读取任务图谱及其所有任务
        
        :param graph_id: 任务图谱ID
        :return: 任务图谱对象（包含任务列表）
        """
        graph = self.read(graph_id)
        if graph:
            tasks = self.task_service.get_by_graph(graph_id)
            graph.tasks = tasks
        return graph
    
    def create_with_tasks(self, graph: TasksGraph, manifest_id: str = None) -> bool:
        """
        创建任务图谱及其所有任务
        
        :param graph: 任务图谱对象
        :param manifest_id: 任务清单ID
        :return: 成功返回True
        """
        try:
            # 保存任务图谱
            setattr(graph, '_manifest_id', manifest_id)
            self.create(graph)
            
            # 保存所有任务
            for task in graph.tasks:
                setattr(task, '_graph_id', graph.graph_id)
                if manifest_id:
                    setattr(task, '_manifest_id', manifest_id)
                self.task_service.create(task)
            
            return True
        except Exception as e:
            self.logger.error(f"创建任务图谱失败: {e}")
            raise
    
    def delete_with_tasks(self, graph_id: str) -> int:
        """
        删除任务图谱及其所有任务
        
        :param graph_id: 任务图谱ID
        :return: 删除的任务数量
        """
        try:
            # 删除所有关联任务
            tasks = self.task_service.get_by_graph(graph_id)
            task_count = 0
            for task in tasks:
                self.task_service.delete(task.task_id)
                task_count += 1
            
            # 删除任务图谱
            self.delete(graph_id)
            
            return task_count
        except Exception as e:
            self.logger.error(f"删除任务图谱失败: {e}")
            raise
    
    def get_by_manifest(self, manifest_id: str) -> List[TasksGraph]:
        """
        按任务清单查询任务图谱
        
        :param manifest_id: 任务清单ID
        :return: 任务图谱列表
        """
        return self.read_all(where={"manifest_id": manifest_id})


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试任务图谱服务
    service = TasksGraphService()
    
    # 创建测试任务图谱
    from bo.task import StartTask, EndTask, Task, Priority
    from datetime import timedelta
    
    now = datetime.now()
    graph = TasksGraph(
        graph_id="GRAPH001",
        graph_name="测试图谱",
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
                task_destinations=["TASK001", "TASK002"]
            ),
            Task(
                task_id="TASK001",
                task_name="开发任务1",
                expected_start_time=now,
                expected_end_time=now + timedelta(hours=2),
                content="开发功能1",
                execute_role="DEV",
                resource_consumption=2.0,
                priority=Priority.HIGH,
                output_target_role="TEST",
                task_source="START001",
                task_destinations=["END001"]
            ),
            Task(
                task_id="TASK002",
                task_name="开发任务2",
                expected_start_time=now,
                expected_end_time=now + timedelta(hours=2),
                content="开发功能2",
                execute_role="DEV",
                resource_consumption=2.0,
                priority=Priority.MEDIUM,
                output_target_role="TEST",
                task_source="START001",
                task_destinations=["END001"]
            ),
            EndTask(
                task_id="END001",
                task_name="结束",
                expected_start_time=now + timedelta(hours=2),
                expected_end_time=now + timedelta(hours=2),
                content="流程结束",
                execute_role="SYSTEM",
                resource_consumption=0.0,
                priority=Priority.LOW,
                task_source="TASK001"
            )
        ]
    )
    
    # 保存
    service.create_with_tasks(graph)
    print(f"创建任务图谱: {graph.graph_id}")
    
    # 读取
    loaded = service.read_with_tasks("GRAPH001")
    print(f"读取任务图谱: {loaded}")
    
    # 删除
    service.delete_with_tasks("GRAPH001")
    print("删除任务图谱成功")
    
    service.disconnect()
