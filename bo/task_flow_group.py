"""任务流组模块

定义 TaskFlowGroup 类，用于管理一组串行执行的任务。
"""
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict, Any
import json

# 循环引用需要延迟导入
from .task import Task, StartTask, EndTask, HaltTask


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
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TaskFlowGroup':
        """
        从JSON字符串加载任务流组
        
        :param json_str: JSON格式的字符串
        :return: TaskFlowGroup 对象
        """
        from .task import Task, StartTask, EndTask, HaltTask
        
        data = json.loads(json_str)
        
        # 根据 task_type 字段创建正确的任务类型对象
        if 'tasks' in data:
            processed_tasks = []
            for task_data in data['tasks']:
                task_type = task_data.get('task_type', 'normal')
                if task_type == 'start':
                    task = StartTask(**task_data)
                elif task_type == 'end':
                    task = EndTask(**task_data)
                elif task_type == 'halt':
                    task = HaltTask(**task_data)
                else:
                    task = Task(**task_data)
                processed_tasks.append(task)
            data['tasks'] = processed_tasks
        
        return cls(**data)


# 更新类型提示引用
TaskFlowGroup.model_rebuild()
