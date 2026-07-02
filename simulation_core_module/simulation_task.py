"""
仿真任务模块

该模块负责初始化仿真组织和仿真人员，并启动仿真人员进入工作状态。
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import logging
import sys
import signal
import threading
from enum import Enum
import os

from organization import Organization
from ssys.aiworker import AIWorker
from task import Task


class ConfigFormat(str, Enum):
    JSON = "json"
    YAML = "yaml"


class SimulationConfig(BaseModel):
    """仿真任务配置模型"""
    simulation_name: str = Field(description="仿真任务名称")
    start_time: datetime = Field(default_factory=datetime.now, description="仿真开始时间")
    organizations: List['OrganizationConfig'] = Field(default_factory=list, description="组织配置列表")

    @field_validator('start_time', mode='before')
    @classmethod
    def parse_datetime(cls, v: Any) -> datetime:
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00').replace(' ', 'T'))
        return v


class OrganizationConfig(BaseModel):
    """组织配置模型"""
    org_id: str = Field(description="组织唯一标识")
    name: str = Field(description="组织名称")
    parent_org_id: Optional[str] = Field(default=None, description="父组织ID")
    workers: List['WorkerConfig'] = Field(default_factory=list, description="员工配置列表")


class WorkerConfig(BaseModel):
    """员工配置模型"""
    employee_id: str = Field(description="员工工号")
    name: str = Field(description="员工姓名")
    department: str = Field(description="所属部门")
    roles: List[str] = Field(description="扮演的角色列表")
    daily_work_hours: float = Field(default=8.0, description="每天工作时长限制（小时）")
    initial_tasks: List[Dict[str, Any]] = Field(default_factory=list, description="初始任务列表")


class SimulationEngine:
    """
    仿真引擎

    负责管理整个仿真任务的生命周期，包括：
    - 加载配置
    - 初始化组织和人员
    - 启动/停止仿真
    """

    def __init__(self):
        self._logger = self._setup_logging()
        self._organizations: Dict[str, Organization] = {}
        self._workers: Dict[str, AIWorker] = {}
        self._role_registry: Dict[str, AIWorker] = {}
        self._is_running: bool = False
        self._root_org: Optional[Organization] = None
        self._lock = threading.Lock()

    def _setup_logging(self) -> logging.Logger:
        """配置日志"""
        logger = logging.getLogger('SimulationEngine')
        logger.setLevel(logging.INFO)
        logger.propagate = False  # 阻止日志传播到父 logger，避免重复输出

        # 检查是否已添加处理器，避免重复添加
        if logger.handlers:
            return logger

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # 使用绝对路径，基于脚本所在目录
        base_dir = os.path.dirname(os.path.abspath(__file__))
        log_dir = os.path.join(base_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(
            os.path.join(log_dir, 'simulation_engine.log'), mode='w', encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(logging.INFO)

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

        return logger

    def load_config_from_file(self, file_path: str) -> SimulationConfig:
        """
        从文件加载配置

        :param file_path: 配置文件路径
        :return: 仿真配置对象
        """
        self._logger.info(f"从文件加载配置: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if file_path.endswith('.json'):
            config_dict = json.loads(content)
        elif file_path.endswith(('.yaml', '.yml')):
            try:
                import yaml
                config_dict = yaml.safe_load(content)
            except ImportError:
                raise ImportError("需要安装pyyaml库来解析YAML配置文件")
        else:
            raise ValueError("不支持的配置文件格式，请使用JSON或YAML格式")

        config = SimulationConfig(**config_dict)
        self._logger.info(f"配置加载成功: {config.simulation_name}")
        return config

    def load_config_from_dict(self, config_dict: Dict[str, Any]) -> SimulationConfig:
        """
        从字典加载配置

        :param config_dict: 配置字典
        :return: 仿真配置对象
        """
        config = SimulationConfig(**config_dict)
        self._logger.info(f"配置加载成功: {config.simulation_name}")
        return config

    def _create_organization(self, org_config: OrganizationConfig) -> Organization:
        """根据配置创建组织"""
        org = Organization(
            org_id=org_config.org_id,
            name=org_config.name
        )
        self._organizations[org.org_id] = org
        self._logger.info(f"创建组织: {org.name} (ID: {org.org_id})")
        return org

    def _create_worker(self, worker_config: WorkerConfig) -> AIWorker:
        """根据配置创建员工"""
        worker = AIWorker(
            employee_id=worker_config.employee_id,
            name=worker_config.name,
            department=worker_config.department,
            roles=worker_config.roles,
            daily_work_hours=worker_config.daily_work_hours
        )

        for role in worker_config.roles:
            self._role_registry[role] = worker

        for task_dict in worker_config.initial_tasks:
            task = Task(**task_dict)
            worker.add_task(task)

        self._workers[worker.employee_id] = worker
        self._logger.info(
            f"创建员工: {worker.name} (ID: {worker.employee_id}, "
            f"部门: {worker.department}, 角色: {worker.roles})"
        )
        return worker

    def initialize(self, config: SimulationConfig) -> None:
        """
        根据配置初始化仿真环境

        :param config: 仿真配置
        """
        with self._lock:
            self._logger.info("开始初始化仿真环境...")

            self._organizations.clear()
            self._workers.clear()
            self._role_registry.clear()

            for org_config in config.organizations:
                self._create_organization(org_config)

            for org_config in config.organizations:
                if org_config.parent_org_id and org_config.parent_org_id in self._organizations:
                    parent_org = self._organizations[org_config.parent_org_id]
                    child_org = self._organizations[org_config.org_id]
                    parent_org.add_child(child_org)

            for org_config in config.organizations:
                org = self._organizations[org_config.org_id]
                for worker_config in org_config.workers:
                    worker = self._create_worker(worker_config)
                    org.add_worker(worker)

            if self._organizations:
                self._root_org = next(iter(self._organizations.values()))

            self._logger.info(
                f"仿真环境初始化完成: "
                f"{len(self._organizations)}个组织, {len(self._workers)}名员工"
            )

    def start(self) -> None:
        """启动所有仿真人员进入工作状态"""
        with self._lock:
            if self._is_running:
                self._logger.warning("仿真引擎已经在运行中")
                return

            self._is_running = True
            self._logger.info("启动仿真引擎...")

            for worker in self._workers.values():
                worker.working(self._role_registry)

            self._logger.info(f"所有员工已启动工作状态，共{len(self._workers)}人")

    def stop(self) -> None:
        """停止所有仿真人员的工作状态"""
        with self._lock:
            if not self._is_running:
                self._logger.warning("仿真引擎未在运行")
                return

            self._logger.info("停止仿真引擎...")

            for worker in self._workers.values():
                worker.stop_working()

            self._is_running = False
            self._logger.info("仿真引擎已停止")

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

    def get_simulation_status(self) -> Dict[str, Any]:
        """获取仿真状态"""
        worker_status = []
        for worker in self._workers.values():
            worker_status.append({
                "employee_id": worker.employee_id,
                "name": worker.name,
                "is_alive": worker._is_alive,
                "is_working": worker._is_working,
                "is_sleeping": worker._is_sleeping,
                "pending_tasks": worker.has_pending_tasks(),
                "total_tasks": len(worker.task_list)
            })

        return {
            "is_running": self._is_running,
            "organization_count": len(self._organizations),
            "worker_count": len(self._workers),
            "workers": worker_status
        }

    def assign_task_to_worker(self, employee_id: str, task: Task) -> bool:
        """给指定员工分配任务"""
        worker = self._workers.get(employee_id)
        if worker:
            worker.add_task(task)
            self._logger.info(f"已分配任务{task.task_id}给员工{worker.name}")
            return True
        self._logger.warning(f"未找到员工{employee_id}")
        return False

    def assign_task_by_role(self, role: str, task: Task) -> bool:
        """给指定角色的员工分配任务"""
        if role in self._role_registry:
            worker = self._role_registry[role]
            worker.add_task(task)
            self._logger.info(f"已分配任务{task.task_id}给角色{role}的员{worker.name}")
            return True
        self._logger.warning(f"未找到角色{role}对应的员工")
        return False

    def is_running(self) -> bool:
        """检查仿真引擎是否在运行"""
        return self._is_running


class SimulationTaskModule:
    """
    仿真任务模块

    提供独立的仿真任务启动接口，支持配置文件的加载和仿真引擎的管理。
    """

    def __init__(self, config_path: Optional[str] = None):
        self._engine = SimulationEngine()
        self._config_path = config_path
        self._config: Optional[SimulationConfig] = None
        self._logger = self._engine._logger
        self._shutdown_event = threading.Event()

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame) -> None:
        """处理系统信号"""
        self._logger.info(f"接收到信号 {signum}，准备关闭...")
        self.shutdown()

    def load_config(self, config_path: str) -> None:
        """加载配置文件"""
        self._config_path = config_path
        self._config = self._engine.load_config_from_file(config_path)

    def initialize(self, config: Optional[SimulationConfig] = None) -> None:
        """初始化仿真环境"""
        if config:
            self._config = config
        elif not self._config and self._config_path:
            self._config = self._engine.load_config_from_file(self._config_path)

        if not self._config:
            raise ValueError("未提供配置，请先加载配置文件或传入配置对象")

        self._engine.initialize(self._config)

    def start(self) -> None:
        """启动仿真"""
        if not self._config:
            raise ValueError("未初始化配置，请先调用load_config或initialize")

        self._engine.start()
        self._logger.info("仿真任务模块已启动")

    def run(self, config_path: str) -> None:
        """
        完整运行仿真任务

        :param config_path: 配置文件路径
        """
        self._logger.info("=" * 50)
        self._logger.info("仿真任务模块启动")
        self._logger.info("=" * 50)

        self.load_config(config_path)
        self.initialize()
        self.start()

        self._shutdown_event.wait()

        self._logger.info("=" * 50)
        self._logger.info("仿真任务模块关闭")
        self._logger.info("=" * 50)

    def shutdown(self) -> None:
        """关闭仿真任务模块"""
        if self._engine.is_running():
            self._engine.stop()
        self._shutdown_event.set()

    def get_engine(self) -> SimulationEngine:
        """获取仿真引擎"""
        return self._engine


def create_sample_config() -> Dict[str, Any]:
    """创建示例配置"""
    return {
        "simulation_name": "项目仿真任务",
        "start_time": datetime.now().isoformat(),
        "organizations": [
            {
                "org_id": "ORG001",
                "name": "研发部",
                "parent_org_id": None,
                "workers": [
                    {
                        "employee_id": "EMP001",
                        "name": "张三",
                        "department": "研发部",
                        "roles": ["DEV", "TEST"],
                        "daily_work_hours": 8.0,
                        "initial_tasks": []
                    },
                    {
                        "employee_id": "EMP002",
                        "name": "李四",
                        "department": "研发部",
                        "roles": ["TEST", "QA"],
                        "daily_work_hours": 8.0,
                        "initial_tasks": []
                    }
                ]
            },
            {
                "org_id": "ORG002",
                "name": "项目管理部门",
                "parent_org_id": None,
                "workers": [
                    {
                        "employee_id": "EMP003",
                        "name": "王五",
                        "department": "项目管理部门",
                        "roles": ["PM", "PMA"],
                        "daily_work_hours": 8.0,
                        "initial_tasks": []
                    }
                ]
            }
        ]
    }


if __name__ == "__main__":
    import time

    module = SimulationTaskModule()

    sample_config = create_sample_config()
    module.initialize(module._engine.load_config_from_dict(sample_config))
    module.start()

    time.sleep(5)

    engine = module.get_engine()
    now = datetime.now()
    task = Task(
        task_id="T001",
        task_name="测试任务",
        expected_start_time=now,
        expected_end_time=now,
        content="测试任务",
        execute_role="DEV",
        resource_consumption=1.0,
        priority="high",
        output_target_role="TEST"
    )
    engine.assign_task_to_worker("EMP001", task)

    time.sleep(10)

    module.shutdown()
