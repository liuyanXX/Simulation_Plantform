"""任务图谱模块

定义 TasksGraph 类，用于表示有向图结构的任务图谱。
"""
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict, Any
import json

# 循环引用需要延迟导入
from .task import Task, StartTask, EndTask, HaltTask


class TasksGraph(BaseModel):
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
        graph = TasksGraph(
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
    def validate_graph(self) -> 'TasksGraph':
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
        # 延迟导入避免循环依赖
        from .task_flow_group import TaskFlowGroup
        
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
    
    def save_to_file(self, file_path: str) -> None:
        """
        保存图谱到文件
        
        :param file_path: 文件路径
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
    
    @classmethod
    def from_task_manifest(cls, manifest: 'TaskManifest') -> 'TasksGraph':
        """
        从任务清单对象解析生成任务图谱
        
        将任务清单中的所有任务流组合并为一个任务图谱，建立任务之间的关联关系。
        
        :param manifest: TaskManifest 对象
        :return: TasksGraph 对象
        """
        # 收集所有任务
        all_tasks = []
        task_id_map = {}
        
        for flow_group in manifest.flow_groups:
            for task in flow_group.tasks:
                # 创建任务的深拷贝，避免修改原对象
                task_data = task.model_dump()
                task_cls = type(task)
                new_task = task_cls(**task_data)
                
                # 确保任务ID唯一
                if new_task.task_id not in task_id_map:
                    task_id_map[new_task.task_id] = new_task
                    all_tasks.append(new_task)
        
        # 创建图谱
        graph = cls(
            graph_id=f"GRAPH_{manifest.manifest_id}",
            graph_name=f"{manifest.manifest_name}_图谱",
            tasks=all_tasks,
            description=f"从任务清单 {manifest.manifest_id} 生成的任务图谱"
        )
        
        return graph
    
    @classmethod
    def from_task_manifest_file(cls, file_path: str) -> 'TasksGraph':
        """
        从任务清单文件解析生成任务图谱
        
        :param file_path: 任务清单文件路径
        :return: TasksGraph 对象
        """
        from task_manifest import TaskManifest
        
        manifest = TaskManifest.load_from_file(file_path)
        return cls.from_task_manifest(manifest)
    
    def __str__(self) -> str:
        """返回图谱的字符串表示"""
        return f"TasksGraph(graph_id={self.graph_id}, graph_name={self.graph_name}, tasks={len(self.tasks)}个, paths={len(self.extract_all_paths())}条)"


# 更新类型提示引用
TasksGraph.update_forward_refs()