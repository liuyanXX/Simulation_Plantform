"""任务分派引擎模块

该模块负责将任务清单分派到仿真流程引擎的启动员工。
支持根据任务清单ID查找、分派任务流组等功能。
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import logging
import sys
import os

from bo.task_manifest import TaskManifest
from bo.task_flow_group import TaskFlowGroup
from bo.task import StartTask
from simulation_process_engine import SimulationProcessEngine


class TaskDispatchEngine:
    """
    任务分派引擎
    
    负责将任务清单分派到仿真流程引擎的启动员工（__Start__AI_Worker）。
    主要功能：
    - 获取任务清单对象
    - 对任务清单对象进行规范性检查
    - 将任务清单拆解为任务流组
    - 将任务流组的StartTask插入到启动员工的任务清单中
    
    :param process_engine: 仿真流程引擎实例
    :param manifest_dir: 任务清单文件目录，默认为当前目录的 manifests 子目录
    :param logger_name: 日志记录器名称
    """
    
    def __init__(
        self,
        process_engine: Optional[SimulationProcessEngine] = None,
        manifest_dir: Optional[str] = None
    ):
        self._process_engine = process_engine
        self._manifest_dir = manifest_dir or self._get_default_manifest_dir()
        self._logger = self._setup_logging('TaskDispatchEngine')
        self._manifest_cache: Dict[str, TaskManifest] = {}
        self._dispatched_manifests: Dict[str, List[str]] = {}
        
        self._ensure_manifest_dir()
    
    def _get_default_manifest_dir(self) -> str:
        """获取默认的任务清单目录"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, 'manifests')
    
    def _ensure_manifest_dir(self) -> None:
        """确保任务清单目录存在"""
        if not os.path.exists(self._manifest_dir):
            os.makedirs(self._manifest_dir)
            self._logger.info(f"创建任务清单目录: {self._manifest_dir}")
    
    def _setup_logging(self, logger_name: str) -> logging.Logger:
        """配置日志系统"""
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        if logger.handlers:
            return logger
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        file_handler = logging.FileHandler(
            'logs/task_dispatch_engine.log', mode='w', encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(logging.INFO)
        
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
        
        return logger
    
    def set_process_engine(self, process_engine: SimulationProcessEngine) -> None:
        """
        设置仿真流程引擎
        
        :param process_engine: 仿真流程引擎实例
        """
        self._process_engine = process_engine
        self._logger.info("仿真流程引擎已设置")
    
    def _get_manifest_file_path(self, manifest_id: str) -> str:
        """
        根据任务清单ID获取文件路径
        
        :param manifest_id: 任务清单ID
        :return: 任务清单文件路径
        """
        return os.path.join(self._manifest_dir, f"{manifest_id}.json")
    
    def load_manifest(self, manifest_id: str) -> Optional[TaskManifest]:
        """
        根据任务清单ID加载任务清单
        
        :param manifest_id: 任务清单ID
        :return: 任务清单对象，如果不存在返回None
        """
        if manifest_id in self._manifest_cache:
            self._logger.info(f"从缓存加载任务清单: {manifest_id}")
            return self._manifest_cache[manifest_id]
        
        file_path = self._get_manifest_file_path(manifest_id)
        
        if not os.path.exists(file_path):
            self._logger.warning(f"任务清单文件不存在: {file_path}")
            return None
        
        self._logger.info(f"从文件加载任务清单: {file_path}")
        
        manifest = TaskManifest.load_from_file(file_path)
        self._manifest_cache[manifest_id] = manifest
        
        return manifest
    
    def validate_manifest(self, manifest: TaskManifest) -> List[str]:
        """
        对任务清单进行规范性检查
        
        检查项包括：
        - 清单ID和名称是否有效
        - 任务流组列表是否为空
        - 每个任务流组是否包含必要的任务
        - 任务的执行角色是否有效
        - 是否有起始任务（StartTask）
        - 是否有终点任务（EndTask）
        - 任务之间的依赖关系是否正确
        
        :param manifest: 任务清单对象
        :return: 错误列表，如果为空则表示检查通过
        """
        errors: List[str] = []
        
        if not manifest.manifest_id or not manifest.manifest_id.strip():
            errors.append("任务清单ID不能为空")
        
        if not manifest.manifest_name or not manifest.manifest_name.strip():
            errors.append("任务清单名称不能为空")
        
        if not manifest.flow_groups:
            errors.append("任务清单必须包含至少一个任务流组")
            return errors
        
        all_task_ids = set()
        all_roles = set()
        
        for flow_group in manifest.flow_groups:
            if not flow_group.tasks:
                errors.append(
                    f"任务流组 {flow_group.flow_id} 不包含任何任务"
                )
                continue
            
            has_start_task = False
            has_end_task = False
            
            for task in flow_group.tasks:
                task_id = task.task_id
                
                if not task_id or not task_id.strip():
                    errors.append(
                        f"任务流组 {flow_group.flow_id} 包含无效的任务ID"
                    )
                    continue
                
                if task_id in all_task_ids:
                    errors.append(
                        f"任务ID {task_id} 在多个任务流组中重复出现"
                    )
                
                all_task_ids.add(task_id)
                
                if isinstance(task, StartTask):
                    has_start_task = True
                
                from bo.task import EndTask
                if isinstance(task, EndTask):
                    has_end_task = True
                
                if task.execute_role:
                    all_roles.add(task.execute_role)
            
            if not has_start_task:
                errors.append(
                    f"任务流组 {flow_group.flow_id} 缺少起始任务（StartTask）"
                )
            
            if not has_end_task:
                errors.append(
                    f"任务流组 {flow_group.flow_id} 缺少终点任务（EndTask）"
                )
        
        if not errors:
            self._logger.info(f"任务清单 {manifest.manifest_id} 规范性检查通过")
        else:
            self._logger.warning(
                f"任务清单 {manifest.manifest_id} 规范性检查发现 {len(errors)} 个问题"
            )
        
        return errors
    
    def split_manifest_to_flow_groups(self, manifest: TaskManifest) -> List[TaskFlowGroup]:
        """
        将任务清单拆解为任务流组
        
        :param manifest: 任务清单对象
        :return: 任务流组列表
        """
        self._logger.info(
            f"正在拆解任务清单 {manifest.manifest_id}，"
            f"共 {len(manifest.flow_groups)} 个任务流组"
        )
        
        return manifest.flow_groups
    
    def extract_start_tasks(self, flow_group: TaskFlowGroup) -> List[StartTask]:
        """
        从任务流组中提取起始任务
        
        :param flow_group: 任务流组对象
        :return: 起始任务列表
        """
        start_tasks: List[StartTask] = []
        
        for task in flow_group.tasks:
            if isinstance(task, StartTask):
                start_tasks.append(task)
        
        return start_tasks
    
    def dispatch_start_tasks_to_starter(
        self,
        start_tasks: List[StartTask],
        manifest_id: str
    ) -> int:
        """
        将起始任务分派到启动员工的任务清单中
        
        :param start_tasks: 起始任务列表
        :param manifest_id: 任务清单ID（用于日志记录）
        :return: 成功分派的任务数量
        """
        if not self._process_engine:
            raise ValueError("仿真流程引擎未设置，请先调用 set_process_engine()")
        
        starter_worker = self._process_engine.get_worker("__START_WORKER__")
        
        if not starter_worker:
            raise ValueError("启动员工 __Start__AI_Worker 不存在")
        
        dispatched_count = 0
        
        for start_task in start_tasks:
            starter_worker.add_task(start_task)
            dispatched_count += 1
            self._logger.info(
                f"分派起始任务 {start_task.task_id} ({start_task.task_name}) "
                f"到启动员工 {starter_worker.name}"
            )
        
        return dispatched_count
    
    def dispatch_manifest(self, manifest: TaskManifest) -> Dict[str, Any]:
        """
        根据任务清单对象执行完整的分派流程
        
        流程：
        1. 进行规范性检查
        2. 拆解为任务流组
        3. 提取每个流组的起始任务
        4. 将起始任务分派到启动员工
        
        :param manifest: 任务清单对象
        :return: 分派结果信息
        """
        if not self._process_engine:
            raise ValueError("仿真流程引擎未设置")
        
        manifest_id = manifest.manifest_id
        
        self._logger.info("=" * 60)
        self._logger.info(f"开始分派任务清单: {manifest_id}")
        self._logger.info("=" * 60)
        
        validation_errors = self.validate_manifest(manifest)
        
        if validation_errors:
            return {
                "success": False,
                "manifest_id": manifest_id,
                "manifest_name": manifest.manifest_name,
                "validation_errors": validation_errors
            }
        
        flow_groups = self.split_manifest_to_flow_groups(manifest)
        dispatched_flow_groups = []
        total_start_tasks = 0
        
        for flow_group in flow_groups:
            start_tasks = self.extract_start_tasks(flow_group)
            dispatched_count = self.dispatch_start_tasks_to_starter(
                start_tasks, manifest_id
            )
            total_start_tasks += dispatched_count
            dispatched_flow_groups.append({
                "flow_id": flow_group.flow_id,
                "flow_name": flow_group.flow_name,
                "dispatched_start_tasks": dispatched_count
            })
            
            if manifest_id not in self._dispatched_manifests:
                self._dispatched_manifests[manifest_id] = []
            self._dispatched_manifests[manifest_id].append(flow_group.flow_id)
        
        self._logger.info("=" * 60)
        self._logger.info(f"任务清单分派完成: {manifest_id}")
        self._logger.info(f"分派任务流组数量: {len(flow_groups)}")
        self._logger.info(f"分派起始任务总数: {total_start_tasks}")
        self._logger.info("=" * 60)
        
        return {
            "success": True,
            "manifest_id": manifest_id,
            "manifest_name": manifest.manifest_name,
            "flow_groups": dispatched_flow_groups,
            "total_flow_groups": len(flow_groups),
            "total_start_tasks": total_start_tasks
        }
    
    def dispatch_manifest_from_data(
        self,
        manifest_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        根据任务清单数据执行完整的分派流程
        
        :param manifest_data: 任务清单数据字典
        :return: 分派结果信息
        """
        if not self._process_engine:
            raise ValueError("仿真流程引擎未设置")
        
        manifest = TaskManifest(**manifest_data)
        
        manifest_id = manifest.manifest_id
        self._manifest_cache[manifest_id] = manifest
        
        self._logger.info("=" * 60)
        self._logger.info(f"开始分派任务清单（内存数据）: {manifest_id}")
        self._logger.info("=" * 60)
        
        validation_errors = self.validate_manifest(manifest)
        
        if validation_errors:
            return {
                "success": False,
                "manifest_id": manifest_id,
                "manifest_name": manifest.manifest_name,
                "validation_errors": validation_errors
            }
        
        flow_groups = self.split_manifest_to_flow_groups(manifest)
        dispatched_flow_groups = []
        total_start_tasks = 0
        
        for flow_group in flow_groups:
            start_tasks = self.extract_start_tasks(flow_group)
            dispatched_count = self.dispatch_start_tasks_to_starter(
                start_tasks, manifest_id
            )
            total_start_tasks += dispatched_count
            dispatched_flow_groups.append({
                "flow_id": flow_group.flow_id,
                "flow_name": flow_group.flow_name,
                "dispatched_start_tasks": dispatched_count
            })
            
            if manifest_id not in self._dispatched_manifests:
                self._dispatched_manifests[manifest_id] = []
            self._dispatched_manifests[manifest_id].append(flow_group.flow_id)
        
        self._logger.info("=" * 60)
        self._logger.info(f"任务清单分派完成: {manifest_id}")
        self._logger.info(f"分派任务流组数量: {len(flow_groups)}")
        self._logger.info(f"分派起始任务总数: {total_start_tasks}")
        self._logger.info("=" * 60)
        
        return {
            "success": True,
            "manifest_id": manifest_id,
            "manifest_name": manifest.manifest_name,
            "flow_groups": dispatched_flow_groups,
            "total_flow_groups": len(flow_groups),
            "total_start_tasks": total_start_tasks
        }
    
    def get_starter_worker_status(self) -> Optional[Dict[str, Any]]:
        """
        获取启动员工的任务清单状态
        
        :return: 启动员工状态信息，如果引擎未设置返回None
        """
        if not self._process_engine:
            return None
        
        starter_worker = self._process_engine.get_worker("__START_WORKER__")
        
        if not starter_worker:
            return None
        
        task_info = []
        for task in starter_worker.task_list:
            task_info.append({
                "task_id": task.task_id,
                "task_name": task.task_name,
                "execute_role": task.execute_role
            })
        
        return {
            "employee_id": starter_worker.employee_id,
            "name": starter_worker.name,
            "department": starter_worker.department,
            "total_tasks": len(starter_worker.task_list),
            "tasks": task_info
        }
    
    def get_dispatched_manifests(self) -> Dict[str, List[str]]:
        """
        获取已分派的任务清单及其任务流组
        
        :return: 已分派的任务清单字典
        """
        return self._dispatched_manifests.copy()
    
    def clear_cache(self) -> None:
        """清除任务清单缓存"""
        self._manifest_cache.clear()
        self._logger.info("任务清单缓存已清除")
    
    def get_manifest_dir(self) -> str:
        """获取任务清单目录路径"""
        return self._manifest_dir
    
    def set_manifest_dir(self, manifest_dir: str) -> None:
        """
        设置任务清单目录路径
        
        :param manifest_dir: 新的任务清单目录路径
        """
        self._manifest_dir = manifest_dir
        self._ensure_manifest_dir()
        self._logger.info(f"任务清单目录已设置为: {manifest_dir}")


# 示例用法
if __name__ == "__main__":
    from simulation_process_engine import SimulationProcessEngine
    import threading
    import time
    
    from datetime import datetime
    
    sample_manifest = {
        "manifest_id": "TEST001",
        "manifest_name": "测试任务清单",
        "flow_groups": [
            {
                "flow_id": "FLOW001",
                "flow_name": "测试流程1",
                "tasks": [
                    {
                        "task_id": "START001",
                        "task_name": "开始",
                        "task_type": "start",
                        "expected_start_time": datetime.now().isoformat(),
                        "expected_end_time": datetime.now().isoformat(),
                        "content": "开始任务",
                        "task_source": None,
                        "execute_role": "__START__",
                        "resource_consumption": 0.0,
                        "priority": "low",
                        "output_target_role": "DEV",
                        "task_destinations": ["T001"]
                    },
                    {
                        "task_id": "T001",
                        "task_name": "开发任务",
                        "expected_start_time": datetime.now().isoformat(),
                        "expected_end_time": datetime.now().isoformat(),
                        "content": "开发模块",
                        "task_source": "START001",
                        "execute_role": "DEV",
                        "resource_consumption": 1.0,
                        "priority": "high",
                        "output_target_role": "__END__",
                        "task_destinations": ["END001"]
                    },
                    {
                        "task_id": "END001",
                        "task_name": "结束",
                        "task_type": "end",
                        "expected_start_time": datetime.now().isoformat(),
                        "expected_end_time": datetime.now().isoformat(),
                        "content": "结束任务",
                        "task_source": "T001",
                        "execute_role": "__END__",
                        "resource_consumption": 0.0,
                        "priority": "low",
                        "output_target_role": "",
                        "task_destinations": []
                    }
                ]
            }
        ],
        "status": "draft"
    }
    
    manifest_dir = "manifests"
    if not os.path.exists(manifest_dir):
        os.makedirs(manifest_dir)
    
    manifest_file = os.path.join(manifest_dir, "TEST001.json")
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(sample_manifest, f, ensure_ascii=False, indent=2)
    
    print(f"示例任务清单已保存到: {manifest_file}")
    
    sample_org_manifest = {
        'org_id': 'ROOT',
        'name': '总公司',
        'workers': [],
        'children': [
            {
                'org_id': 'RD',
                'name': '研发部',
                'workers': [
                    {
                        'employee_id': 'EMP001',
                        'name': '张三',
                        'department': '研发部',
                        'roles': ['DEV'],
                        'daily_work_hours': 8.0
                    }
                ],
                'children': []
            }
        ]
    }
    
    org_manifest_file = os.path.join(manifest_dir, "sample_org.json")
    with open(org_manifest_file, 'w', encoding='utf-8') as f:
        json.dump(sample_org_manifest, f, ensure_ascii=False, indent=2)
    
    print(f"示例组织清单已保存到: {org_manifest_file}")
    
    process_engine = SimulationProcessEngine(org_manifest_file)
    dispatch_engine = TaskDispatchEngine(process_engine=process_engine)
    
    def run_engine():
        process_engine.run()
    
    engine_thread = threading.Thread(target=run_engine, daemon=True)
    engine_thread.start()
    
    time.sleep(3)
    
    print("\n--- 分派任务清单 ---")
    result = dispatch_engine.dispatch_manifest("TEST001")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    print("\n--- 启动员工状态 ---")
    starter_status = dispatch_engine.get_starter_worker_status()
    print(json.dumps(starter_status, ensure_ascii=False, indent=2))
    
    time.sleep(5)
    
    process_engine.stop()
    time.sleep(2)