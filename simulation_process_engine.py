"""仿真流程引擎模块

该模块负责解析仿真组织清单，启动仿真智能员工实例进入工作状态。
支持多线程方式运行，每个智能员工占用一个独立线程。
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import logging
import sys
import threading
import signal
import time

from bo.organization import Organization, OrganizationFactory
from bo.ai_worker import AIWorker
from bo.task import Task
from worker_type_registry import WorkerTypeRegistry


class SimulationProcessEngine:
    """
    仿真流程引擎
    
    负责管理整个仿真流程的生命周期：
    - 解析仿真组织清单
    - 初始化仿真组织和智能员工
    - 使用多线程启动智能员工工作
    - 管理仿真的启动、运行和停止
    
    :param org_manifest_path: 仿真组织清单文件路径
    :param logger_name: 日志记录器名称
    """
    
    def __init__(self, org_manifest_path: Optional[str] = None):
        self._org_manifest_path = org_manifest_path
        self._logger = self._setup_logging('SimulationProcessEngine')
        self._organizations: Dict[str, Organization] = {}
        self._workers: Dict[str, AIWorker] = {}
        self._role_registry: Dict[str, AIWorker] = {}
        self._is_running: bool = False
        self._root_org: Optional[Organization] = None
        self._lock = threading.Lock()
        self._shutdown_event = threading.Event()
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
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
            'logs/simulation_process_engine.log', mode='w', encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(logging.INFO)
        
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
        
        return logger
    
    def _signal_handler(self, signum, frame) -> None:
        """处理系统信号（SIGINT, SIGTERM）"""
        self._logger.info(f"接收到信号 {signum}，准备关闭仿真引擎...")
        self.stop()
    
    def parse_organization_manifest(self, manifest_path: str) -> Organization:
        """
        解析仿真组织清单文件
        
        :param manifest_path: 组织清单文件路径（JSON格式）
        :return: 根组织对象
        :raises ValueError: 如果文件格式不正确或内容无效
        """
        self._logger.info(f"正在解析组织清单文件: {manifest_path}")
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            manifest_data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON解析错误: {e}")
        
        if 'org_id' not in manifest_data or 'name' not in manifest_data:
            raise ValueError("组织清单必须包含 org_id 和 name 字段")
        
        self._root_org = OrganizationFactory.create_organization_from_config(manifest_data)
        self._organizations[self._root_org.org_id] = self._root_org
        
        self._collect_all_organizations(self._root_org)
        
        self._logger.info(
            f"组织清单解析完成: "
            f"{len(self._organizations)}个组织, "
            f"{self._root_org.get_total_worker_count()}名员工"
        )
        
        return self._root_org
    
    def _collect_all_organizations(self, org: Organization) -> None:
        """递归收集所有组织"""
        for child in org.children:
            self._organizations[child.org_id] = child
            self._collect_all_organizations(child)
    
    def initialize_workers(self) -> None:
        """
        初始化所有智能员工
        
        从组织树中提取所有员工，验证员工类型是否已注册，
        并构建角色注册表。同时创建一个特殊的启动员工 __Start__AI_Worker，
        用于接收所有的启动任务（StartTask）。
        """
        self._logger.info("正在初始化智能员工...")
        
        if not self._root_org:
            raise ValueError("请先解析组织清单")
        
        self._create_start_worker()
        
        all_workers = self._root_org.get_all_workers()
        
        for worker in all_workers:
            worker_type = type(worker).__name__
            
            if not WorkerTypeRegistry.is_registered(worker_type):
                raise ValueError(
                    f"员工 {worker.name} ({worker.employee_id}) 的类型 {worker_type} "
                    f"未在智能员工类型注册表中注册"
                )
            
            self._workers[worker.employee_id] = worker
            
            for role in worker.roles:
                if role not in self._role_registry:
                    self._role_registry[role] = worker
                else:
                    self._logger.warning(
                        f"角色 {role} 已被员工 {self._role_registry[role].name} "
                        f"占用，员工 {worker.name} 的该角色将被忽略"
                    )
            
            self._logger.info(
                f"初始化员工: {worker.name} (ID: {worker.employee_id}, "
                f"类型: {worker_type}, 角色: {worker.roles})"
            )
        
        self._logger.info(
            f"智能员工初始化完成: {len(self._workers)}名员工, "
            f"{len(self._role_registry)}个角色"
        )
    
    def _create_start_worker(self) -> None:
        """
        创建启动员工 __Start__AI_Worker
        
        该员工用于接收所有的启动任务（StartTask），作为仿真流程的入口点。
        它会自动注册一个特殊角色 '__START__'，用于接收启动任务。
        """
        start_worker_id = "__START_WORKER__"
        start_worker_name = "__Start__AI_Worker"
        
        if start_worker_id in self._workers:
            self._logger.warning(f"启动员工 {start_worker_name} 已存在")
            return
        
        start_worker = AIWorker(
            employee_id=start_worker_id,
            name=start_worker_name,
            department="仿真引擎",
            roles=["__START__"]
        )
        
        self._workers[start_worker_id] = start_worker
        self._role_registry["__START__"] = start_worker
        
        self._logger.info(
            f"创建启动员工: {start_worker_name} (ID: {start_worker_id}, "
            f"类型: AIWorker, 角色: ['__START__'])"
        )
    
    def assign_initial_tasks(self, tasks: List[Task]) -> None:
        """
        分配初始任务给员工
        
        根据任务的执行角色分配给对应的员工。
        对于 StartTask（启动任务），会自动分配给 __Start__AI_Worker 员工。
        
        :param tasks: 任务列表
        """
        from bo.task import StartTask
        
        for task in tasks:
            if isinstance(task, StartTask):
                if "__START__" in self._role_registry:
                    worker = self._role_registry["__START__"]
                    worker.add_task(task)
                    self._logger.info(
                        f"分配启动任务 {task.task_id} 给启动员工 {worker.name}"
                    )
                else:
                    self._logger.error(
                        f"无法分配启动任务 {task.task_id}: "
                        f"启动员工 __Start__AI_Worker 未创建"
                    )
            elif task.execute_role in self._role_registry:
                worker = self._role_registry[task.execute_role]
                worker.add_task(task)
                self._logger.info(
                    f"分配任务 {task.task_id} 给员工 {worker.name}"
                )
            else:
                self._logger.warning(
                    f"无法分配任务 {task.task_id}: "
                    f"角色 {task.execute_role} 不存在于角色注册表中"
                )
    
    def start(self) -> None:
        """
        启动仿真引擎
        
        使用多线程方式启动所有智能员工，每个员工占用一个独立线程。
        员工启动后立即进入working状态，持续工作直到引擎停止。
        """
        with self._lock:
            if self._is_running:
                self._logger.warning("仿真引擎已经在运行中")
                return
            
            if not self._workers:
                raise ValueError("请先初始化智能员工")
            
            self._is_running = True
            self._shutdown_event.clear()
            
            self._logger.info("=" * 60)
            self._logger.info("启动仿真流程引擎...")
            self._logger.info(f"启动 {len(self._workers)} 名智能员工")
            self._logger.info("=" * 60)
            
            for worker in self._workers.values():
                worker.working(self._role_registry)
                self._logger.info(f"员工 {worker.name} 已启动工作状态")
            
            self._logger.info("所有智能员工已启动")
    
    def stop(self) -> None:
        """
        停止仿真引擎
        
        停止所有智能员工的工作线程，等待线程结束后退出。
        """
        with self._lock:
            if not self._is_running:
                self._logger.warning("仿真引擎未在运行")
                return
            
            self._logger.info("=" * 60)
            self._logger.info("停止仿真流程引擎...")
            self._logger.info("=" * 60)
            
            self._is_running = False
            self._shutdown_event.set()
            
            for worker in self._workers.values():
                worker.stop_working()
                self._logger.info(f"员工 {worker.name} 已停止工作")
            
            self._logger.info("所有智能员工已停止")
    
    def run(self, manifest_path: Optional[str] = None) -> None:
        """
        完整运行仿真流程
        
        :param manifest_path: 组织清单文件路径（可选，如果已在构造函数中指定）
        """
        if manifest_path:
            self._org_manifest_path = manifest_path
        
        if not self._org_manifest_path:
            raise ValueError("请提供组织清单文件路径")
        
        self._logger.info("=" * 60)
        self._logger.info("仿真流程引擎启动")
        self._logger.info("=" * 60)
        
        try:
            self.parse_organization_manifest(self._org_manifest_path)
            self.initialize_workers()
            self.start()
            
            self._logger.info("仿真引擎运行中，按 Ctrl+C 停止...")
            self._shutdown_event.wait()
            
        except Exception as e:
            self._logger.error(f"仿真引擎运行出错: {e}", exc_info=True)
            self.stop()
            raise
        
        finally:
            self._logger.info("=" * 60)
            self._logger.info("仿真流程引擎关闭")
            self._logger.info("=" * 60)
    
    def get_organization(self, org_id: str) -> Optional[Organization]:
        """获取指定ID的组织"""
        return self._organizations.get(org_id)
    
    def get_worker(self, employee_id: str) -> Optional[AIWorker]:
        """获取指定工号的员工"""
        return self._workers.get(employee_id)
    
    def get_all_organizations(self) -> Dict[str, Organization]:
        """获取所有组织"""
        return self._organizations.copy()
    
    def get_all_workers(self) -> Dict[str, AIWorker]:
        """获取所有员工"""
        return self._workers.copy()
    
    def get_role_registry(self) -> Dict[str, AIWorker]:
        """获取角色注册表"""
        return self._role_registry.copy()
    
    def is_running(self) -> bool:
        """检查仿真引擎是否在运行"""
        return self._is_running
    
    def get_simulation_status(self) -> Dict[str, Any]:
        """获取仿真状态信息"""
        worker_status = []
        for worker in self._workers.values():
            worker_status.append({
                "employee_id": worker.employee_id,
                "name": worker.name,
                "department": worker.department,
                "roles": worker.roles,
                "is_alive": worker._is_alive,
                "is_working": worker._is_working,
                "is_sleeping": worker._is_sleeping,
                "pending_tasks": worker.has_pending_tasks(),
                "total_tasks": len(worker.task_list)
            })
        
        org_summary = []
        for org in self._organizations.values():
            org_summary.append({
                "org_id": org.org_id,
                "name": org.name,
                "worker_count": len(org.workers),
                "child_count": len(org.children)
            })
        
        return {
            "is_running": self._is_running,
            "organization_count": len(self._organizations),
            "worker_count": len(self._workers),
            "role_count": len(self._role_registry),
            "organizations": org_summary,
            "workers": worker_status
        }


# 示例用法
if __name__ == "__main__":
    # 创建示例组织清单
    sample_manifest = {
        "org_id": "ROOT",
        "name": "总公司",
        "workers": [],
        "children": [
            {
                "org_id": "RD",
                "name": "研发部",
                "workers": [
                    {
                        "employee_id": "EMP001",
                        "name": "张三",
                        "department": "研发部",
                        "roles": ["DEV", "TEST"],
                        "daily_work_hours": 8.0
                    },
                    {
                        "employee_id": "EMP002",
                        "name": "李四",
                        "department": "研发部",
                        "roles": ["DEV"],
                        "daily_work_hours": 8.0
                    }
                ],
                "children": [
                    {
                        "org_id": "RD-FE",
                        "name": "前端开发组",
                        "workers": [
                            {
                                "employee_id": "EMP003",
                                "name": "王五",
                                "department": "前端开发组",
                                "roles": ["DEV"],
                                "daily_work_hours": 8.0
                            }
                        ],
                        "children": []
                    }
                ]
            },
            {
                "org_id": "QA",
                "name": "测试部",
                "workers": [
                    {
                        "employee_id": "EMP004",
                        "name": "赵六",
                        "department": "测试部",
                        "roles": ["TEST", "QA"],
                        "daily_work_hours": 8.0
                    }
                ],
                "children": []
            }
        ]
    }
    
    # 保存示例组织清单到文件
    manifest_file = 'sample_org_manifest.json'
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(sample_manifest, f, ensure_ascii=False, indent=2)
    
    print(f"示例组织清单已保存到: {manifest_file}")
    
    # 创建并启动仿真引擎
    engine = SimulationProcessEngine(manifest_file)
    
    try:
        # 在独立线程中运行引擎
        def run_engine():
            engine.run()
        
        engine_thread = threading.Thread(target=run_engine, daemon=True)
        engine_thread.start()
        
        time.sleep(3)
        
        # 添加测试任务
        now = datetime.now()
        test_task = Task(
            task_id="T001",
            task_name="开发用户登录模块",
            expected_start_time=now,
            expected_end_time=now,
            content="开发用户登录功能",
            execute_role="DEV",
            resource_consumption=0.5,
            priority="high",
            output_target_role="TEST"
        )
        
        engine.assign_initial_tasks([test_task])
        
        time.sleep(10)
        
        # 获取状态
        status = engine.get_simulation_status()
        print("\n仿真状态:")
        print(json.dumps(status, ensure_ascii=False, indent=2))
        
    finally:
        engine.stop()
        time.sleep(2)