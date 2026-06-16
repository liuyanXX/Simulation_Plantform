"""业务对象模块

该模块包含所有业务对象类的定义：
- AIWorker: 智能员工类
- Task, StartTask, EndTask, HaltTask: 任务类
- TaskFlowGroup: 任务流组类
- TasksGraph: 任务图谱类
- TaskManifest: 任务清单类
- Role: 角色类
- Organization: 组织类
"""

from .ai_worker import AIWorker
from .task import Task, StartTask, EndTask, HaltTask
from .task_flow_group import TaskFlowGroup
from .tasks_graph import TasksGraph
from .task_manifest import TaskManifest
from .role import Role
from .organization import Organization, OrganizationFactory

__all__ = [
    'AIWorker',
    'Task',
    'StartTask',
    'EndTask',
    'HaltTask',
    'TaskFlowGroup',
    'TasksGraph',
    'TaskManifest',
    'Role',
    'Organization',
    'OrganizationFactory',
]
