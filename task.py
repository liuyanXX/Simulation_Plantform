from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
from enum import Enum


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskType(str, Enum):
    """任务类型枚举"""
    NORMAL = "normal"
    START = "start"
    END = "end"
    HALT = "halt"


class Task(BaseModel):
    task_id: str = Field(description="任务唯一标识")
    task_name: str = Field(description="任务名称（人类可读）")
    expected_start_time: datetime = Field(description="期望开始时间")
    expected_end_time: datetime = Field(description="期望结束时间")
    scheduled_start_time: Optional[datetime] = Field(default=None, description="排期开始时间")
    scheduled_end_time: Optional[datetime] = Field(default=None, description="排期结束时间")
    actual_start_time: Optional[datetime] = Field(default=None, description="实际开始时间")
    actual_end_time: Optional[datetime] = Field(default=None, description="实际结束时间")
    content: str = Field(description="工作内容")
    execute_role: str = Field(description="执行角色")
    resource_consumption: float = Field(description="资源消耗（工时）")
    priority: Priority = Field(description="优先级")
    output_target_role: str = Field(description="输出物目标角色（实际触发的下一任务的执行角色）")
    next_task_info: Optional[Dict[str, Any]] = Field(default=None, description="下一步任务信息")
    is_completed: bool = Field(default=False, description="任务是否完成")
    task_source: Optional[str] = Field(default=None, description="任务来源（触发本任务的上一任务ID）")
    task_destinations: List[str] = Field(default_factory=list, description="任务去向（本任务完成后可能触发的所有任务ID列表）")
    task_type: TaskType = Field(default=TaskType.NORMAL, description="任务类型")

    @field_validator('priority')
    @classmethod
    def priority_must_be_valid(cls, v: Priority) -> Priority:
        if v not in [Priority.HIGH, Priority.MEDIUM, Priority.LOW]:
            raise ValueError('priority must be high, medium, or low')
        return v

    @field_validator('expected_start_time', 'expected_end_time', mode='before')
    @classmethod
    def parse_datetime(cls, v: Any) -> datetime:
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00').replace(' ', 'T'))
        return v

    def to_json(self) -> str:
        return json.dumps(self.model_dump(mode='json'), ensure_ascii=False, indent=2)

    def update_task(self, **kwargs) -> None:
        """
        修改任务对象的属性
        
        支持动态修改任务的任意属性，属性名称必须是 Task 类已定义的字段。
        
        :param kwargs: 要修改的属性键值对
        :raises ValueError: 如果传入了未定义的属性名
        """
        valid_fields = self.model_fields.keys()
        for key, value in kwargs.items():
            if key not in valid_fields:
                raise ValueError(f"属性 '{key}' 不是 Task 类的有效字段")
        
        for key, value in kwargs.items():
            setattr(self, key, value)


class StartTask(Task):
    """
    开始任务类
    
    代表任务流的起点任务，具有以下特点：
    - 不再有上一任务（task_source必须为None）
    - 是任务流的入口点
    - 可以触发后续任务
    
    示例用法：
        start_task = StartTask(
            task_id="START001",
            task_name="流程开始",
            expected_start_time=datetime.now(),
            expected_end_time=datetime.now(),
            content="流程开始节点",
            execute_role="SYSTEM",
            resource_consumption=0.0,
            priority="low",
            output_target_role="DEV",
            task_destinations=["T001", "T002"]
        )
    """
    
    @model_validator(mode='after')
    def validate_start_task(self) -> 'StartTask':
        """验证开始任务的约束条件"""
        if self.task_source is not None:
            raise ValueError("StartTask 不能有上一任务，task_source 必须为 None")
        
        self.task_type = TaskType.START
        
        return self


class EndTask(Task):
    """
    结束任务类
    
    代表任务流的正常终点任务，具有以下特点：
    - 不再有下一任务
    - task_destinations 必须为空列表
    - next_task_info 必须为 None
    - output_target_role 必须为空字符串
    - 标志任务流的正常结束
    
    示例用法：
        end_task = EndTask(
            task_id="END001",
            task_name="流程结束",
            expected_start_time=datetime.now(),
            expected_end_time=datetime.now(),
            content="流程结束节点",
            execute_role="SYSTEM",
            resource_consumption=0.0,
            priority="low",
            task_source="T003"
        )
    """
    
    @model_validator(mode='after')
    def validate_end_task(self) -> 'EndTask':
        """验证结束任务的约束条件"""
        if self.task_destinations:
            raise ValueError("EndTask 不能有下一任务，task_destinations 必须为空列表")
        
        if self.next_task_info is not None:
            raise ValueError("EndTask 不能有后续任务信息，next_task_info 必须为 None")
        
        if self.output_target_role != "":
            raise ValueError("EndTask 不能有输出目标角色，output_target_role 必须为空字符串")
        
        self.task_type = TaskType.END
        
        return self


