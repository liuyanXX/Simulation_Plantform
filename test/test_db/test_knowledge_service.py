"""知识服务测试

测试KnowledgeService的所有方法。
"""

import unittest
import os
import sys
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from data_storage_services.sql_db_services.knowledge_service import KnowledgeService
from knowledge_management.models import Knowledge


class TestKnowledgeService(unittest.TestCase):
    """知识服务测试类"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'test_knowledge_service.log')
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
        cls.logger.info("开始KnowledgeService测试")
        cls.logger.info("=" * 60)

        test_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_data')
        os.makedirs(test_db_path, exist_ok=True)

        from . import ensure_tables_exist
        ensure_tables_exist(test_db_path, "test_knowledge.db")

        cls.service = KnowledgeService(
            db_type="sqlite",
            db_config={"db_path": test_db_path, "db_name": "test_knowledge.db"}
        )

    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        cls.service.disconnect()
        test_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_data')
        db_file = os.path.join(test_db_path, "test_knowledge.db")
        if os.path.exists(db_file):
            os.remove(db_file)
        cls.logger.info("KnowledgeService测试完成")

    def _create_test_knowledge(self, knowledge_id, title):
        """创建测试用知识对象"""
        return Knowledge(
            knowledge_id=knowledge_id,
            title=title,
            summary=f"{title}的摘要",
            content=f"{title}的详细内容",
            index_ids=["IDX_COMP_001"],
            tags=["tag1", "tag2"],
            category="evaluation",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True
        )

    def setUp(self):
        """每个测试前的准备"""
        self.logger.info("\n" + "-" * 60)

    def test_01_create(self):
        """测试01: 创建知识"""
        self.logger.info("测试01: 创建知识")
        knowledge = self._create_test_knowledge("KNOW_TEST_001", "测试知识")
        result = self.service.create(knowledge)
        self.assertTrue(result)
        self.logger.info(f"创建知识成功: {knowledge.knowledge_id}")

    def test_02_read(self):
        """测试02: 读取知识"""
        self.logger.info("测试02: 读取知识")
        knowledge = self._create_test_knowledge("KNOW_TEST_002", "读取测试知识")
        self.service.create(knowledge)
        read_knowledge = self.service.read("KNOW_TEST_002")
        self.assertIsNotNone(read_knowledge)
        self.assertEqual(read_knowledge.title, "读取测试知识")
        self.logger.info(f"读取知识成功: {read_knowledge.knowledge_id}")

    def test_03_update(self):
        """测试03: 更新知识"""
        self.logger.info("测试03: 更新知识")
        knowledge = self._create_test_knowledge("KNOW_TEST_003", "更新前知识")
        self.service.create(knowledge)
        knowledge.title = "更新后知识"
        knowledge.tags = ["updated", "tag"]
        count = self.service.update(knowledge)
        self.assertEqual(count, 1)
        updated = self.service.read("KNOW_TEST_003")
        self.assertEqual(updated.title, "更新后知识")
        self.logger.info("更新知识测试通过")

    def test_04_delete(self):
        """测试04: 删除知识"""
        self.logger.info("测试04: 删除知识")
        knowledge = self._create_test_knowledge("KNOW_TEST_004", "待删除知识")
        self.service.create(knowledge)
        count = self.service.delete("KNOW_TEST_004")
        self.assertEqual(count, 1)
        deleted = self.service.read("KNOW_TEST_004")
        self.assertIsNone(deleted)
        self.logger.info("删除知识测试通过")

    def test_05_exists(self):
        """测试05: 检查知识是否存在"""
        self.logger.info("测试05: 检查知识是否存在")
        knowledge = self._create_test_knowledge("KNOW_TEST_005", "存在性测试知识")
        self.service.create(knowledge)
        exists = self.service.exists("KNOW_TEST_005")
        self.assertTrue(exists)
        not_exists = self.service.exists("KNOW_NONEXISTENT")
        self.assertFalse(not_exists)
        self.logger.info("存在性检查测试通过")

    def test_06_count(self):
        """测试06: 统计知识数量"""
        self.logger.info("测试06: 统计知识数量")
        before_count = self.service.count()
        knowledge = self._create_test_knowledge("KNOW_TEST_006", "统计测试知识")
        self.service.create(knowledge)
        after_count = self.service.count()
        self.assertEqual(after_count, before_count + 1)
        self.logger.info(f"知识数量: {after_count}")

    def test_07_read_all(self):
        """测试07: 读取所有知识"""
        self.logger.info("测试07: 读取所有知识")
        knowledge_list = self.service.read_all()
        self.assertIsInstance(knowledge_list, list)
        self.logger.info(f"读取到 {len(knowledge_list)} 条知识")

    def test_08_get_by_category(self):
        """测试08: 按分类查询知识"""
        self.logger.info("测试08: 按分类查询知识")
        knowledge = self._create_test_knowledge("KNOW_TEST_008", "分类测试知识")
        knowledge.category = "evaluation"
        self.service.create(knowledge)
        knowledge_list = self.service.get_by_category("evaluation")
        self.assertIsInstance(knowledge_list, list)
        self.logger.info(f"分类知识数量: {len(knowledge_list)}")

    def test_09_get_by_tag(self):
        """测试09: 按标签查询知识"""
        self.logger.info("测试09: 按标签查询知识")
        knowledge = self._create_test_knowledge("KNOW_TEST_009", "标签测试知识")
        knowledge.tags = ["uniquetag", "othertag"]
        self.service.create(knowledge)
        knowledge_list = self.service.get_by_tag("uniquetag")
        self.assertIsInstance(knowledge_list, list)
        self.logger.info(f"标签知识数量: {len(knowledge_list)}")

    def test_10_get_by_index(self):
        """测试10: 按指标查询知识"""
        self.logger.info("测试10: 按指标查询知识")
        knowledge = self._create_test_knowledge("KNOW_TEST_010", "指标测试知识")
        knowledge.index_ids = ["IDX_TEST_INDEX_001"]
        self.service.create(knowledge)
        knowledge_list = self.service.get_by_index("IDX_TEST_INDEX_001")
        self.assertIsInstance(knowledge_list, list)
        self.logger.info(f"指标知识数量: {len(knowledge_list)}")

    def test_11_create_many(self):
        """测试11: 批量创建知识"""
        self.logger.info("测试11: 批量创建知识")
        knowledge_list = [
            self._create_test_knowledge(f"KNOW_BATCH_{i}", f"批量知识{i}")
            for i in range(3)
        ]
        count = self.service.create_many(knowledge_list)
        self.assertEqual(count, 3)
        self.logger.info(f"批量创建 {count} 条知识")


if __name__ == '__main__':
    unittest.main()