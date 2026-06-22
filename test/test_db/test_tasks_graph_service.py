"""任务图谱服务测试

测试TasksGraphService的所有方法。
"""

import unittest
import os
import sys
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from data_storage_services.sql_db_services.tasks_graph_service import TasksGraphService
from bo.tasks_graph import TasksGraph


class TestTasksGraphService(unittest.TestCase):
    """任务图谱服务测试类"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'test_tasks_graph_service.log')
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
        cls.logger.info("开始TasksGraphService测试")
        cls.logger.info("=" * 60)

        test_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_data')
        os.makedirs(test_db_path, exist_ok=True)

        from . import ensure_tables_exist
        ensure_tables_exist(test_db_path, "test_graph.db")

        cls.service = TasksGraphService(
            db_type="sqlite",
            db_config={"db_path": test_db_path, "db_name": "test_graph.db"}
        )

    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        cls.service.disconnect()
        test_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_data')
        db_file = os.path.join(test_db_path, "test_graph.db")
        if os.path.exists(db_file):
            os.remove(db_file)
        cls.logger.info("TasksGraphService测试完成")

    @staticmethod
    def _create_test_graph(graph_id, graph_name, manifest_id=None):
        """创建测试用任务图谱对象"""
        return TasksGraph(
            graph_id=graph_id,
            graph_name=graph_name,
            description="测试图谱描述",
            manifest_id=manifest_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    def setUp(self):
        """每个测试前的准备"""
        self.logger.info("\n" + "-" * 60)

    def test_01_create(self):
        """测试01: 创建任务图谱"""
        self.logger.info("测试01: 创建任务图谱")
        graph = self._create_test_graph("GRAPH_001", "测试图谱")
        result = self.service.create(graph)
        self.assertTrue(result)
        self.logger.info(f"创建任务图谱成功: {graph.graph_id}")

    def test_02_read(self):
        """测试02: 读取任务图谱"""
        self.logger.info("测试02: 读取任务图谱")
        graph = self._create_test_graph("GRAPH_002", "读取测试图谱")
        self.service.create(graph)
        read_graph = self.service.read("GRAPH_002")
        self.assertIsNotNone(read_graph)
        self.assertEqual(read_graph.graph_name, "读取测试图谱")
        self.logger.info(f"读取任务图谱成功: {read_graph.graph_id}")

    def test_03_update(self):
        """测试03: 更新任务图谱"""
        self.logger.info("测试03: 更新任务图谱")
        graph = self._create_test_graph("GRAPH_003", "更新前图谱")
        self.service.create(graph)
        graph.graph_name = "更新后图谱"
        count = self.service.update(graph)
        self.assertEqual(count, 1)
        updated = self.service.read("GRAPH_003")
        self.assertEqual(updated.graph_name, "更新后图谱")
        self.logger.info("更新任务图谱测试通过")

    def test_04_delete(self):
        """测试04: 删除任务图谱"""
        self.logger.info("测试04: 删除任务图谱")
        graph = self._create_test_graph("GRAPH_004", "待删除图谱")
        self.service.create(graph)
        count = self.service.delete("GRAPH_004")
        self.assertEqual(count, 1)
        deleted = self.service.read("GRAPH_004")
        self.assertIsNone(deleted)
        self.logger.info("删除任务图谱测试通过")

    def test_05_exists(self):
        """测试05: 检查任务图谱是否存在"""
        self.logger.info("测试05: 检查任务图谱是否存在")
        graph = self._create_test_graph("GRAPH_005", "存在性测试图谱")
        self.service.create(graph)
        exists = self.service.exists("GRAPH_005")
        self.assertTrue(exists)
        not_exists = self.service.exists("GRAPH_NONEXISTENT")
        self.assertFalse(not_exists)
        self.logger.info("存在性检查测试通过")

    def test_06_count(self):
        """测试06: 统计任务图谱数量"""
        self.logger.info("测试06: 统计任务图谱数量")
        before_count = self.service.count()
        graph = self._create_test_graph("GRAPH_006", "统计测试图谱")
        self.service.create(graph)
        after_count = self.service.count()
        self.assertEqual(after_count, before_count + 1)
        self.logger.info(f"任务图谱数量: {after_count}")

    def test_07_read_all(self):
        """测试07: 读取所有任务图谱"""
        self.logger.info("测试07: 读取所有任务图谱")
        graphs = self.service.read_all()
        self.assertIsInstance(graphs, list)
        self.logger.info(f"读取到 {len(graphs)} 个任务图谱")

    def test_08_get_by_manifest(self):
        """测试08: 按任务清单查询任务图谱"""
        self.logger.info("测试08: 按任务清单查询任务图谱")
        graph = self._create_test_graph("GRAPH_008", "清单测试图谱")
        graph.manifest_id = "MANIFEST_001"
        self.service.create(graph)
        graphs = self.service.get_by_manifest("MANIFEST_001")
        self.assertIsInstance(graphs, list)
        self.logger.info(f"清单任务图谱数量: {len(graphs)}")

    def test_09_create_many(self):
        """测试09: 批量创建任务图谱"""
        self.logger.info("测试09: 批量创建任务图谱")
        graphs = [
            self._create_test_graph(f"GRAPH_BATCH_{i}", f"批量图谱{i}")
            for i in range(3)
        ]
        count = self.service.create_many(graphs)
        self.assertEqual(count, 3)
        self.logger.info(f"批量创建 {count} 个任务图谱")


if __name__ == '__main__':
    unittest.main()