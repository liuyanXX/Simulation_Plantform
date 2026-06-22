"""知识管理服务测试

测试KnowledgeManager的所有方法。
"""

import unittest
import os
import sys
import logging
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from knowledge_management import (
    KnowledgeManager,
    Knowledge,
    KnowledgeQueryParams
)


class TestKnowledgeManager(unittest.TestCase):
    """知识管理服务测试类"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        # 配置日志
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'log')
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, 'test_knowledge_manager.log')
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
        cls.logger.info("开始知识管理服务测试")
        cls.logger.info("=" * 60)

        # 使用实际的存储路径（包含预置数据）
        from knowledge_management import get_knowledge_manager
        cls.manager = get_knowledge_manager()

    def setUp(self):
        """每个测试方法前的准备"""
        self.logger.info("\n" + "-" * 60)

    def tearDown(self):
        """每个测试方法后的清理"""
        self.logger.info("-" * 60)

    def test_01_list_knowledge(self):
        """测试01: 获取所有知识"""
        self.logger.info("测试01: 获取所有知识")

        knowledge_list = self.manager.list_knowledge()

        self.assertIsInstance(knowledge_list, list)
        self.logger.info(f"获取到 {len(knowledge_list)} 条知识")

        for k in knowledge_list[:5]:  # 只显示前5条
            self.logger.info(f"  - {k.knowledge_id}: {k.title}")

        self.assertGreater(len(knowledge_list), 0, "知识列表不应为空")

    def test_02_get_knowledge(self):
        """测试02: 根据ID获取知识"""
        self.logger.info("测试02: 根据ID获取知识")

        # 测试存在的知识
        knowledge = self.manager.get_knowledge("KNOW_EVAL_001")
        self.assertIsNotNone(knowledge)
        self.assertEqual(knowledge.title, "SMART原则详解")
        self.logger.info(f"成功获取知识: {knowledge.knowledge_id} - {knowledge.title}")

        # 测试不存在的知识
        knowledge_not_found = self.manager.get_knowledge("KNOW_NOT_EXIST")
        self.assertIsNone(knowledge_not_found)
        self.logger.info("正确返回None对于不存在的知识")

    def test_03_add_knowledge(self):
        """测试03: 添加知识"""
        self.logger.info("测试03: 添加知识")

        new_knowledge = Knowledge(
            knowledge_id="KNOW_TEST_001",
            title="测试知识",
            summary="这是一个测试用的知识摘要",
            content="这是测试知识的详细内容，用于验证知识管理服务的添加功能。",
            index_ids=["IDX_COMP_001"],
            tags=["测试", "验证"],
            category="evaluation"
        )

        added_knowledge = self.manager.add_knowledge(new_knowledge)

        self.assertIsNotNone(added_knowledge)
        self.assertEqual(added_knowledge.knowledge_id, "KNOW_TEST_001")
        self.logger.info(f"成功添加知识: {added_knowledge.knowledge_id} - {added_knowledge.title}")

        # 验证添加成功
        retrieved = self.manager.get_knowledge("KNOW_TEST_001")
        self.assertIsNotNone(retrieved)
        self.logger.info("验证添加成功: 可以查询到新添加的知识")

        # 测试重复添加
        with self.assertRaises(ValueError):
            self.manager.add_knowledge(new_knowledge)
        self.logger.info("正确抛出异常: 重复添加知识")

    def test_04_update_knowledge(self):
        """测试04: 更新知识"""
        self.logger.info("测试04: 更新知识")

        updated = self.manager.update_knowledge(
            "KNOW_TEST_001",
            title="更新后的测试知识",
            summary="更新后的摘要"
        )

        self.assertEqual(updated.title, "更新后的测试知识")
        self.assertEqual(updated.summary, "更新后的摘要")
        self.logger.info(f"成功更新知识: {updated.knowledge_id} - {updated.title}")

        # 验证更新成功
        retrieved = self.manager.get_knowledge("KNOW_TEST_001")
        self.assertEqual(retrieved.title, "更新后的测试知识")
        self.logger.info("验证更新成功: 查询结果与更新一致")

        # 测试更新不存在的知识
        with self.assertRaises(ValueError):
            self.manager.update_knowledge("KNOW_NOT_EXIST", title="测试")
        self.logger.info("正确抛出异常: 更新不存在的知识")

    def test_05_query_knowledge(self):
        """测试05: 查询知识"""
        self.logger.info("测试05: 查询知识")

        # 按标题查询
        params = KnowledgeQueryParams(title="SMART")
        results = self.manager.query_knowledge(params)
        self.assertGreater(len(results), 0)
        self.logger.info(f"按标题查询: 找到 {len(results)} 条知识")

        # 按标签查询
        params = KnowledgeQueryParams(tag="测试")
        results = self.manager.query_knowledge(params)
        self.assertGreater(len(results), 0)
        self.logger.info(f"按标签查询: 找到 {len(results)} 条知识")

        # 按分类查询
        params = KnowledgeQueryParams(category="evaluation")
        results = self.manager.query_knowledge(params)
        self.assertGreater(len(results), 0)
        self.logger.info(f"按分类查询: 找到 {len(results)} 条知识")

    def test_06_get_knowledge_by_index(self):
        """测试06: 获取与指定指标相关的知识"""
        self.logger.info("测试06: 获取与指定指标相关的知识")

        knowledge_list = self.manager.get_knowledge_by_index("IDX_COMP_001")

        self.assertIsInstance(knowledge_list, list)
        self.assertGreater(len(knowledge_list), 0)
        self.logger.info(f"指标 IDX_COMP_001 关联 {len(knowledge_list)} 条知识")

        for k in knowledge_list:
            self.assertIn("IDX_COMP_001", k.index_ids)
            self.logger.info(f"  - {k.knowledge_id}: {k.title}")

    def test_07_search_knowledge(self):
        """测试07: 全文搜索知识"""
        self.logger.info("测试07: 全文搜索知识")

        # 搜索关键词
        results = self.manager.search_knowledge("SMART")
        self.assertGreater(len(results), 0)
        self.logger.info(f"搜索 'SMART': 找到 {len(results)} 条知识")

        for k in results[:3]:  # 只显示前3条
            self.logger.info(f"  - {k.knowledge_id}: {k.title}")

        # 搜索中文关键词
        results = self.manager.search_knowledge("评估")
        self.assertGreater(len(results), 0)
        self.logger.info(f"搜索 '评估': 找到 {len(results)} 条知识")

        # 搜索不存在的内容
        results = self.manager.search_knowledge("不存在的关键词xyz123")
        self.assertEqual(len(results), 0)
        self.logger.info("搜索不存在的内容: 正确返回空列表")

    def test_08_delete_knowledge(self):
        """测试08: 删除知识"""
        self.logger.info("测试08: 删除知识")

        # 删除知识
        result = self.manager.delete_knowledge("KNOW_TEST_001")
        self.assertTrue(result)
        self.logger.info("成功删除知识: KNOW_TEST_001")

        # 验证删除成功
        deleted = self.manager.get_knowledge("KNOW_TEST_001")
        self.assertIsNone(deleted)
        self.logger.info("验证删除成功: 查询不到已删除的知识")

        # 测试删除不存在的知识
        with self.assertRaises(ValueError):
            self.manager.delete_knowledge("KNOW_NOT_EXIST")
        self.logger.info("正确抛出异常: 删除不存在的知识")

    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        cls.logger.info("\n" + "=" * 60)
        cls.logger.info("知识管理服务测试完成")
        cls.logger.info("=" * 60)


if __name__ == '__main__':
    unittest.main(verbosity=2)