class HaltTask(Task):
    """
    中断任务类
    
    代表任务流的异常中断点任务，具有以下特点：
    - 不再有下一任务
    - task_destinations 必须为空列表
    - next_task_info 必须为 None
    - output_target_role 必须为空字符串
    - 标志任务流的异常中断，通常用于错误处理或流程终止
    
    示例用法：
        halt_task = HaltTask(
            task_id="HALT001",
            task_name="流程中断",
            expected_start_time=datetime.now(),
            expected_end_time=datetime.now(),
            content="流程异常中断节点",
            execute_role="SYSTEM",
            resource_consumption=0.0,
            priority="high",
            task_source="T002"
        )
    """
    
    @model_validator(mode='after')
    def validate_halt_task(self) -> 'HaltTask':
        """验证中断任务的约束条件"""
        if self.task_destinations:
            raise ValueError("HaltTask 不能有下一任务，task_destinations 必须为空列表")
        
        if self.next_task_info is not None:
            raise ValueError("HaltTask 不能有后续任务信息，next_task_info 必须为 None")
        
        if self.output_target_role != "":
            raise ValueError("HaltTask 不能有输出目标角色，output_target_role 必须为空字符串")
        
        self.task_type = TaskType.HALT
        
        return self


class TaskFlowGroup(BaseModel):
    """
    任务流组类
    
    表示一个任务流组，包含一组任务，这些任务可以串行执行形成一条任务流。
    
    :param flow_id: 任务流唯一标识
    :param flow_name: 任务流名称（人类可读）
    :param tasks: 任务列表，按执行顺序排列
    :param description: 任务流描述
    
    任务流约束规则：
    1. 必须有且仅有一个开始任务（StartTask），且必须在列表首位
    2. 必须有且仅有一个终点任务（EndTask或HaltTask），且必须在列表末位
    3. 不能从StartTask直接到EndTask或HaltTask，中间必须至少有一个普通任务
    4. 普通任务的下一任务可以是普通Task、EndTask或HaltTask
    5. 任务之间通过task_source和task_destinations建立关联
    
    示例用法：
        flow = TaskFlowGroup(
            flow_id="FLOW001",
            flow_name="用户登录流程",
            tasks=[
                StartTask(...),
                Task(...),
                EndTask(...)
            ],
            description="用户登录功能的完整业务流程"
        )
    """
    flow_id: str = Field(description="任务流唯一标识")
    flow_name: str = Field(description="任务流名称（人类可读）")
    tasks: List['Task'] = Field(default_factory=list, description="任务列表，按执行顺序排列")
    description: Optional[str] = Field(default=None, description="任务流描述")
    
    @model_validator(mode='after')
    def validate_task_flow(self) -> 'TaskFlowGroup':
        """验证任务流的完整性和正确性"""
        if not self.tasks:
            raise ValueError("任务流不能为空，至少需要包含开始任务、普通任务和结束任务")
        
        # 验证必须有且仅有一个开始任务，且在首位
        start_tasks = [t for t in self.tasks if isinstance(t, StartTask)]
        if len(start_tasks) != 1:
            raise ValueError(f"任务流必须有且仅有一个开始任务，当前有 {len(start_tasks)} 个")
        
        if not isinstance(self.tasks[0], StartTask):
            raise ValueError("开始任务必须位于任务流的首位")
        
        # 验证必须有且仅有一个终点任务，且在末位
        end_tasks = [t for t in self.tasks if isinstance(t, (EndTask, HaltTask))]
        if len(end_tasks) != 1:
            raise ValueError(f"任务流必须有且仅有一个终点任务，当前有 {len(end_tasks)} 个")
        
        if not isinstance(self.tasks[-1], (EndTask, HaltTask)):
            raise ValueError("终点任务必须位于任务流的末位")
        
        # 验证不能从StartTask直接到EndTask或HaltTask
        if len(self.tasks) < 3:
            raise ValueError("任务流至少需要包含3个任务：开始任务、至少一个普通任务、终点任务")
        
        if isinstance(self.tasks[1], (EndTask, HaltTask)):
            raise ValueError("开始任务不能直接连接到终点任务，中间必须至少有一个普通任务")
        
        # 验证任务链的连续性
        self._validate_task_chain()
        
        return self
    
    def _validate_task_chain(self) -> None:
        """验证并修复任务之间的链接关系"""
        for i in range(len(self.tasks) - 1):
            current_task = self.tasks[i]
            next_task = self.tasks[i + 1]
            
            # 设置当前任务的task_destinations包含下一任务ID
            if next_task.task_id not in current_task.task_destinations:
                current_task.task_destinations.append(next_task.task_id)
            
            # 清理当前任务中不属于任务流的任务ID
            valid_destinations = []
            task_ids = {t.task_id for t in self.tasks[i+1:]}
            for dest_id in current_task.task_destinations:
                if dest_id in task_ids:
                    valid_destinations.append(dest_id)
            current_task.task_destinations = valid_destinations
            
            # 设置下一任务的task_source为当前任务ID
            next_task.task_source = current_task.task_id
            
            # 设置当前任务的output_target_role为下一任务的execute_role
            if isinstance(next_task, (EndTask, HaltTask)):
                current_task.output_target_role = ""
            else:
                current_task.output_target_role = next_task.execute_role
    
    def add_task(self, task: 'Task', position: Optional[int] = None) -> None:
        """
        添加任务到任务流
        
        :param task: 要添加的任务对象
        :param position: 插入位置（可选），不指定则添加到末尾（但在终点任务之前）
        :raises ValueError: 如果添加位置无效或违反任务流约束
        """
        if not self.tasks:
            # 如果任务流为空，只允许添加StartTask
            if not isinstance(task, StartTask):
                raise ValueError("空任务流只能先添加StartTask")
            self.tasks.append(task)
            return
        
        # 检查是否已经有开始任务
        has_start = any(isinstance(t, StartTask) for t in self.tasks)
        has_end = any(isinstance(t, (EndTask, HaltTask)) for t in self.tasks)
        
        if isinstance(task, StartTask):
            if has_start:
                raise ValueError("任务流已经有一个开始任务")
            # 插入到首位
            self.tasks.insert(0, task)
        elif isinstance(task, (EndTask, HaltTask)):
            if has_end:
                raise ValueError("任务流已经有一个终点任务")
            # 添加到末尾
            self.tasks.append(task)
        else:
            # 普通任务，插入到指定位置或终点任务之前
            if position is not None:
                if position < 0 or position > len(self.tasks):
                    raise ValueError("插入位置无效")
                if has_end and position >= len(self.tasks):
                    raise ValueError("普通任务不能插入到终点任务之后")
                insert_pos = position
            else:
                # 默认插入到终点任务之前
                if has_end:
                    insert_pos = len(self.tasks) - 1
                else:
                    insert_pos = len(self.tasks)
            
            # 重置任务的关联属性，让 _validate_task_chain 重新设置
            task.task_source = None
            task.task_destinations = []
            task.output_target_role = ""
            
            self.tasks.insert(insert_pos, task)
        
        # 重新验证任务流
        self._validate_task_chain()
    
    def remove_task(self, task_id: str) -> None:
        """
        从任务流中移除指定任务
        
        :param task_id: 要移除的任务ID
        :raises ValueError: 如果任务不存在或尝试移除开始/终点任务
        """
        task_index = None
        for i, task in enumerate(self.tasks):
            if task.task_id == task_id:
                task_index = i
                break
        
        if task_index is None:
            raise ValueError(f"未找到任务: {task_id}")
        
        if isinstance(self.tasks[task_index], (StartTask, EndTask, HaltTask)):
            raise ValueError("不能移除开始任务或终点任务")
        
        del self.tasks[task_index]
        
        # 重新验证任务流
        self._validate_task_chain()
    
    def update_task(self, task_id: str, **kwargs) -> None:
        """
        修改任务流中的指定任务
        
        :param task_id: 要修改的任务ID
        :param kwargs: 要修改的属性键值对
        :raises ValueError: 如果任务不存在
        """
        for task in self.tasks:
            if task.task_id == task_id:
                task.update_task(**kwargs)
                return
        
        raise ValueError(f"未找到任务: {task_id}")
    
    def get_task(self, task_id: str) -> Optional['Task']:
        """
        获取指定任务
        
        :param task_id: 任务ID
        :return: 任务对象，如果未找到返回None
        """
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        return None
    
    def get_start_task(self) -> Optional['StartTask']:
        """获取开始任务"""
        for task in self.tasks:
            if isinstance(task, StartTask):
                return task
        return None
    
    def get_end_task(self) -> Optional['Task']:
        """获取终点任务（EndTask或HaltTask）"""
        for task in self.tasks:
            if isinstance(task, (EndTask, HaltTask)):
                return task
        return None
    
    def get_normal_tasks(self) -> List['Task']:
        """获取所有普通任务"""
        return [t for t in self.tasks if isinstance(t, Task) and not isinstance(t, (StartTask, EndTask, HaltTask))]
    
    def get_flow_length(self) -> int:
        """获取任务流长度（任务数量）"""
        return len(self.tasks)
    
    def is_valid(self) -> bool:
        """检查任务流是否有效"""
        try:
            self.validate_task_flow()
            return True
        except ValueError:
            return False
    
    def to_json(self) -> str:
        """导出任务流为JSON格式"""
        return json.dumps(self.model_dump(mode='json'), ensure_ascii=False, indent=2)
    
    def get_flow_summary(self) -> Dict[str, Any]:
        """获取任务流摘要信息"""
        start_task = self.get_start_task()
        end_task = self.get_end_task()
        normal_tasks = self.get_normal_tasks()
        
        return {
            "flow_id": self.flow_id,
            "flow_name": self.flow_name,
            "description": self.description,
            "total_tasks": self.get_flow_length(),
            "start_task_id": start_task.task_id if start_task else None,
            "end_task_id": end_task.task_id if end_task else None,
            "end_task_type": end_task.task_type.value if end_task else None,
            "normal_task_count": len(normal_tasks),
            "normal_task_ids": [t.task_id for t in normal_tasks]
        }
    
    def __str__(self) -> str:
        """返回任务流的字符串表示"""
        return f"TaskFlowGroup(flow_id={self.flow_id}, flow_name={self.flow_name}, tasks={len(self.tasks)}个)"


