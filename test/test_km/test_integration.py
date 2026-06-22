"""知识管理模块组合调用测试

测试评价指标和知识的组合操作。
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
    KnowledgeManager,
    EvaluationIndex,
    Knowledge,
    IndexType,
    IndexLevel,
    IndexQueryParams,
    KnowledgeQueryParams
)


class TestKnowledgeManagementIntegration(unittest.TestCase):
    """知识管理模块组合调用测试类"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        # 配置日志
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'log')
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, 'test_integration.log')
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
        cls.logger.info("开始知识管理模块组合调用测试")
        cls.logger.info("=" * 60)

        # 使用实际的存储路径（包含预置数据）
        from knowledge_management import get_index_manager, get_knowledge_manager
        cls.index_manager = get_index_manager()
        cls.knowledge_manager = get_knowledge_manager()

    def setUp(self):
        """每个测试方法前的准备"""
        self.logger.info("\n" + "-" * 60)

    def tearDown(self):
        """每个测试方法后的清理"""
        self.logger.info("-" * 60)

    def test_01_create_index_and_knowledge(self):
        """测试01: 创建指标并关联知识"""
        self.logger.info("测试01: 创建指标并关联知识")

        # 创建指标
        index = EvaluationIndex(
            index_id="IDX_INTEGRATION_001",
            name="集成测试指标",
            description="用于集成测试的评价指标",
            evaluation_method="通过集成测试进行评价",
            agent_ids=["INTEGRATION_AGENT"],
            index_type=IndexType.COMPLETENESS,
            index_level=IndexLevel.LEVEL_2,
            weight=20.0
        )
        self.index_manager.add_index(index)
        self.logger.info(f"创建指标: {index.index_id}")

        # 创建关联的知识
        knowledge = Knowledge(
            knowledge_id="KNOW_INTEGRATION_001",
            title="集成测试知识",
            summary="用于集成测试的知识摘要",
            content="这是集成测试知识的详细内容，用于验证指标和知识的关联。",
            index_ids=["IDX_INTEGRATION_001"],
            tags=["集成测试", "关联测试"],
            category="evaluation"
        )
        self.knowledge_manager.add_knowledge(knowledge)
        self.logger.info(f"创建知识: {knowledge.knowledge_id}")

        # 验证关联
        related_knowledge = self.knowledge_manager.get_knowledge_by_index("IDX_INTEGRATION_001")
        self.assertEqual(len(related_knowledge), 1)
        self.assertEqual(related_knowledge[0].knowledge_id, "KNOW_INTEGRATION_001")
        self.logger.info("验证成功: 知识与指标正确关联")

    def test_02_query_by_agent_and_get_knowledge(self):
        """测试02: 通过Agent查询指标并获取相关知识"""
        self.logger.info("测试02: 通过Agent查询指标并获取相关知识")

        # 查询Agent负责的指标
        params = IndexQueryParams(agent_id="COMP_001")
        indices = self.index_manager.query_indices(params)
        self.logger.info(f"Agent COMP_001 负责 {len(indices)} 个指标")

        # 获取每个指标关联的知识
        total_knowledge = 0
        for index in indices:
            knowledge_list = self.knowledge_manager.get_knowledge_by_index(index.index_id)
            total_knowledge += len(knowledge_list)
            self.logger.info(f"  指标 {index.index_id} 关联 {len(knowledge_list)} 条知识")

        self.logger.info(f"总计关联 {total_knowledge} 条知识")

    def test_03_create_parent_child_indices_with_knowledge(self):
        """测试03: 创建父子指标并关联知识"""
        self.logger.info("测试03: 创建父子指标并关联知识")

        # 创建父指标
        parent_index = EvaluationIndex(
            index_id="IDX_PRNT_001",
            name="父级集成指标",
            description="父级集成测试指标",
            evaluation_method="父级评价方法",
            agent_ids=["INTEGRATION_AGENT"],
            index_type=IndexType.COMPLETENESS,
            index_level=IndexLevel.LEVEL_1,
            weight=100.0
        )
        self.index_manager.add_index(parent_index)
        self.logger.info(f"创建父指标: {parent_index.index_id}")

        # 创建子指标
        child_index = EvaluationIndex(
            index_id="IDX_CHLD_001",
            name="子级集成指标",
            description="子级集成测试指标",
            evaluation_method="子级评价方法",
            agent_ids=["INTEGRATION_AGENT"],
            index_type=IndexType.COMPLETENESS,
            index_level=IndexLevel.LEVEL_2,
            parent_id="IDX_PRNT_001",
            weight=50.0
        )
        self.index_manager.add_index(child_index)
        self.logger.info(f"创建子指标: {child_index.index_id}")

        # 为子指标创建知识
        knowledge = Knowledge(
            knowledge_id="KNOW_CHLD_001",
            title="子指标知识",
            summary="子指标相关知识",
            content="这是子指标相关的知识内容。",
            index_ids=["IDX_CHLD_001"],
            tags=["子指标", "集成测试"],
            category="evaluation"
        )
        self.knowledge_manager.add_knowledge(knowledge)
        self.logger.info(f"创建知识: {knowledge.knowledge_id}")

        # 验证父子关系
        children = self.index_manager.get_child_indices("IDX_PRNT_001")
        self.assertEqual(len(children), 1)
        self.assertEqual(children[0].index_id, "IDX_CHLD_001")
        self.logger.info("验证成功: 父子指标关系正确")

        # 验证知识关联
        related_knowledge = self.knowledge_manager.get_knowledge_by_index("IDX_CHLD_001")
        self.assertEqual(len(related_knowledge), 1)
        self.logger.info("验证成功: 子指标知识关联正确")

    def test_04_search_and_filter_workflow(self):
        """测试04: 搜索和过滤工作流"""
        self.logger.info("测试04: 搜索和过滤工作流")

        # 步骤1: 搜索知识
        search_results = self.knowledge_manager.search_knowledge("评估")
        self.logger.info(f"步骤1: 搜索 '评估' 找到 {len(search_results)} 条知识")

        # 步骤2: 提取关联的指标ID
        index_ids = set()
        for k in search_results:
            index_ids.update(k.index_ids)
        self.logger.info(f"步骤2: 提取到 {len(index_ids)} 个关联指标ID")

        # 步骤3: 查询这些指标
        for index_id in list(index_ids)[:3]:  # 只查询前3个
            index = self.index_manager.get_index(index_id)
            if index:
                self.logger.info(f"  指标: {index.index_id} - {index.name}")

        # 步骤4: 按类型过滤指标
        params = IndexQueryParams(index_type=IndexType.COMPLETENESS)
        completeness_indices = self.index_manager.query_indices(params)
        self.logger.info(f"步骤4: 完整性类型指标 {len(completeness_indices)} 个")

        # 步骤5: 获取这些指标的所有知识
        all_knowledge_ids = set()
        for index in completeness_indices:
            knowledge_list = self.knowledge_manager.get_knowledge_by_index(index.index_id)
            for k in knowledge_list:
                all_knowledge_ids.add(k.knowledge_id)

        self.logger.info(f"步骤5: 完整性指标关联的知识 {len(all_knowledge_ids)} 条")

    def test_05_update_index_and_sync_knowledge(self):
        """测试05: 更新指标并同步知识"""
        self.logger.info("测试05: 更新指标并同步知识")

        # 创建新指标
        index = EvaluationIndex(
            index_id="IDX_SYNC_001",
            name="同步测试指标",
            description="用于测试同步的指标",
            evaluation_method="同步测试方法",
            agent_ids=["SYNC_AGENT"],
            index_type=IndexType.RATIONALITY,
            index_level=IndexLevel.LEVEL_2,
            weight=30.0
        )
        self.index_manager.add_index(index)
        self.logger.info(f"创建指标: {index.index_id}")

        # 创建关联知识
        knowledge1 = Knowledge(
            knowledge_id="KNOW_SYNC_001",
            title="同步知识1",
            summary="同步测试知识1",
            content="同步测试知识内容1",
            index_ids=["IDX_SYNC_001"],
            tags=["同步", "测试"],
            category="evaluation"
        )
        knowledge2 = Knowledge(
            knowledge_id="KNOW_SYNC_002",
            title="同步知识2",
            summary="同步测试知识2",
            content="同步测试知识内容2",
            index_ids=["IDX_SYNC_001"],
            tags=["同步", "测试"],
            category="evaluation"
        )
        self.knowledge_manager.add_knowledge(knowledge1)
        self.knowledge_manager.add_knowledge(knowledge2)
        self.logger.info("创建2条关联知识")

        # 更新指标
        updated_index = self.index_manager.update_index(
            "IDX_SYNC_001",
            name="更新后的同步测试指标",
            weight=40.0
        )
        self.logger.info(f"更新指标: {updated_index.name}")

        # 验证知识关联仍然有效
        related_knowledge = self.knowledge_manager.get_knowledge_by_index("IDX_SYNC_001")
        self.assertEqual(len(related_knowledge), 2)
        self.logger.info("验证成功: 指标更新后知识关联仍然有效")

        # 更新知识，添加新的指标关联
        updated_knowledge = self.knowledge_manager.update_knowledge(
            "KNOW_SYNC_001",
            index_ids=["IDX_SYNC_001", "IDX_COMP_001"]
        )
        self.logger.info("更新知识: 添加新的指标关联")

        # 验证知识关联到多个指标
        k = self.knowledge_manager.get_knowledge("KNOW_SYNC_001")
        self.assertIn("IDX_SYNC_001", k.index_ids)
        self.assertIn("IDX_COMP_001", k.index_ids)
        self.logger.info("验证成功: 知识正确关联到多个指标")

    def test_06_delete_index_with_knowledge_cleanup(self):
        """测试06: 删除指标并处理知识关联"""
        self.logger.info("测试06: 删除指标并处理知识关联")

        # 创建指标和知识
        index = EvaluationIndex(
            index_id="IDX_DELETE_001",
            name="待删除指标",
            description="用于测试删除的指标",
            evaluation_method="删除测试方法",
            agent_ids=["DELETE_AGENT"],
            index_type=IndexType.RISK,
            index_level=IndexLevel.LEVEL_2,
            weight=25.0
        )
        self.index_manager.add_index(index)
        self.logger.info(f"创建指标: {index.index_id}")

        knowledge = Knowledge(
            knowledge_id="KNOW_DELETE_001",
            title="待删除指标的知识",
            summary="待删除指标相关知识",
            content="待删除指标相关知识内容",
            index_ids=["IDX_DELETE_001"],
            tags=["删除", "测试"],
            category="evaluation"
        )
        self.knowledge_manager.add_knowledge(knowledge)
        self.logger.info(f"创建知识: {knowledge.knowledge_id}")

        # 删除指标
        self.index_manager.delete_index("IDX_DELETE_001")
        self.logger.info("删除指标: IDX_DELETE_001")

        # 验证指标已删除
        deleted_index = self.index_manager.get_index("IDX_DELETE_001")
        self.assertIsNone(deleted_index)
        self.logger.info("验证成功: 指标已删除")

        # 知识仍然存在，但关联的指标ID已不存在
        remaining_knowledge = self.knowledge_manager.get_knowledge("KNOW_DELETE_001")
        self.assertIsNotNone(remaining_knowledge)
        self.logger.info("知识仍然存在: KNOW_DELETE_001")

        # 更新知识，移除已删除的指标关联
        self.knowledge_manager.update_knowledge(
            "KNOW_DELETE_001",
            index_ids=[]  # 清空关联
        )
        self.logger.info("更新知识: 清空指标关联")

        # 清理测试数据
        self.knowledge_manager.delete_knowledge("KNOW_DELETE_001")
        self.logger.info("清理测试知识: KNOW_DELETE_001")

    def test_07_full_workflow(self):
        """测试07: 完整工作流"""
        self.logger.info("测试07: 完整工作流")

        # 步骤1: 创建完整的指标体系
        self.logger.info("步骤1: 创建完整的指标体系")
        parent = EvaluationIndex(
            index_id="IDX_WORK_001",
            name="工作流父指标",
            description="工作流测试父指标",
            evaluation_method="父指标评价",
            agent_ids=["WORKFLOW_AGENT"],
            index_type=IndexType.STRATEGY,
            index_level=IndexLevel.LEVEL_1,
            weight=100.0
        )
        self.index_manager.add_index(parent)

        child1 = EvaluationIndex(
            index_id="IDX_WORK_002",
            name="工作流子指标1",
            description="工作流测试子指标1",
            evaluation_method="子指标1评价",
            agent_ids=["WORKFLOW_AGENT"],
            index_type=IndexType.STRATEGY,
            index_level=IndexLevel.LEVEL_2,
            parent_id="IDX_WORK_001",
            weight=50.0
        )
        self.index_manager.add_index(child1)

        child2 = EvaluationIndex(
            index_id="IDX_WORK_003",
            name="工作流子指标2",
            description="工作流测试子指标2",
            evaluation_method="子指标2评价",
            agent_ids=["WORKFLOW_AGENT"],
            index_type=IndexType.STRATEGY,
            index_level=IndexLevel.LEVEL_2,
            parent_id="IDX_WORK_001",
            weight=50.0
        )
        self.index_manager.add_index(child2)
        self.logger.info("创建1个父指标和2个子指标")

        # 步骤2: 为每个子指标创建知识
        self.logger.info("步骤2: 为每个子指标创建知识")
        for i, child_id in enumerate(["IDX_WORK_002", "IDX_WORK_003"], 1):
            knowledge = Knowledge(
                knowledge_id=f"KNOW_WORK_00{i}",
                title=f"工作流知识{i}",
                summary=f"工作流测试知识{i}摘要",
                content=f"工作流测试知识{i}内容",
                index_ids=[child_id],
                tags=["工作流", "测试"],
                category="evaluation"
            )
            self.knowledge_manager.add_knowledge(knowledge)
        self.logger.info("创建2条知识")

        # 步骤3: 查询并验证
        self.logger.info("步骤3: 查询并验证")
        children = self.index_manager.get_child_indices("IDX_WORK_001")
        self.assertEqual(len(children), 2)
        self.logger.info(f"父指标有 {len(children)} 个子指标")

        for child in children:
            knowledge_list = self.knowledge_manager.get_knowledge_by_index(child.index_id)
            self.assertEqual(len(knowledge_list), 1)
            self.logger.info(f"  子指标 {child.index_id} 有 {len(knowledge_list)} 条知识")

        # 步骤4: 清理
        self.logger.info("步骤4: 清理测试数据")
        self.knowledge_manager.delete_knowledge("KNOW_WORK_001")
        self.knowledge_manager.delete_knowledge("KNOW_WORK_002")
        self.index_manager.delete_index("IDX_WORK_002")
        self.index_manager.delete_index("IDX_WORK_003")
        self.index_manager.delete_index("IDX_WORK_001")
        self.logger.info("清理完成")

    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        cls.logger.info("\n" + "=" * 60)
        cls.logger.info("知识管理模块组合调用测试完成")
        cls.logger.info("=" * 60)


if __name__ == '__main__':
    unittest.main(verbosity=2)
