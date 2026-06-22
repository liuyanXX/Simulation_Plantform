"""任务服务测试

测试TaskService的所有方法。
"""

import unittest
import os
import sys
import logging
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from data_storage_services.sql_db_services.task_service import TaskService
from bo.task import Task, StartTask, EndTask, Priority, TaskType


class TestTaskService(unittest.TestCase):
    """任务服务测试类"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'test_task_service.log')
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        cls.logger = logging.getLogger(__name__)
        cls.logger.info("=" * 60)
        cls.logger.info("开始TaskService测试")
        cls.logger.info("=" * 60)

        test_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_data')
        os.makedirs(test_db_path, exist_ok=True)

        from . import ensure_tables_exist
        ensure_tables_exist(test_db_path, "test_task.db")

        cls.service = TaskService(
            db_type="sqlite",
            db_config={"db_path": test_db_path, "db_name": "test_task.db"}
        )

    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        cls.service.disconnect()
        test_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_data')
        db_file = os.path.join(test_db_path, "test_task.db")
        if os.path.exists(db_file):
            os.remove(db_file)
        cls.logger.info("TaskService测试完成")

    @staticmethod
    def _create_test_task(task_id, task_name, task_type=TaskType.NORMAL):
        """创建测试用任务对象"""
        now = datetime.now()
        if task_type == TaskType.START:
            return StartTask(
                task_id=task_id,
                task_name=task_name,
                expected_start_time=now,
                expected_end_time=now + timedelta(hours=1),
                content=f"任务内容: {task_name}",
                execute_role="SYSTEM",
                resource_consumption=0.0,
                priority=Priority.LOW,
                output_target_role="DEV",
                next_task_info={"next": "T002"},
                is_completed=False,
                task_source=None,
                task_destinations=["T002"],
                task_type=TaskType.START
            )
        elif task_type == TaskType.END:
            return EndTask(
                task_id=task_id,
                task_name=task_name,
                expected_start_time=now,
                expected_end_time=now + timedelta(hours=1),
                content=f"任务内容: {task_name}",
                execute_role="SYSTEM",
                resource_consumption=0.0,
                priority=Priority.LOW,
                output_target_role="",
                next_task_info=None,
                is_completed=False,
                task_source="T001",
                task_destinations=[],
                task_type=TaskType.END
            )
        else:
            return Task(
                task_id=task_id,
                task_name=task_name,
                expected_start_time=now,
                expected_end_time=now + timedelta(hours=8),
                content=f"任务内容: {task_name}",
                execute_role="DEV",
                resource_consumption=8.0,
                priority=Priority.MEDIUM,
                output_target_role="TEST",
                next_task_info={"next": "T003"},
                is_completed=False,
                task_source="T001",
                task_destinations=["T003"],
                task_type=TaskType.NORMAL
            )

    def setUp(self):
        """每个测试前的准备"""
        self.logger.info("\n" + "-" * 60)

    def test_01_create(self):
        """测试01: 创建任务"""
        self.logger.info("测试01: 创建任务")
        task = self._create_test_task("TASK_001", "测试任务")
        result = self.service.create(task)
        self.assertTrue(result)
        self.logger.info(f"创建任务成功: {task.task_id}")

    def test_02_read(self):
        """测试02: 读取任务"""
        self.logger.info("测试02: 读取任务")
        task = self._create_test_task("TASK_002", "读取测试任务")
        self.service.create(task)
        read_task = self.service.read("TASK_002")
        self.assertIsNotNone(read_task)
        self.assertEqual(read_task.task_name, "读取测试任务")
        self.logger.info(f"读取任务成功: {read_task.task_id}")

    def test_03_update(self):
        """测试03: 更新任务"""
        self.logger.info("测试03: 更新任务")
        task = self._create_test_task("TASK_003", "更新前任务")
        self.service.create(task)
        task.task_name = "更新后任务"
        task.is_completed = True
        count = self.service.update(task)
        self.assertEqual(count, 1)
        updated = self.service.read("TASK_003")
        self.assertEqual(updated.task_name, "更新后任务")
        self.assertTrue(updated.is_completed)
        self.logger.info("更新任务测试通过")

    def test_04_delete(self):
        """测试04: 删除任务"""
        self.logger.info("测试04: 删除任务")
        task = self._create_test_task("TASK_004", "待删除任务")
        self.service.create(task)
        count = self.service.delete("TASK_004")
        self.assertEqual(count, 1)
        deleted = self.service.read("TASK_004")
        self.assertIsNone(deleted)
        self.logger.info("删除任务测试通过")

    def test_05_exists(self):
        """测试05: 检查任务是否存在"""
        self.logger.info("测试05: 检查任务是否存在")
        task = self._create_test_task("TASK_005", "存在性测试任务")
        self.service.create(task)
        exists = self.service.exists("TASK_005")
        self.assertTrue(exists)
        not_exists = self.service.exists("TASK_NONEXISTENT")
        self.assertFalse(not_exists)
        self.logger.info("存在性检查测试通过")

    def test_06_count(self):
        """测试06: 统计任务数量"""
        self.logger.info("测试06: 统计任务数量")
        before_count = self.service.count()
        task = self._create_test_task("TASK_006", "统计测试任务")
        self.service.create(task)
        after_count = self.service.count()
        self.assertEqual(after_count, before_count + 1)
        self.logger.info(f"任务数量: {after_count}")

    def test_07_read_all(self):
        """测试07: 读取所有任务"""
        self.logger.info("测试07: 读取所有任务")
        tasks = self.service.read_all()
        self.assertIsInstance(tasks, list)
        self.logger.info(f"读取到 {len(tasks)} 个任务")

    def test_08_create_start_task(self):
        """测试08: 创建开始任务"""
        self.logger.info("测试08: 创建开始任务")
        task = self._create_test_task("TASK_START_001", "开始任务", TaskType.START)
        result = self.service.create(task)
        self.assertTrue(result)
        self.logger.info("创建开始任务测试通过")

    def test_09_create_end_task(self):
        """测试09: 创建结束任务"""
        self.logger.info("测试09: 创建结束任务")
        task = self._create_test_task("TASK_END_001", "结束任务", TaskType.END)
        result = self.service.create(task)
        self.assertTrue(result)
        self.logger.info("创建结束任务测试通过")

    def test_10_get_by_flow_group(self):
        """测试10: 按任务流组查询"""
        self.logger.info("测试10: 按任务流组查询")
        task = self._create_test_task("TASK_010", "流组测试任务")
        task._flow_group_id = "FLOW_001"
        self.service.create(task)
        tasks = self.service.get_by_flow_group("FLOW_001")
        self.assertIsInstance(tasks, list)
        self.logger.info(f"流组任务数量: {len(tasks)}")

    def test_11_get_by_graph(self):
        """测试11: 按任务图谱查询"""
        self.logger.info("测试11: 按任务图谱查询")
        task = self._create_test_task("TASK_011", "图谱测试任务")
        task._graph_id = "GRAPH_001"
        self.service.create(task)
        tasks = self.service.get_by_graph("GRAPH_001")
        self.assertIsInstance(tasks, list)
        self.logger.info(f"图谱任务数量: {len(tasks)}")

    def test_12_get_by_manifest(self):
        """测试12: 按任务清单查询"""
        self.logger.info("测试12: 按任务清单查询")
        task = self._create_test_task("TASK_012", "清单测试任务")
        task._manifest_id = "MANIFEST_001"
        self.service.create(task)
        tasks = self.service.get_by_manifest("MANIFEST_001")
        self.assertIsInstance(tasks, list)
        self.logger.info(f"清单任务数量: {len(tasks)}")

    def test_13_get_by_execute_role(self):
        """测试13: 按执行角色查询"""
        self.logger.info("测试13: 按执行角色查询")
        task = self._create_test_task("TASK_013", "角色测试任务")
        task.execute_role = "QA"
        self.service.create(task)
        tasks = self.service.get_by_execute_role("QA")
        self.assertIsInstance(tasks, list)
        self.logger.info(f"角色任务数量: {len(tasks)}")

    def test_14_get_pending_tasks(self):
        """测试14: 获取未完成任务"""
        self.logger.info("测试14: 获取未完成任务")
        task = self._create_test_task("TASK_014", "待完成任务")
        task.is_completed = False
        self.service.create(task)
        tasks = self.service.get_pending_tasks()
        self.assertIsInstance(tasks, list)
        self.logger.info(f"未完成任务数量: {len(tasks)}")

    def test_15_create_many(self):
        """测试15: 批量创建任务"""
        self.logger.info("测试15: 批量创建任务")
        tasks = [
            self._create_test_task(f"TASK_BATCH_{i}", f"批量任务{i}")
            for i in range(3)
        ]
        count = self.service.create_many(tasks)
        self.assertEqual(count, 3)
        self.logger.info(f"批量创建 {count} 个任务")


if __name__ == '__main__':
    unittest.main()