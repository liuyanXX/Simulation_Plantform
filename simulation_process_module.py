"""仿真任务模块

该模块负责协调仿真流程引擎和任务分派引擎的启动、运行和停止。
提供统一的接口管理整个仿真任务的生命周期。
"""
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import sys
import threading

from pydantic import BaseModel, Field, field_validator

from bo.task_manifest import TaskManifest
from bo.organization import Organization
from simulation_process_engine import SimulationProcessEngine
from task_dispatch_engine import TaskDispatchEngine


class SimulationProcessModuleConfig(BaseModel):
    """
    仿真任务模块配置
    
    :param org_manifest_path: 仿真组织清单文件路径
    :param manifest_dir: 任务清单文件目录
    :param auto_start: 是否自动启动仿真
    :param stop_timeout: 停止超时时间（秒）
    """
    org_manifest_path: str = Field(description="仿真组织清单文件路径")
    manifest_dir: Optional[str] = Field(default=None, description="任务清单文件目录")
    auto_start: bool = Field(default=False, description="是否自动启动仿真")
    stop_timeout: float = Field(default=30.0, description="停止超时时间（秒）")
    
    @field_validator('stop_timeout')
    @classmethod
    def validate_stop_timeout(cls, v: float) -> float:
        """验证停止超时时间"""
        if v <= 0:
            raise ValueError("停止超时时间必须大于0")
        return v


class SimulationProcessModuleStatus(BaseModel):
    """
    仿真任务模块状态
    
    :param is_running: 是否正在运行
    :param process_engine_running: 仿真流程引擎是否运行
    :param dispatch_engine_ready: 任务分派引擎是否就绪
    :param manifest_dispatched: 任务清单是否已分派
    :param start_time: 启动时间
    :param stop_time: 停止时间
    """
    is_running: bool = Field(description="是否正在运行")
    process_engine_running: bool = Field(description="仿真流程引擎是否运行")
    dispatch_engine_ready: bool = Field(description="任务分派引擎是否就绪")
    manifest_dispatched: bool = Field(description="任务清单是否已分派")
    start_time: Optional[datetime] = Field(default=None, description="启动时间")
    stop_time: Optional[datetime] = Field(default=None, description="停止时间")


