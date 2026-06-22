"""仿真核心模块

提供仿真引擎、任务管理、任务调度、员工类型注册等核心功能。

核心组件：
- simulation_process_engine: 仿真过程引擎
- simulation_process_module: 仿真过程模块
- simulation_task: 仿真任务定义
- task_dispatch_engine: 任务调度引擎
- worker_type_registry: 员工类型注册表
"""

from .simulation_process_engine import SimulationProcessEngine
from .simulation_process_module import SimulationProcessModule
from .simulation_task import SimulationTask, TaskStatus, TaskType
from .task_dispatch_engine import TaskDispatchEngine
from .worker_type_registry import WorkerTypeRegistry, WorkerType

__all__ = [
    'SimulationProcessEngine',
    'SimulationProcessModule',
    'SimulationTask',
    'TaskStatus',
    'TaskType',
    'TaskDispatchEngine',
    'WorkerTypeRegistry',
    'WorkerType'
]
