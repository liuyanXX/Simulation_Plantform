from pydantic import BaseModel, Field, field_validator, PrivateAttr
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import sys
import time
import threading
import os


def setup_logging():
    """
    配置日志系统
    
    配置根日志记录器，设置日志级别为 INFO，并添加两个处理器：
    1. 文件处理器：将日志写入 logs/ai_worker.log 文件
    2. 控制台处理器：将日志输出到标准输出
    
    :return: 配置好的日志记录器
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 使用绝对路径，基于脚本所在目录
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(base_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    file_handler = logging.FileHandler(os.path.join(log_dir, 'ai_worker.log'), mode='w', encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.INFO)
    
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    
    return logger


logger = setup_logging()


class AIWorker(BaseModel):
    """
    AI 员工模型
    
    表示仿真系统中的一个员工实体，具备任务处理能力，支持持续工作模式。
    
    :param employee_id: 员工工号，唯一标识
    :param name: 员工姓名
    :param department: 所属部门
    :param roles: 扮演的角色列表，用于任务分配校验
    :param daily_work_hours: 每天工作时长限制（小时），默认8小时
    :param task_list: 任务清单，存储待执行和已执行的任务
    :param current_time: 当前时间，用于任务排期计算
    
    :ivar _is_alive: 是否处于活跃状态（持续工作模式）
    :ivar _is_working: 是否正在执行任务
    :ivar _is_sleeping: 是否处于休眠状态（等待新任务）
    :ivar _wake_event: 唤醒事件，用于唤醒休眠中的员工
    :ivar _working_thread: 工作线程，执行持续工作循环
    :ivar _check_interval: 检查任务清单的间隔时间（秒），默认2秒
    """
    employee_id: str = Field(description="员工工号")
    name: str = Field(description="员工姓名")
    department: str = Field(description="所属部门")
    roles: List[str] = Field(description="扮演的角色列表")
    daily_work_hours: float = Field(default=8.0, description="每天工作时长限制（小时）")
    task_list: List[Task] = Field(default_factory=list, description="任务清单")
    current_time: datetime = Field(default_factory=datetime.now, description="当前时间")
    
    _is_alive: bool = PrivateAttr(default=False)
    _is_working: bool = PrivateAttr(default=False)
    _is_sleeping: bool = PrivateAttr(default=False)
    _wake_event: threading.Event = PrivateAttr(default_factory=threading.Event)
    _working_thread: Optional[threading.Thread] = PrivateAttr(default=None)
    _check_interval: float = PrivateAttr(default=2.0)
    _task_flow_groups: List['TaskFlowGroup'] = PrivateAttr(default_factory=list)

    @field_validator('daily_work_hours')
    @classmethod
    def daily_work_hours_must_be_positive(cls, v: float) -> float:
        """
        验证每日工作时长必须为正数
        
        :param v: 每日工作时长（小时）
        :return: 验证通过的工作时长
        :raises ValueError: 如果工作时长小于等于0
        """
        if v <= 0:
            raise ValueError('daily_work_hours must be positive')
        return v

    def add_task(self, task: Task) -> None:
        """
        向员工添加任务
        
        校验任务的执行角色是否与员工的角色匹配，如果匹配则将任务添加到任务清单。
        如果员工处于休眠状态且有新任务加入，会自动唤醒员工。
        
        :param task: 待添加的任务对象
        :raises ValueError: 如果员工不具备执行该任务的角色
        """
        if task.execute_role not in self.roles:
            raise ValueError(f"员工{self.name}不具备执行角色{task.execute_role}")
        self.task_list.append(task)
        logger.info(f"员工{self.name}添加任务: {task.task_id}")
        
        if self._is_alive and self._is_sleeping:
            self.wake_up()
    
    def set_task_flow_groups(self, flow_groups: List['TaskFlowGroup']) -> None:
        """
        设置任务流组列表
        
        用于在任务分派时，将任务流组信息传递给员工，以便在执行任务时
        能够根据 task_destinations 获取下一个任务。
        
        :param flow_groups: 任务流组列表
        """
        self._task_flow_groups = flow_groups
        logger.info(f"员工{self.name}已设置 {len(flow_groups)} 个任务流组")
    
    def _find_next_task(self, current_task: Task) -> Optional[Task]:
        """
        根据当前任务的 task_destinations 在任务流组中查找下一个任务
        
        :param current_task: 当前执行的任务
        :return: 下一个任务对象，如果不存在则返回 None
        """
        if not current_task.task_destinations:
            logger.info(f"任务 {current_task.task_id} 没有后续任务（task_destinations 为空）")
            return None
        
        # 遍历所有任务流组，查找下一个任务
        for flow_group in self._task_flow_groups:
            task_map = {task.task_id: task for task in flow_group.tasks}
            
            for dest_task_id in current_task.task_destinations:
                if dest_task_id in task_map:
                    next_task = task_map[dest_task_id]
                    logger.info(
                        f"找到后续任务: {dest_task_id} (执行角色: {next_task.execute_role})"
                    )
                    return next_task
        
        logger.warning(
            f"在任务流组中未找到任务 {current_task.task_id} 的后续任务 "
            f"(task_destinations: {current_task.task_destinations})"
        )
        return None

    def _get_priority_order(self, priority: Priority) -> int:
        """
        获取优先级排序值
        
        将优先级转换为数字，用于任务排序。值越小优先级越高。
        
        :param priority: 任务优先级
        :return: 优先级对应的排序值（HIGH=0, MEDIUM=1, LOW=2）
        """
        priority_order = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
        return priority_order[priority]

    def schedule_tasks(self) -> None:
        """
        对任务清单进行排期
        
        根据任务优先级和期望开始时间对任务进行排序，并为每个任务分配排期时间。
        排期从上午9点开始，考虑每日工作时长限制，跨天任务会自动安排到次日。
        """
        if not self.task_list:
            logger.info(f"员工{self.name}任务清单为空，无需排期")
            return

        sorted_tasks = sorted(
            self.task_list,
            key=lambda t: (self._get_priority_order(t.priority), t.expected_start_time)
        )

        current_schedule_time = self.current_time.replace(hour=9, minute=0, second=0, microsecond=0)
        
        for task in sorted_tasks:
            task.scheduled_start_time = current_schedule_time
            
            work_duration = timedelta(hours=task.resource_consumption)
            
            today_end_time = current_schedule_time.replace(hour=int(9 + self.daily_work_hours), minute=0, second=0, microsecond=0)
            remaining_today = (today_end_time - current_schedule_time).total_seconds() / 3600
            
            if task.resource_consumption <= remaining_today:
                task.scheduled_end_time = current_schedule_time + work_duration
                current_schedule_time = task.scheduled_end_time
            else:
                task.scheduled_end_time = current_schedule_time + work_duration
                current_schedule_time = task.scheduled_end_time
                
                if task.scheduled_end_time > today_end_time:
                    next_day = task.scheduled_end_time + timedelta(days=1)
                    current_schedule_time = next_day.replace(hour=9, minute=0, second=0, microsecond=0)

        self.task_list = sorted_tasks
        logger.info(f"员工{self.name}完成任务排期，共{len(self.task_list)}个任务")

    def think(self, task: Task) -> None:
        """
        思考任务（预处理阶段）
        
        在执行任务前，输出任务的详细信息，模拟员工理解任务的过程。
        
        :param task: 待思考的任务对象
        """
        logger.info(f"员工{self.name}开始思考任务: {task.task_id}")
        logger.info(f"任务内容: {task.content}")
        logger.info(f"执行角色: {task.execute_role}")
        logger.info(f"资源消耗: {task.resource_consumption}小时")
        logger.info(f"优先级: {task.priority}")
        logger.info(f"输出目标角色: {task.output_target_role}")
        logger.info(f"员工{self.name}思考完成，准备执行任务")

    def execute_task(self, task: Task, role_registry: Dict[str, 'AIWorker']) -> None:
        """
        执行单个任务
        
        执行任务的完整流程：
        1. 调用 think 方法进行任务分析
        2. 设置任务实际开始时间
        3. 模拟任务执行（通过睡眠模拟工作时长，最长5秒）
        4. 设置任务实际结束时间和完成状态
        5. 根据 task_destinations 和 output_target_role 查找并传递下一个任务给目标员工
        
        :param task: 待执行的任务对象
        :param role_registry: 角色注册表，用于查找目标角色对应的员工
        """
        self.think(task)
        
        task.actual_start_time = datetime.now()
        logger.info(f"员工{self.name}开始执行任务: {task.task_id}")
        
        simulation_duration = task.resource_consumption * 60 
        time.sleep(min(simulation_duration, 5))
        
        task.actual_end_time = datetime.now()
        task.is_completed = True
        
        logger.info(f"员工{self.name}完成任务: {task.task_id}")
        logger.info(f"任务执行信息:\n{task.to_json()}")
        
        # 传递后续任务
        self._dispatch_next_task(task, role_registry)
    
    def _dispatch_next_task(self, task: Task, role_registry: Dict[str, 'AIWorker']) -> None:
        """
        根据当前任务查找并传递下一个任务
        
        优先使用 next_task_info，如果不存在则根据 task_destinations
        和 output_target_role 在任务流组中查找下一个任务。
        
        对于 EndTask 或 HaltTask 类型的任务，不再传递后续任务。
        
        :param task: 当前执行完成的任务
        :param role_registry: 角色注册表，用于查找目标角色对应的员工
        """
        # 如果当前任务是终点任务，不再传递后续任务
        from .task import TaskType
        if hasattr(task, 'task_type') and task.task_type == TaskType.END:
            logger.info(f"任务 {task.task_id} 是终点任务，流程结束")
            return
        
        if hasattr(task, 'task_type') and task.task_type == TaskType.HALT:
            logger.info(f"任务 {task.task_id} 是中断任务，流程终止")
            return
        
        next_task = None
        
        # 优先使用 next_task_info
        if task.next_task_info:
            logger.info(f"使用 next_task_info 创建后续任务")
            next_task = Task(**task.next_task_info)
        else:
            # 根据 task_destinations 和 output_target_role 查找下一个任务
            next_task = self._find_next_task(task)
        
        if next_task:
            target_role = next_task.execute_role
            if target_role in role_registry:
                target_worker = role_registry[target_role]
                target_worker.add_task(next_task)
                logger.info(
                    f"员工{self.name}已将任务 {next_task.task_id} "
                    f"传递给 {target_worker.name}（角色: {target_role}）"
                )
            else:
                logger.warning(f"目标角色 {target_role} 不存在于角色注册表中，任务将不被执行")
        else:
            logger.info(f"任务 {task.task_id} 执行完成，无后续任务需要传递")

    def work(self, role_registry: Dict[str, 'AIWorker']) -> None:
        """
        执行一轮工作
        
        对任务清单进行排期，然后依次执行所有未完成的任务。
        
        :param role_registry: 角色注册表，用于任务执行时的任务传递
        """
        self.schedule_tasks()
        
        for task in self.task_list:
            if not task.is_completed:
                self.execute_task(task, role_registry)
            else:
                logger.info(f"任务{task.task_id}已完成，跳过执行")

    def get_task_status(self) -> List[Dict[str, Any]]:
        """
        获取所有任务的状态列表
        
        将任务清单转换为JSON可序列化的字典列表，便于外部查看任务状态。
        
        :return: 任务状态字典列表
        """
        return [task.model_dump(mode='json') for task in self.task_list]
    
    def has_pending_tasks(self) -> bool:
        """
        检查是否有未完成的任务
        
        :return: 如果存在未完成的任务返回True，否则返回False
        """
        return any(not task.is_completed for task in self.task_list)
    
    def wake_up(self) -> None:
        """
        唤醒休眠中的员工
        
        设置唤醒事件，使员工从休眠状态中醒来，准备处理新任务。
        """
        if self._is_sleeping:
            self._wake_event.set()
            logger.info(f"员工{self.name}已被唤醒")
    
    def sleep(self) -> None:
        """
        进入休眠状态
        
        将员工置于休眠状态，等待新任务的到来。
        当有新任务添加时，会通过 wake_up 方法唤醒。
        """
        self._is_sleeping = True
        logger.info(f"员工{self.name}进入休眠状态，等待新任务...")
        self._wake_event.wait()
        self._wake_event.clear()
        self._is_sleeping = False
        logger.info(f"员工{self.name}从休眠中醒来")
    
    def working(self, role_registry: Dict[str, 'AIWorker'], check_interval: float = 2.0) -> None:
        """
        启动持续工作状态
        
        创建并启动一个守护线程，持续检查任务清单并执行任务。
        工作循环流程：
        1. 检查是否有待办任务
        2. 如果有，执行 work 方法处理所有任务
        3. 如果没有，进入休眠状态等待新任务
        4. 循环执行以上步骤直到停止工作
        
        :param role_registry: 角色注册表，用于任务执行和任务传递
        :param check_interval: 检查任务清单的间隔时间（秒），默认2秒
        """
        if self._is_alive:
            logger.info(f"员工{self.name}已经处于工作状态")
            return
        
        self._is_alive = True
        self._check_interval = check_interval
        
        def working_loop():
            while self._is_alive:
                if self.has_pending_tasks():
                    self._is_working = True
                    logger.info(f"员工{self.name}检测到待办任务，开始工作")
                    self.work(role_registry)
                    self._is_working = False
                    logger.info(f"员工{self.name}本轮工作完成")
                
                if self._is_alive and not self.has_pending_tasks():
                    self.sleep()
                
                time.sleep(self._check_interval)
        
        self._working_thread = threading.Thread(target=working_loop, daemon=True)
        self._working_thread.start()
        logger.info(f"员工{self.name}已启动持续工作状态")
    
    def stop_working(self) -> None:
        """
        停止持续工作状态
        
        设置 _is_alive 标志为 False，唤醒休眠中的员工，
        并等待工作线程结束（最多等待5秒）。
        """
        self._is_alive = False
        self.wake_up()
        
        if self._working_thread:
            self._working_thread.join(timeout=5)
            self._working_thread = None
        
        logger.info(f"员工{self.name}已停止工作")

    def __str__(self) -> str:
        """
        返回员工的字符串表示
        
        :return: 包含员工工号、姓名、部门和角色的字符串
        """
        return f"AIWorker(工号={self.employee_id}, 姓名={self.name}, 部门={self.department}, 角色={self.roles})"


# 延迟导入避免循环依赖，然后更新类型提示引用
from .task import Task, Priority
from .task_flow_group import TaskFlowGroup
AIWorker.update_forward_refs()


if __name__ == "__main__":
    worker1 = AIWorker(
        employee_id="EMP001",
        name="张三",
        department="研发部",
        roles=["DEV", "TEST"],
        daily_work_hours=8.0
    )

    worker2 = AIWorker(
        employee_id="EMP002",
        name="李四",
        department="测试部",
        roles=["TEST", "QA"],
        daily_work_hours=8.0
    )

    role_registry = {
        "DEV": worker1,
        "TEST": worker2,
        "QA": worker2
    }

    print("=== 测试持续工作模式 ===")
    print("启动张三和李四的持续工作状态...")
    worker1.working(role_registry, check_interval=2.0)
    worker2.working(role_registry, check_interval=2.0)
    
    time.sleep(1)
    
    now = datetime.now()
    task1 = Task(
        task_id="T001",
        task_name="开发用户登录模块",
        expected_start_time=now,
        expected_end_time=now + timedelta(hours=4),
        content="开发用户登录模块",
        execute_role="DEV",
        resource_consumption=0.5,
        priority=Priority.HIGH,
        output_target_role="TEST",
        next_task_info={
            "task_id": "T002",
            "task_name": "测试用户登录模块",
            "expected_start_time": now.isoformat(),
            "expected_end_time": (now + timedelta(hours=2)).isoformat(),
            "content": "测试用户登录模块",
            "execute_role": "TEST",
            "resource_consumption": 0.5,
            "priority": "high",
            "output_target_role": "QA"
        }
    )
    
    print("\n添加第一个任务给张三...")
    worker1.add_task(task1)
    
    time.sleep(3)
    
    task2 = Task(
        task_id="T003",
        task_name="开发数据报表模块",
        expected_start_time=now,
        expected_end_time=now + timedelta(hours=6),
        content="开发数据报表模块",
        execute_role="DEV",
        resource_consumption=0.5,
        priority=Priority.MEDIUM,
        output_target_role="TEST"
    )
    
    print("\n添加第二个任务给张三...")
    worker1.add_task(task2)
    
    time.sleep(3)
    
    print("\n=== 停止工作 ===")
    worker1.stop_working()
    worker2.stop_working()
    
    print("\n张三的任务列表:")
    for task in worker1.task_list:
        print(task.to_json())
    
    print("\n李四的任务列表:")
    for task in worker2.task_list:
        print(task.to_json())