class SimulationProcessModule:
    """
    仿真任务模块
    
    负责协调仿真流程引擎和任务分派引擎的启动、运行和停止。
    提供统一的接口管理整个仿真任务的生命周期。
    
    主要功能：
    - 接收任务清单对象和仿真组织清单对象
    - 启动仿真流程引擎和任务分派引擎
    - 分派任务清单到仿真流程引擎
    - 同步停止所有引擎
    
    设计原则：
    - 面向对象设计：封装引擎管理逻辑，提供清晰的接口
    - 微服务设计：模块独立运行，通过接口与其他组件交互
    - 单一职责：专注于仿真任务的协调管理
    
    :param config: 仿真任务模块配置
    """
    
    def __init__(self, config: SimulationProcessModuleConfig):
        """
        初始化仿真任务模块
        
        :param config: 仿真任务模块配置
        """
        self._config = config
        self._logger = self._setup_logging('SimulationProcessModule')
        
        # 引擎实例
        self._process_engine: Optional[SimulationProcessEngine] = None
        self._dispatch_engine: Optional[TaskDispatchEngine] = None
        
        # 状态管理
        self._is_running: bool = False
        self._manifest_dispatched: bool = False
        self._start_time: Optional[datetime] = None
        self._stop_time: Optional[datetime] = None
        self._lock = threading.Lock()
        
        # 仿真流程引擎运行线程
        self._engine_thread: Optional[threading.Thread] = None
        
        self._logger.info("仿真任务模块初始化完成")
    
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
            'logs/simulation_process_module.log', mode='w', encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(logging.INFO)
        
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
        
        return logger
    
    def start(self) -> None:
        """
        启动仿真任务模块
        
        依次启动仿真流程引擎和任务分派引擎。
        """
        with self._lock:
            if self._is_running:
                self._logger.warning("仿真任务模块已经在运行中")
                return
            
            self._logger.info("=" * 60)
            self._logger.info("启动仿真任务模块")
            self._logger.info("=" * 60)
            
            self._start_time = datetime.now()
            self._is_running = True
            self._manifest_dispatched = False
            
            try:
                # 1. 启动仿真流程引擎
                self._start_process_engine()
                
                # 2. 启动任务分派引擎
                self._start_dispatch_engine()
                
                self._logger.info("=" * 60)
                self._logger.info("仿真任务模块启动完成")
                self._logger.info("=" * 60)
                
            except Exception as e:
                self._logger.error(f"启动仿真任务模块失败: {e}", exc_info=True)
                self._stop_all_engines()
                self._is_running = False
                raise
    
    def _start_process_engine(self) -> None:
        """
        启动仿真流程引擎
        
        在独立线程中运行仿真流程引擎，避免阻塞主线程。
        """
        self._logger.info("正在启动仿真流程引擎...")
        
        # 创建仿真流程引擎
        self._process_engine = SimulationProcessEngine(
            self._config.org_manifest_path
        )
        
        # 在独立线程中运行引擎
        def run_engine():
            try:
                self._process_engine.run()
            except Exception as e:
                self._logger.error(f"仿真流程引擎运行出错: {e}", exc_info=True)
        
        self._engine_thread = threading.Thread(
            target=run_engine,
            daemon=True,
            name="SimulationProcessEngine-Thread"
        )
        self._engine_thread.start()
        
        # 等待引擎初始化完成
        import time
        time.sleep(2)
        
        if not self._process_engine.is_running():
            raise RuntimeError("仿真流程引擎启动失败")
        
        self._logger.info("仿真流程引擎启动成功")
    
    def _start_dispatch_engine(self) -> None:
        """
        启动任务分派引擎
        
        将仿真流程引擎实例传递给任务分派引擎。
        """
        self._logger.info("正在启动任务分派引擎...")
        
        # 创建任务分派引擎
        self._dispatch_engine = TaskDispatchEngine(
            process_engine=self._process_engine,
            manifest_dir=self._config.manifest_dir
        )
        
        self._logger.info("任务分派引擎启动成功")
    
    def dispatch_manifest(self, manifest: TaskManifest) -> Dict[str, Any]:
        """
        分派任务清单
        
        将任务清单对象传递给任务分派引擎进行分派。
        
        :param manifest: 任务清单对象
        :return: 分派结果
        """
        if not self._is_running:
            raise RuntimeError("仿真任务模块未启动，请先调用 start() 方法")
        
        if not self._dispatch_engine:
            raise RuntimeError("任务分派引擎未初始化")
        
        self._logger.info("=" * 60)
        self._logger.info(f"分派任务清单: {manifest.manifest_id}")
        self._logger.info("=" * 60)
        
        result = self._dispatch_engine.dispatch_manifest(manifest)
        
        if result.get("success"):
            self._manifest_dispatched = True
            self._logger.info("任务清单分派成功")
        else:
            self._logger.error("任务清单分派失败")
        
        return result
    
    def stop(self) -> None:
        """
        停止仿真任务模块
        
        同步停止仿真流程引擎和任务分派引擎。
        """
        with self._lock:
            if not self._is_running:
                self._logger.warning("仿真任务模块未在运行")
                return
            
            self._logger.info("=" * 60)
            self._logger.info("停止仿真任务模块")
            self._logger.info("=" * 60)
            
            self._stop_time = datetime.now()
            self._is_running = False
            
            try:
                self._stop_all_engines()
                
                self._logger.info("=" * 60)
                self._logger.info("仿真任务模块停止完成")
                self._logger.info("=" * 60)
                
            except Exception as e:
                self._logger.error(f"停止仿真任务模块失败: {e}", exc_info=True)
                raise
    
    def _stop_all_engines(self) -> None:
        """
        停止所有引擎
        
        同步停止仿真流程引擎和任务分派引擎。
        """
        # 停止仿真流程引擎
        if self._process_engine:
            self._logger.info("正在停止仿真流程引擎...")
            self._process_engine.stop()
            self._logger.info("仿真流程引擎已停止")
        
        # 任务分派引擎不需要显式停止，它只是仿真流程引擎的包装器
        self._dispatch_engine = None
        
        # 等待引擎线程结束
        if self._engine_thread and self._engine_thread.is_alive():
            self._engine_thread.join(timeout=self._config.stop_timeout)
            if self._engine_thread.is_alive():
                self._logger.warning("仿真流程引擎线程未在超时时间内结束")
        
        self._process_engine = None
    
    def get_status(self) -> SimulationProcessModuleStatus:
        """
        获取仿真任务模块状态
        
        :return: 模块状态信息
        """
        process_engine_running = (
            self._process_engine is not None and
            self._process_engine.is_running()
        )
        
        dispatch_engine_ready = self._dispatch_engine is not None
        
        return SimulationProcessModuleStatus(
            is_running=self._is_running,
            process_engine_running=process_engine_running,
            dispatch_engine_ready=dispatch_engine_ready,
            manifest_dispatched=self._manifest_dispatched,
            start_time=self._start_time,
            stop_time=self._stop_time
        )
    
    def get_process_engine(self) -> Optional[SimulationProcessEngine]:
        """
        获取仿真流程引擎实例
        
        :return: 仿真流程引擎实例，如果未初始化返回None
        """
        return self._process_engine
    
    def get_dispatch_engine(self) -> Optional[TaskDispatchEngine]:
        """
        获取任务分派引擎实例
        
        :return: 任务分派引擎实例，如果未初始化返回None
        """
        return self._dispatch_engine
    
    def get_simulation_status(self) -> Optional[Dict[str, Any]]:
        """
        获取仿真状态信息
        
        :return: 仿真状态信息，如果引擎未运行返回None
        """
        if not self._process_engine:
            return None
        
        return self._process_engine.get_simulation_status()
    
    def get_starter_worker_status(self) -> Optional[Dict[str, Any]]:
        """
        获取启动员工状态
        
        :return: 启动员工状态信息，如果引擎未就绪返回None
        """
        if not self._dispatch_engine:
            return None
        
        return self._dispatch_engine.get_starter_worker_status()
    
    def is_running(self) -> bool:
        """
        检查模块是否正在运行
        
        :return: 如果正在运行返回True，否则返回False
        """
        return self._is_running
    
    def is_manifest_dispatched(self) -> bool:
        """
        检查任务清单是否已分派
        
        :return: 如果已分派返回True，否则返回False
        """
        return self._manifest_dispatched
    
    def __enter__(self):
        """
        上下文管理器入口
        
        支持使用 with 语句自动管理模块生命周期。
        """
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        上下文管理器出口
        
        自动停止模块。
        """
        self.stop()
        return False


# 示例用法
if __name__ == "__main__":
    import json
    import os
    import time
    
    # 创建示例组织清单
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
                    },
                    {
                        'employee_id': 'EMP002',
                        'name': '李四',
                        'department': '研发部',
                        'roles': ['TEST'],
                        'daily_work_hours': 8.0
                    }
                ],
                'children': []
            }
        ]
    }
    
    # 保存组织清单
    org_manifest_file = 'sample_org_manifest_module.json'
    with open(org_manifest_file, 'w', encoding='utf-8') as f:
        json.dump(sample_org_manifest, f, ensure_ascii=False, indent=2)
    
    print(f"示例组织清单已保存到: {org_manifest_file}")
    
    # 创建示例任务清单
    from datetime import datetime
    from bo.task import StartTask, EndTask, Task
    from bo.task_flow_group import TaskFlowGroup
    
    now = datetime.now()
    
    # 创建任务对象
    start_task = StartTask(
        task_id="START001",
        task_name="开始",
        expected_start_time=now,
        expected_end_time=now,
        content="流程开始",
        task_source=None,
        execute_role="__START__",
        resource_consumption=0.0,
        priority="low",
        output_target_role="DEV",
        task_destinations=["T001"]
    )
    
    dev_task = Task(
        task_id="T001",
        task_name="开发任务",
        expected_start_time=now,
        expected_end_time=now,
        content="开发用户模块",
        task_source="START001",
        execute_role="DEV",
        resource_consumption=1.0,
        priority="high",
        output_target_role="TEST",
        task_destinations=["T002"]
    )
    
    test_task = Task(
        task_id="T002",
        task_name="测试任务",
        expected_start_time=now,
        expected_end_time=now,
        content="测试用户模块",
        task_source="T001",
        execute_role="TEST",
        resource_consumption=0.5,
        priority="high",
        output_target_role="__END__",
        task_destinations=["END001"]
    )
    
    end_task = EndTask(
        task_id="END001",
        task_name="结束",
        expected_start_time=now,
        expected_end_time=now,
        content="流程结束",
        task_source="T002",
        execute_role="__END__",
        resource_consumption=0.0,
        priority="low",
        output_target_role="",
        task_destinations=[]
    )
    
    # 创建任务流组
    flow_group = TaskFlowGroup(
        flow_id="FLOW001",
        flow_name="开发流程",
        tasks=[start_task, dev_task, test_task, end_task]
    )
    
    # 创建任务清单对象
    manifest = TaskManifest(
        manifest_id="SIM001",
        manifest_name="仿真测试清单",
        flow_groups=[flow_group],
        status="active"
    )
    
    # 创建仿真任务模块配置
    config = SimulationProcessModuleConfig(
        org_manifest_path=org_manifest_file,
        manifest_dir="manifests",
        auto_start=False
    )
    
    # 使用 with 语句管理模块生命周期
    print("\n--- 启动仿真任务模块 ---")
    with SimulationProcessModule(config) as module:
        # 检查状态
        status = module.get_status()
        print(f"模块状态: {status.model_dump_json(indent=2)}")
        
        # 分派任务清单
        print("\n--- 分派任务清单 ---")
        result = module.dispatch_manifest(manifest)
        print(f"分派结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # 获取启动员工状态
        print("\n--- 启动员工状态 ---")
        starter_status = module.get_starter_worker_status()
        print(json.dumps(starter_status, ensure_ascii=False, indent=2))
        
        # 等待一段时间观察仿真运行
        print("\n--- 仿真运行中... ---")
        time.sleep(5)
        
        # 获取仿真状态
        print("\n--- 仿真状态 ---")
        sim_status = module.get_simulation_status()
        print(json.dumps(sim_status, ensure_ascii=False, indent=2))
    
    print("\n--- 仿真任务模块已停止 ---")
    
    # 清理临时文件
    if os.path.exists(org_manifest_file):
        os.remove(org_manifest_file)
        print(f"已删除临时文件: {org_manifest_file}")