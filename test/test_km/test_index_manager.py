"""评价指标管理服务测试

测试EvaluationIndexManager的所有方法。
"""

import unittest
import os
import sys
import logging
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from knowledge_management import (
    EvaluationIndexManager,
    EvaluationIndex,
    IndexType,
    IndexLevel,
    IndexQueryParams
)


class TestEvaluationIndexManager(unittest.TestCase):
    """评价指标管理服务测试类"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        # 配置日志
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'log')
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, 'test_index_manager.log')
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
        cls.logger.info("开始评价指标管理服务测试")
        cls.logger.info("=" * 60)

        # 使用实际的存储路径（包含预置数据）
        from knowledge_management import get_index_manager
        cls.manager = get_index_manager()

    def setUp(self):
        """每个测试方法前的准备"""
        self.logger.info("\n" + "-" * 60)

    def tearDown(self):
        """每个测试方法后的清理"""
        self.logger.info("-" * 60)

    def test_01_list_indices(self):
        """测试01: 获取所有评价指标"""
        self.logger.info("测试01: 获取所有评价指标")

        indices = self.manager.list_indices()

        self.assertIsInstance(indices, list)
        self.logger.info(f"获取到 {len(indices)} 个评价指标")

        for idx in indices:
            self.logger.info(f"  - {idx.index_id}: {idx.name}")

        self.assertGreater(len(indices), 0, "评价指标列表不应为空")

    def test_02_get_index(self):
        """测试02: 根据ID获取评价指标"""
        self.logger.info("测试02: 根据ID获取评价指标")

        # 测试存在的指标
        index = self.manager.get_index("IDX_COMP_001")
        self.assertIsNotNone(index)
        self.assertEqual(index.name, "目标完整性")
        self.logger.info(f"成功获取指标: {index.index_id} - {index.name}")

        # 测试不存在的指标
        index_not_found = self.manager.get_index("IDX_NOT_EXIST")
        self.assertIsNone(index_not_found)
        self.logger.info("正确返回None对于不存在的指标")

    def test_03_add_index(self):
        """测试03: 添加评价指标"""
        self.logger.info("测试03: 添加评价指标")

        new_index = EvaluationIndex(
            index_id="IDX_TEST_001",
            name="测试指标",
            description="这是一个测试用的评价指标",
            evaluation_method="通过测试方法进行评价",
            agent_ids=["TEST_AGENT"],
            index_type=IndexType.COMPLETENESS,
            index_level=IndexLevel.LEVEL_2,
            weight=10.0
        )

        added_index = self.manager.add_index(new_index)

        self.assertIsNotNone(added_index)
        self.assertEqual(added_index.index_id, "IDX_TEST_001")
        self.logger.info(f"成功添加指标: {added_index.index_id} - {added_index.name}")

        # 验证添加成功
        retrieved = self.manager.get_index("IDX_TEST_001")
        self.assertIsNotNone(retrieved)
        self.logger.info("验证添加成功: 可以查询到新添加的指标")

        # 测试重复添加
        with self.assertRaises(ValueError):
            self.manager.add_index(new_index)
        self.logger.info("正确抛出异常: 重复添加指标")

    def test_04_update_index(self):
        """测试04: 更新评价指标"""
        self.logger.info("测试04: 更新评价指标")

        updated = self.manager.update_index(
            "IDX_TEST_001",
            name="更新后的测试指标",
            weight=15.0
        )

        self.assertEqual(updated.name, "更新后的测试指标")
        self.assertEqual(updated.weight, 15.0)
        self.logger.info(f"成功更新指标: {updated.index_id} - {updated.name}")

        # 验证更新成功
        retrieved = self.manager.get_index("IDX_TEST_001")
        self.assertEqual(retrieved.name, "更新后的测试指标")
        self.logger.info("验证更新成功: 查询结果与更新一致")

        # 测试更新不存在的指标
        with self.assertRaises(ValueError):
            self.manager.update_index("IDX_NOT_EXIST", name="测试")
        self.logger.info("正确抛出异常: 更新不存在的指标")

    def test_05_query_indices(self):
        """测试05: 查询评价指标"""
        self.logger.info("测试05: 查询评价指标")

        # 按类型查询
        params = IndexQueryParams(index_type=IndexType.COMPLETENESS)
        results = self.manager.query_indices(params)
        self.assertGreater(len(results), 0)
        self.logger.info(f"按类型查询: 找到 {len(results)} 个完整性指标")

        # 按Agent查询
        params = IndexQueryParams(agent_id="COMP_001")
        results = self.manager.query_indices(params)
        self.assertGreater(len(results), 0)
        self.logger.info(f"按Agent查询: 找到 {len(results)} 个指标")

        # 按名称查询
        params = IndexQueryParams(name="完整性")
        results = self.manager.query_indices(params)
        self.assertGreater(len(results), 0)
        self.logger.info(f"按名称查询: 找到 {len(results)} 个指标")

    def test_06_get_indices_by_agent(self):
        """测试06: 获取指定Agent负责的指标"""
        self.logger.info("测试06: 获取指定Agent负责的指标")

        indices = self.manager.get_indices_by_agent("COMP_001")

        self.assertIsInstance(indices, list)
        self.assertGreater(len(indices), 0)
        self.logger.info(f"Agent COMP_001 负责 {len(indices)} 个指标")

        for idx in indices:
            self.assertIn("COMP_001", idx.agent_ids)
            self.logger.info(f"  - {idx.index_id}: {idx.name}")

    def test_07_get_child_indices(self):
        """测试07: 获取子指标列表"""
        self.logger.info("测试07: 获取子指标列表")

        # 先添加一个父指标
        parent_index = EvaluationIndex(
            index_id="IDX_PARENT_001",
            name="父指标",
            description="这是一个父指标",
            evaluation_method="父指标评价方法",
            agent_ids=["TEST_AGENT"],
            index_type=IndexType.COMPLETENESS,
            index_level=IndexLevel.LEVEL_1,
            weight=100.0
        )
        self.manager.add_index(parent_index)
        self.logger.info("添加父指标: IDX_PARENT_001")

        # 添加子指标
        child_index = EvaluationIndex(
            index_id="IDX_CHILD_001",
            name="子指标",
            description="这是一个子指标",
            evaluation_method="子指标评价方法",
            agent_ids=["TEST_AGENT"],
            index_type=IndexType.COMPLETENESS,
            index_level=IndexLevel.LEVEL_2,
            parent_id="IDX_PARENT_001",
            weight=50.0
        )
        self.manager.add_index(child_index)
        self.logger.info("添加子指标: IDX_CHILD_001")

        # 获取子指标
        children = self.manager.get_child_indices("IDX_PARENT_001")
        self.assertEqual(len(children), 1)
        self.assertEqual(children[0].index_id, "IDX_CHILD_001")
        self.logger.info(f"成功获取子指标: {children[0].index_id}")

    def test_08_delete_index(self):
        """测试08: 删除评价指标"""
        self.logger.info("测试08: 删除评价指标")

        # 删除没有子指标的指标
        result = self.manager.delete_index("IDX_CHILD_001")
        self.assertTrue(result)
        self.logger.info("成功删除子指标: IDX_CHILD_001")

        # 验证删除成功
        deleted = self.manager.get_index("IDX_CHILD_001")
        self.assertIsNone(deleted)
        self.logger.info("验证删除成功: 查询不到已删除的指标")

        # 删除父指标（现在没有子指标依赖）
        result = self.manager.delete_index("IDX_PARENT_001")
        self.assertTrue(result)
        self.logger.info("成功删除父指标: IDX_PARENT_001")

        # 测试删除不存在的指标
        with self.assertRaises(ValueError):
            self.manager.delete_index("IDX_NOT_EXIST")
        self.logger.info("正确抛出异常: 删除不存在的指标")

        # 清理测试指标
        self.manager.delete_index("IDX_TEST_001")
        self.logger.info("清理测试指标: IDX_TEST_001")

    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        cls.logger.info("\n" + "=" * 60)
        cls.logger.info("评价指标管理服务测试完成")
        cls.logger.info("=" * 60)


if __name__ == '__main__':
    unittest.main(verbosity=2)