# 更新类型提示引用
Task.update_forward_refs()
StartTask.update_forward_refs()
EndTask.update_forward_refs()
HaltTask.update_forward_refs()
TaskFlowGroup.update_forward_refs()


class TaskGraph(BaseModel):
    """
    任务图谱类
    
    表示一个有向图结构的任务图谱，图中的节点都是Task类或其子类。
    支持从开始任务到终点任务的路径分析和拆分。
    
    :param graph_id: 图谱唯一标识
    :param graph_name: 图谱名称（人类可读）
    :param tasks: 任务节点列表
    :param description: 图谱描述
    
    图谱约束规则：
    1. 图中可以有多个开始任务（StartTask）
    2. 图中可以有多个终点任务（EndTask或HaltTask）
    3. 路径的起点必须是StartTask，终点必须是EndTask或HaltTask
    4. 普通任务可以有多个来源和多个去向（支持分支和汇聚）
    5. 任务之间通过task_source和task_destinations建立有向边
    
    示例用法：
        graph = TaskGraph(
            graph_id="GRAPH001",
            graph_name="用户注册登录流程",
            tasks=[start_task, task1, task2, task3, end_task, halt_task],
            description="包含分支逻辑的用户注册登录业务流程"
        )
        
        # 获取所有路径
        paths = graph.extract_all_paths()
        
        # 将路径转换为任务流组
        flows = graph.split_into_flow_groups()
    """
    graph_id: str = Field(description="图谱唯一标识")
    graph_name: str = Field(description="图谱名称（人类可读）")
    tasks: List['Task'] = Field(default_factory=list, description="任务节点列表")
    description: Optional[str] = Field(default=None, description="图谱描述")
    
    @model_validator(mode='after')
    def validate_graph(self) -> 'TaskGraph':
        """验证任务图谱的完整性"""
        if not self.tasks:
            raise ValueError("任务图谱不能为空")
        
        # 构建任务ID到任务对象的映射
        task_map = {t.task_id: t for t in self.tasks}
        
        # 验证所有task_destinations中的任务ID都存在
        for task in self.tasks:
            for dest_id in task.task_destinations:
                if dest_id not in task_map:
                    raise ValueError(f"任务 {task.task_id} 的 task_destinations 中包含不存在的任务ID: {dest_id}")
        
        # 验证所有task_source引用的任务ID都存在（除了StartTask）
        for task in self.tasks:
            if task.task_source is not None and task.task_source not in task_map:
                raise ValueError(f"任务 {task.task_id} 的 task_source 引用了不存在的任务ID: {task.task_source}")
        
        return self
    
    def get_task_map(self) -> Dict[str, 'Task']:
        """获取任务ID到任务对象的映射"""
        return {t.task_id: t for t in self.tasks}
    
    def get_start_tasks(self) -> List['StartTask']:
        """获取所有开始任务"""
        return [t for t in self.tasks if isinstance(t, StartTask)]
    
    def get_end_tasks(self) -> List['Task']:
        """获取所有终点任务（EndTask或HaltTask）"""
        return [t for t in self.tasks if isinstance(t, (EndTask, HaltTask))]
    
    def get_normal_tasks(self) -> List['Task']:
        """获取所有普通任务"""
        return [t for t in self.tasks if isinstance(t, Task) and not isinstance(t, (StartTask, EndTask, HaltTask))]
    
    def extract_all_paths(self) -> List[List[str]]:
        """
        提取所有从StartTask到EndTask或HaltTask的路径
        
        :return: 路径列表，每条路径是任务ID的列表
        """
        paths = []
        start_tasks = self.get_start_tasks()
        task_map = self.get_task_map()
        
        def dfs(current_task_id: str, visited: set, path: List[str]) -> None:
            """深度优先搜索查找路径"""
            if current_task_id in visited:
                return
            
            visited.add(current_task_id)
            path.append(current_task_id)
            
            current_task = task_map[current_task_id]
            
            # 如果到达终点任务，记录路径
            if isinstance(current_task, (EndTask, HaltTask)):
                paths.append(path.copy())
                visited.remove(current_task_id)
                path.pop()
                return
            
            # 继续搜索下一任务
            for dest_id in current_task.task_destinations:
                dfs(dest_id, visited.copy(), path.copy())
            
            visited.remove(current_task_id)
            path.pop()
        
        # 从每个开始任务出发搜索
        for start_task in start_tasks:
            dfs(start_task.task_id, set(), [])
        
        return paths
    
    def split_into_flow_groups(self) -> List['TaskFlowGroup']:
        """
        将图谱拆分为多个任务流组
        
        每个路径形成一个独立的任务流组对象，自动处理任务的重复引用。
        
        :return: 任务流组列表
        """
        paths = self.extract_all_paths()
        flow_groups = []
        task_map = self.get_task_map()
        
        for idx, path in enumerate(paths):
            # 根据路径中的任务ID获取任务对象
            path_tasks = []
            for task_id in path:
                # 创建任务的深拷贝，避免修改原对象
                task_data = task_map[task_id].model_dump()
                task_cls = type(task_map[task_id])
                path_task = task_cls(**task_data)
                path_tasks.append(path_task)
            
            # 创建任务流组
            flow = TaskFlowGroup(
                flow_id=f"{self.graph_id}_FLOW{idx + 1:03d}",
                flow_name=f"{self.graph_name}_路径{idx + 1}",
                tasks=path_tasks,
                description=f"从任务图谱 {self.graph_id} 提取的第 {idx + 1} 条路径"
            )
            
            flow_groups.append(flow)
        
        return flow_groups
    
    def get_path_summary(self) -> List[Dict[str, Any]]:
        """
        获取所有路径的摘要信息
        
        :return: 路径摘要列表，包含路径ID、任务数量、起点、终点等信息
        """
        paths = self.extract_all_paths()
        task_map = self.get_task_map()
        summaries = []
        
        for idx, path in enumerate(paths):
            start_task = task_map[path[0]]
            end_task = task_map[path[-1]]
            
            summary = {
                "path_id": f"PATH{idx + 1:03d}",
                "total_tasks": len(path),
                "start_task_id": path[0],
                "start_task_name": start_task.task_name,
                "end_task_id": path[-1],
                "end_task_name": end_task.task_name,
                "end_task_type": end_task.task_type.value,
                "task_ids": path,
                "task_names": [task_map[t].task_name for t in path]
            }
            summaries.append(summary)
        
        return summaries
    
    def is_connected(self) -> bool:
        """
        检查图谱是否连通
        
        :return: 如果所有任务都能从至少一个StartTask到达，则返回True
        """
        paths = self.extract_all_paths()
        reachable_tasks = set()
        
        for path in paths:
            reachable_tasks.update(path)
        
        return reachable_tasks == {t.task_id for t in self.tasks}
    
    def find_paths_between(self, start_task_id: str, end_task_id: str) -> List[List[str]]:
        """
        查找两个任务之间的所有路径
        
        :param start_task_id: 起始任务ID
        :param end_task_id: 目标任务ID
        :return: 路径列表
        """
        paths = []
        task_map = self.get_task_map()
        
        if start_task_id not in task_map or end_task_id not in task_map:
            return paths
        
        def dfs(current_task_id: str, visited: set, path: List[str]) -> None:
            if current_task_id in visited:
                return
            
            visited.add(current_task_id)
            path.append(current_task_id)
            
            if current_task_id == end_task_id:
                paths.append(path.copy())
                visited.remove(current_task_id)
                path.pop()
                return
            
            current_task = task_map[current_task_id]
            for dest_id in current_task.task_destinations:
                dfs(dest_id, visited.copy(), path.copy())
            
            visited.remove(current_task_id)
            path.pop()
        
        dfs(start_task_id, set(), [])
        return paths
    
    def add_task(self, task: 'Task') -> None:
        """
        添加任务到图谱
        
        :param task: 要添加的任务对象
        """
        # 检查任务ID是否已存在
        if any(t.task_id == task.task_id for t in self.tasks):
            raise ValueError(f"任务ID {task.task_id} 已存在")
        
        self.tasks.append(task)
        
        # 重新验证图谱
        self.validate_graph()
    
    def remove_task(self, task_id: str) -> None:
        """
        从图谱中移除任务
        
        :param task_id: 要移除的任务ID
        :raises ValueError: 如果任务不存在或任务被其他任务引用
        """
        task_index = None
        for i, task in enumerate(self.tasks):
            if task.task_id == task_id:
                task_index = i
                break
        
        if task_index is None:
            raise ValueError(f"未找到任务: {task_id}")
        
        # 检查是否有其他任务引用该任务
        for task in self.tasks:
            if task.task_source == task_id:
                raise ValueError(f"任务 {task.task_id} 的 task_source 引用了该任务，无法移除")
            if task_id in task.task_destinations:
                raise ValueError(f"任务 {task.task_id} 的 task_destinations 引用了该任务，无法移除")
        
        del self.tasks[task_index]
    
    def update_task(self, task_id: str, **kwargs) -> None:
        """
        修改图谱中的指定任务
        
        :param task_id: 要修改的任务ID
        :param kwargs: 要修改的属性键值对
        :raises ValueError: 如果任务不存在
        """
        for task in self.tasks:
            if task.task_id == task_id:
                task.update_task(**kwargs)
                return
        
        raise ValueError(f"未找到任务: {task_id}")
    
    def get_graph_summary(self) -> Dict[str, Any]:
        """获取图谱摘要信息"""
        start_tasks = self.get_start_tasks()
        end_tasks = self.get_end_tasks()
        normal_tasks = self.get_normal_tasks()
        paths = self.extract_all_paths()
        
        return {
            "graph_id": self.graph_id,
            "graph_name": self.graph_name,
            "description": self.description,
            "total_tasks": len(self.tasks),
            "start_task_count": len(start_tasks),
            "start_task_ids": [t.task_id for t in start_tasks],
            "end_task_count": len(end_tasks),
            "end_task_ids": [t.task_id for t in end_tasks],
            "normal_task_count": len(normal_tasks),
            "path_count": len(paths),
            "is_connected": self.is_connected()
        }
    
    def to_json(self) -> str:
        """导出图谱为JSON格式"""
        return json.dumps(self.model_dump(mode='json'), ensure_ascii=False, indent=2)
    
    def __str__(self) -> str:
        """返回图谱的字符串表示"""
        return f"TaskGraph(graph_id={self.graph_id}, graph_name={self.graph_name}, tasks={len(self.tasks)}个, paths={len(self.extract_all_paths())}条)"


# 更新类型提示引用
TaskGraph.update_forward_refs()
