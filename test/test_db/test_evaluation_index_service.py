"""评价指标服务测试

测试EvaluationIndexService的所有方法。
"""

import unittest
import os
import sys
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from data_storage_services.sql_db_services.evaluation_index_service import EvaluationIndexService


class TestEvaluationIndexService(unittest.TestCase):
    """评价指标服务测试类"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'test_evaluation_index_service.log')
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
        cls.logger.info("开始EvaluationIndexService测试")
        cls.logger.info("=" * 60)

        test_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_data')
        os.makedirs(test_db_path, exist_ok=True)

        from . import ensure_tables_exist
        ensure_tables_exist(test_db_path, "test_eval_index.db")

        cls.service = EvaluationIndexService(
            db_type="sqlite",
            db_config={"db_path": test_db_path, "db_name": "test_eval_index.db"}
        )

    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        cls.service.disconnect()
        test_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_data')
        db_file = os.path.join(test_db_path, "test_eval_index.db")
        if os.path.exists(db_file):
            os.remove(db_file)
        cls.logger.info("EvaluationIndexService测试完成")

    def _create_test_index(self, index_id, name, description="测试指标描述"):
        """创建测试用评价指标对象"""
        return EvaluationIndex(
            index_id=index_id,
            name=name,
            description=description,
            evaluation_method="测试方法",
            agent_ids=["agent1", "agent2"],
            index_type=IndexType.COMPLETENESS,
            index_level=IndexLevel.LEVEL_1,
            parent_id=None,
            weight=1.0,
            score_range=(0, 100),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True
        )

    def setUp(self):
        """每个测试前的准备"""
        self.logger.info("\n" + "-" * 60)

    def test_01_create(self):
        """测试01: 创建评价指标"""
        self.logger.info("测试01: 创建评价指标")
        index = self._create_test_index("INDEX_001", "测试指标")
        result = self.service.create(index)
        self.assertTrue(result)
        self.logger.info(f"创建评价指标成功: {index.index_id}")

    def test_02_read(self):
        """测试02: 读取评价指标"""
        self.logger.info("测试02: 读取评价指标")
        index = self._create_test_index("INDEX_002", "读取测试指标")
        self.service.create(index)
        read_index = self.service.read("INDEX_002")
        self.assertIsNotNone(read_index)
        self.assertEqual(read_index.name, "读取测试指标")
        self.logger.info(f"读取评价指标成功: {read_index.index_id}")

    def test_03_update(self):
        """测试03: 更新评价指标"""
        self.logger.info("测试03: 更新评价指标")
        index = self._create_test_index("INDEX_003", "更新前指标")
        self.service.create(index)
        index.name = "更新后指标"
        index.weight = 2.0
        count = self.service.update(index)
        self.assertEqual(count, 1)
        updated = self.service.read("INDEX_003")
        self.assertEqual(updated.name, "更新后指标")
        self.logger.info("更新评价指标测试通过")

    def test_04_delete(self):
        """测试04: 删除评价指标"""
        self.logger.info("测试04: 删除评价指标")
        index = self._create_test_index("INDEX_004", "待删除指标")
        self.service.create(index)
        count = self.service.delete("INDEX_004")
        self.assertEqual(count, 1)
        deleted = self.service.read("INDEX_004")
        self.assertIsNone(deleted)
        self.logger.info("删除评价指标测试通过")

    def test_05_exists(self):
        """测试05: 检查评价指标是否存在"""
        self.logger.info("测试05: 检查评价指标是否存在")
        index = self._create_test_index("INDEX_005", "存在性测试指标")
        self.service.create(index)
        exists = self.service.exists("INDEX_005")
        self.assertTrue(exists)
        not_exists = self.service.exists("INDEX_NONEXISTENT")
        self.assertFalse(not_exists)
        self.logger.info("存在性检查测试通过")

    def test_06_count(self):
        """测试06: 统计评价指标数量"""
        self.logger.info("测试06: 统计评价指标数量")
        before_count = self.service.count()
        index = self._create_test_index("INDEX_006", "统计测试指标")
        self.service.create(index)
        after_count = self.service.count()
        self.assertEqual(after_count, before_count + 1)
        self.logger.info(f"评价指标数量: {after_count}")

    def test_07_read_all(self):
        """测试07: 读取所有评价指标"""
        self.logger.info("测试07: 读取所有评价指标")
        indices = self.service.read_all()
        self.assertIsInstance(indices, list)
        self.logger.info(f"读取到 {len(indices)} 个评价指标")

    def test_08_get_by_type(self):
        """测试08: 按类型查询评价指标"""
        self.logger.info("测试08: 按类型查询评价指标")
        index = self._create_test_index("IDX_TEST_008", "类型测试指标")
        index.index_type = IndexType.RATIONALITY
        self.service.create(index)
        indices = self.service.get_by_type(IndexType.RATIONALITY)
        self.assertIsInstance(indices, list)
        self.logger.info(f"类型评价指标数量: {len(indices)}")

    def test_09_get_by_level(self):
        """测试09: 按层级查询评价指标"""
        self.logger.info("测试09: 按层级查询评价指标")
        index = self._create_test_index("IDX_TEST_009", "层级测试指标")
        index.index_level = IndexLevel.LEVEL_2
        self.service.create(index)
        indices = self.service.get_by_level(IndexLevel.LEVEL_2)
        self.assertIsInstance(indices, list)
        self.logger.info(f"层级评价指标数量: {len(indices)}")

    def test_10_get_active_indices(self):
        """测试10: 获取激活的评价指标"""
        self.logger.info("测试10: 获取激活的评价指标")
        index = self._create_test_index("INDEX_010", "激活测试指标")
        index.is_active = True
        self.service.create(index)
        indices = self.service.get_active_indices()
        self.assertIsInstance(indices, list)
        self.logger.info(f"激活评价指标数量: {len(indices)}")

    def test_11_get_children(self):
        """测试11: 获取子指标"""
        self.logger.info("测试11: 获取子指标")
        parent_index = self._create_test_index("INDEX_011_PARENT", "父指标")
        self.service.create(parent_index)
        child_index = self._create_test_index("INDEX_011_CHILD", "子指标")
        child_index.parent_id = "INDEX_011_PARENT"
        self.service.create(child_index)
        children = self.service.get_children("INDEX_011_PARENT")
        self.assertIsInstance(children, list)
        self.logger.info(f"子指标数量: {len(children)}")

    def test_12_create_many(self):
        """测试12: 批量创建评价指标"""
        self.logger.info("测试12: 批量创建评价指标")
        indices = [
            self._create_test_index(f"INDEX_BATCH_{i}", f"批量指标{i}")
            for i in range(3)
        ]
        count = self.service.create_many(indices)
        self.assertEqual(count, 3)
        self.logger.info(f"批量创建 {count} 个评价指标")


if __name__ == '__main__':
    unittest.main()