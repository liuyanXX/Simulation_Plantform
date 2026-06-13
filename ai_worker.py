from pydantic import BaseModel, Field, field_validator, PrivateAttr
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import sys
import time
import threading
from task import Task, Priority


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    file_handler = logging.FileHandler('ai_worker.log', mode='w', encoding='utf-8')
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

    @field_validator('daily_work_hours')
    @classmethod
    def daily_work_hours_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('daily_work_hours must be positive')
        return v

    def add_task(self, task: Task) -> None:
        if task.execute_role not in self.roles:
            raise ValueError(f"员工{self.name}不具备执行角色{task.execute_role}")
        self.task_list.append(task)
        logger.info(f"员工{self.name}添加任务: {task.task_id}")
        
        if self._is_alive and self._is_sleeping:
            self.wake_up()

    def _get_priority_order(self, priority: Priority) -> int:
        priority_order = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
        return priority_order[priority]

    def schedule_tasks(self) -> None:
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
        logger.info(f"员工{self.name}开始思考任务: {task.task_id}")
        logger.info(f"任务内容: {task.content}")
        logger.info(f"执行角色: {task.execute_role}")
        logger.info(f"资源消耗: {task.resource_consumption}小时")
        logger.info(f"优先级: {task.priority}")
        logger.info(f"输出目标角色: {task.output_target_role}")
        logger.info(f"员工{self.name}思考完成，准备执行任务")

    def execute_task(self, task: Task, role_registry: Dict[str, 'AIWorker']) -> None:
        self.think(task)
        
        task.actual_start_time = datetime.now()
        logger.info(f"员工{self.name}开始执行任务: {task.task_id}")
        
        import time
        simulation_duration = task.resource_consumption * 60 
        time.sleep(min(simulation_duration, 5))
        
        task.actual_end_time = datetime.now()
        task.is_completed = True
        
        logger.info(f"员工{self.name}完成任务: {task.task_id}")
        logger.info(f"任务执行信息:\n{task.to_json()}")
        
        if task.output_target_role in role_registry:
            target_worker = role_registry[task.output_target_role]
            if task.next_task_info:
                next_task = Task(**task.next_task_info)
                target_worker.add_task(next_task)
                logger.info(f"员工{self.name}已将后续任务传递给{target_worker.name}")
        else:
            logger.warning(f"目标角色{task.output_target_role}不存在于角色注册表中")

    def work(self, role_registry: Dict[str, 'AIWorker']) -> None:
        self.schedule_tasks()
        
        for task in self.task_list:
            if not task.is_completed:
                self.execute_task(task, role_registry)
            else:
                logger.info(f"任务{task.task_id}已完成，跳过执行")

    def get_task_status(self) -> List[Dict[str, Any]]:
        return [task.model_dump(mode='json') for task in self.task_list]
    
    def has_pending_tasks(self) -> bool:
        """检查是否有未完成的任务"""
        return any(not task.is_completed for task in self.task_list)
    
    def wake_up(self) -> None:
        """唤醒休眠中的员工"""
        if self._is_sleeping:
            self._wake_event.set()
            logger.info(f"员工{self.name}已被唤醒")
    
    def sleep(self) -> None:
        """进入休眠状态，等待新任务"""
        self._is_sleeping = True
        logger.info(f"员工{self.name}进入休眠状态，等待新任务...")
        self._wake_event.wait()
        self._wake_event.clear()
        self._is_sleeping = False
        logger.info(f"员工{self.name}从休眠中醒来")
    
    def working(self, role_registry: Dict[str, 'AIWorker'], check_interval: float = 2.0) -> None:
        """
        启动持续工作状态
        
        :param role_registry: 角色注册表
        :param check_interval: 检查任务清单的间隔时间（秒）
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
        """停止持续工作状态"""
        self._is_alive = False
        self.wake_up()
        
        if self._working_thread:
            self._working_thread.join(timeout=5)
            self._working_thread = None
        
        logger.info(f"员工{self.name}已停止工作")

    def __str__(self) -> str:
        return f"AIWorker(工号={self.employee_id}, 姓名={self.name}, 部门={self.department}, 角色={self.roles})"


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
        expected_start_time=now,
        expected_end_time=now + timedelta(hours=4),
        content="开发用户登录模块",
        execute_role="DEV",
        resource_consumption=0.5,
        priority=Priority.HIGH,
        output_target_role="TEST",
        next_task_info={
            "task_id": "T002",
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
