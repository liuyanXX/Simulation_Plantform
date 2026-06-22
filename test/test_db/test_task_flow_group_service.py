"""任务流组服务测试

测试TaskFlowGroupService的所有方法。
"""

import unittest
import os
import sys
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from data_storage_services.sql_db_services.task_flow_group_service import TaskFlowGroupService
from bo.task_flow_group import TaskFlowGroup


class TestTaskFlowGroupService(unittest.TestCase):
    """任务流组服务测试类"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'test_task_flow_group_service.log')
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
        cls.logger.info("开始TaskFlowGroupService测试")
        cls.logger.info("=" * 60)

        test_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_data')
        os.makedirs(test_db_path, exist_ok=True)

        from . import ensure_tables_exist
        ensure_tables_exist(test_db_path, "test_flow_group.db")

        cls.service = TaskFlowGroupService(
            db_type="sqlite",
            db_config={"db_path": test_db_path, "db_name": "test_flow_group.db"}
        )

    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        cls.service.disconnect()
        test_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_data')
        db_file = os.path.join(test_db_path, "test_flow_group.db")
        if os.path.exists(db_file):
            os.remove(db_file)
        cls.logger.info("TaskFlowGroupService测试完成")

    @staticmethod
    def _create_test_flow_group(flow_id, flow_name, manifest_id=None):
        """创建测试用任务流组对象"""
        return TaskFlowGroup(
            flow_id=flow_id,
            flow_name=flow_name,
            description="测试流组描述",
            manifest_id=manifest_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    def setUp(self):
        """每个测试前的准备"""
        self.logger.info("\n" + "-" * 60)

    def test_01_create(self):
        """测试01: 创建任务流组"""
        self.logger.info("测试01: 创建任务流组")
        flow_group = self._create_test_flow_group("FLOW_001", "测试流组")
        result = self.service.create(flow_group)
        self.assertTrue(result)
        self.logger.info(f"创建任务流组成功: {flow_group.flow_id}")

    def test_02_read(self):
        """测试02: 读取任务流组"""
        self.logger.info("测试02: 读取任务流组")
        flow_group = self._create_test_flow_group("FLOW_002", "读取测试流组")
        self.service.create(flow_group)
        read_flow_group = self.service.read("FLOW_002")
        self.assertIsNotNone(read_flow_group)
        self.assertEqual(read_flow_group.flow_name, "读取测试流组")
        self.logger.info(f"读取任务流组成功: {read_flow_group.flow_id}")

    def test_03_update(self):
        """测试03: 更新任务流组"""
        self.logger.info("测试03: 更新任务流组")
        flow_group = self._create_test_flow_group("FLOW_003", "更新前流组")
        self.service.create(flow_group)
        flow_group.flow_name = "更新后流组"
        count = self.service.update(flow_group)
        self.assertEqual(count, 1)
        updated = self.service.read("FLOW_003")
        self.assertEqual(updated.flow_name, "更新后流组")
        self.logger.info("更新任务流组测试通过")

    def test_04_delete(self):
        """测试04: 删除任务流组"""
        self.logger.info("测试04: 删除任务流组")
        flow_group = self._create_test_flow_group("FLOW_004", "待删除流组")
        self.service.create(flow_group)
        count = self.service.delete("FLOW_004")
        self.assertEqual(count, 1)
        deleted = self.service.read("FLOW_004")
        self.assertIsNone(deleted)
        self.logger.info("删除任务流组测试通过")

    def test_05_exists(self):
        """测试05: 检查任务流组是否存在"""
        self.logger.info("测试05: 检查任务流组是否存在")
        flow_group = self._create_test_flow_group("FLOW_005", "存在性测试流组")
        self.service.create(flow_group)
        exists = self.service.exists("FLOW_005")
        self.assertTrue(exists)
        not_exists = self.service.exists("FLOW_NONEXISTENT")
        self.assertFalse(not_exists)
        self.logger.info("存在性检查测试通过")

    def test_06_count(self):
        """测试06: 统计任务流组数量"""
        self.logger.info("测试06: 统计任务流组数量")
        before_count = self.service.count()
        flow_group = self._create_test_flow_group("FLOW_006", "统计测试流组")
        self.service.create(flow_group)
        after_count = self.service.count()
        self.assertEqual(after_count, before_count + 1)
        self.logger.info(f"任务流组数量: {after_count}")

    def test_07_read_all(self):
        """测试07: 读取所有任务流组"""
        self.logger.info("测试07: 读取所有任务流组")
        flow_groups = self.service.read_all()
        self.assertIsInstance(flow_groups, list)
        self.logger.info(f"读取到 {len(flow_groups)} 个任务流组")

    def test_08_get_by_manifest(self):
        """测试08: 按任务清单查询任务流组"""
        self.logger.info("测试08: 按任务清单查询任务流组")
        flow_group = self._create_test_flow_group("FLOW_008", "清单测试流组")
        flow_group.manifest_id = "MANIFEST_001"
        self.service.create(flow_group)
        flow_groups = self.service.get_by_manifest("MANIFEST_001")
        self.assertIsInstance(flow_groups, list)
        self.logger.info(f"清单任务流组数量: {len(flow_groups)}")

    def test_09_create_many(self):
        """测试09: 批量创建任务流组"""
        self.logger.info("测试09: 批量创建任务流组")
        flow_groups = [
            self._create_test_flow_group(f"FLOW_BATCH_{i}", f"批量流组{i}")
            for i in range(3)
        ]
        count = self.service.create_many(flow_groups)
        self.assertEqual(count, 3)
        self.logger.info(f"批量创建 {count} 个任务流组")


if __name__ == '__main__':
    unittest.main()