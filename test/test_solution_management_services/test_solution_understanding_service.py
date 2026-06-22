import os
import sys
import logging
import unittest
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
logs_dir = os.path.join(project_root, 'logs')
os.makedirs(logs_dir, exist_ok=True)

from solution_management_services.solution_understanding_service import (
    SolutionUnderstandingService,
    UnderstandingResult
)
from ai_modules.basic.llm_client import MockLLMClient
from bo.solution import Solution, SolutionDocument, SolutionStatus, SolutionPriority

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, 'test_solution_understanding_service.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TestSolutionUnderstandingService(unittest.TestCase):
    """测试SolutionUnderstandingService"""

    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        logger.info("=" * 60)
        logger.info("开始测试SolutionUnderstandingService")
        logger.info("=" * 60)
        
        cls.test_storage = "test_understanding_data"
        os.makedirs(cls.test_storage, exist_ok=True)
        
        cls.llm_client = MockLLMClient()
        cls.service = SolutionUnderstandingService(
            llm_client=cls.llm_client,
            storage_path=cls.test_storage
        )
        
        cls.test_doc = SolutionDocument(
            document_id="DOC_UNDERSTAND_001",
            file_name="test_doc.txt",
            text_content="数字化转型实施方案。目标：实现业务流程数字化，提升运营效率。举措：引入云计算平台，建设大数据分析系统。",
            version="1.0"
        )
        
        cls.test_solution = Solution(
            solution_id="SOL_TEST_001",
            name="测试方案",
            version="1.0",
            status=SolutionStatus.DRAFT,
            priority=SolutionPriority.HIGH,
            purpose="测试目的",
            objectives=["目标1", "目标2"],
            initiatives=["举措1", "举措2"],
            work_content="测试工作内容"
        )

    @classmethod
    def tearDownClass(cls):
        """清理测试数据"""
        import shutil
        if os.path.exists(cls.test_storage):
            shutil.rmtree(cls.test_storage)
        logger.info("测试数据已清理")

    def test_01_create_solution(self):
        """测试创建方案"""
        logger.info("测试01: 创建方案")
        
        solution = self.service.create_solution(self.test_solution)
        
        self.assertIsNotNone(solution)
        self.assertEqual(solution.solution_id, "SOL_TEST_001")
        self.assertEqual(solution.name, "测试方案")
        
        logger.info(f"  ✓ 创建成功: {solution.solution_id}")

    def test_02_create_duplicate_solution(self):
        """测试创建重复方案"""
        logger.info("测试02: 创建重复方案（应报错）")
        
        with self.assertRaises(ValueError):
            self.service.create_solution(self.test_solution)
        
        logger.info("  ✓ 重复检测正常")

    def test_03_get_solution(self):
        """测试获取方案"""
        logger.info("测试03: 获取方案")
        
        solution = self.service.get_solution("SOL_TEST_001")
        
        self.assertIsNotNone(solution)
        self.assertEqual(solution.solution_id, "SOL_TEST_001")
        
        logger.info(f"  ✓ 获取成功: {solution.name}")

    def test_04_get_nonexistent_solution(self):
        """测试获取不存在的方案"""
        logger.info("测试04: 获取不存在的方案")
        
        solution = self.service.get_solution("SOL_NOT_EXIST")
        
        self.assertIsNone(solution)
        logger.info("  ✓ 返回None")

    def test_05_list_solutions(self):
        """测试查询方案列表"""
        logger.info("测试05: 查询方案列表")
        
        solutions = self.service.list_solutions()
        
        self.assertTrue(len(solutions) > 0)
        logger.info(f"  ✓ 查询到 {len(solutions)} 个方案")

    def test_06_list_solutions_with_status_filter(self):
        """测试按状态过滤"""
        logger.info("测试06: 按状态过滤方案")
        
        # 添加另一个状态的方案
        solution2 = Solution(
            solution_id="SOL_TEST_002",
            name="审核中方案",
            version="1.0",
            status=SolutionStatus.REVIEW,
            priority=SolutionPriority.MEDIUM,
            purpose="审核测试"
        )
        self.service.create_solution(solution2)
        
        solutions = self.service.list_solutions(status=SolutionStatus.DRAFT)
        
        self.assertEqual(len(solutions), 1)
        self.assertEqual(solutions[0].solution_id, "SOL_TEST_001")
        
        logger.info("  ✓ 状态过滤正常")

    def test_07_list_solutions_with_priority_filter(self):
        """测试按优先级过滤"""
        logger.info("测试07: 按优先级过滤方案")
        
        solutions = self.service.list_solutions(priority=SolutionPriority.HIGH)
        
        self.assertEqual(len(solutions), 1)
        logger.info("  ✓ 优先级过滤正常")

    def test_08_list_solutions_with_keyword(self):
        """测试关键词搜索"""
        logger.info("测试08: 关键词搜索")
        
        solutions = self.service.list_solutions(keyword="测试")
        
        self.assertTrue(len(solutions) > 0)
        logger.info(f"  ✓ 搜索到 {len(solutions)} 个方案")

    def test_09_get_all_solutions(self):
        """测试获取所有方案"""
        logger.info("测试09: 获取所有方案")
        
        solutions = self.service.get_all_solutions()
        
        self.assertTrue(len(solutions) >= 2)
        logger.info(f"  ✓ 共有 {len(solutions)} 个方案")

    def test_10_update_solution(self):
        """测试更新方案"""
        logger.info("测试10: 更新方案")
        
        updated = self.service.update_solution(
            "SOL_TEST_001",
            version="2.0",
            status=SolutionStatus.REVIEW,
            description="更新描述"
        )
        
        self.assertEqual(updated.version, "2.0")
        self.assertEqual(updated.status, SolutionStatus.REVIEW)
        self.assertEqual(updated.description, "更新描述")
        
        logger.info(f"  ✓ 更新成功: {updated.version}")

    def test_11_update_nonexistent_solution(self):
        """测试更新不存在的方案"""
        logger.info("测试11: 更新不存在的方案（应报错）")
        
        with self.assertRaises(ValueError):
            self.service.update_solution("SOL_NOT_EXIST", version="2.0")
        
        logger.info("  ✓ 错误处理正常")

    def test_12_delete_solution(self):
        """测试删除方案"""
        logger.info("测试12: 删除方案")
        
        result = self.service.delete_solution("SOL_TEST_002")
        
        self.assertTrue(result)
        self.assertIsNone(self.service.get_solution("SOL_TEST_002"))
        
        logger.info("  ✓ 删除成功")

    def test_13_delete_nonexistent_solution(self):
        """测试删除不存在的方案"""
        logger.info("测试13: 删除不存在的方案（应报错）")
        
        with self.assertRaises(ValueError):
            self.service.delete_solution("SOL_NOT_EXIST")
        
        logger.info("  ✓ 错误处理正常")

    def test_14_save_solution(self):
        """测试保存方案"""
        logger.info("测试14: 保存方案")
        
        path = self.service.save_solution("SOL_TEST_001")
        
        self.assertTrue(os.path.exists(path))
        logger.info(f"  ✓ 保存成功: {path}")

    def test_15_save_all_solutions(self):
        """测试保存所有方案"""
        logger.info("测试15: 保存所有方案")
        
        paths = self.service.save_all_solutions()
        
        self.assertTrue(len(paths) > 0)
        logger.info(f"  ✓ 保存了 {len(paths)} 个方案")

    def test_16_load_solution(self):
        """测试加载方案"""
        logger.info("测试16: 加载方案")
        
        new_service = SolutionUnderstandingService(
            llm_client=self.llm_client,
            storage_path=self.test_storage
        )
        count = new_service.load_all_solutions()
        
        self.assertTrue(count > 0)
        loaded = new_service.get_solution("SOL_TEST_001")
        self.assertIsNotNone(loaded)
        
        logger.info(f"  ✓ 加载了 {count} 个方案")

    def test_17_understand_document(self):
        """测试理解文档"""
        logger.info("测试17: 理解文档")
        
        result = self.service.understand_document(self.test_doc)
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.solution)
        self.assertIsNotNone(result.raw_response)
        
        logger.info(f"  ✓ 文档理解成功: {result.solution.solution_id}")

    def test_18_understand_empty_document(self):
        """测试理解空文档"""
        logger.info("测试18: 理解空文档（应失败）")
        
        empty_doc = SolutionDocument(
            document_id="DOC_EMPTY",
            file_name="empty.txt",
            text_content=""
        )
        
        result = self.service.understand_document(empty_doc)
        
        self.assertFalse(result.success)
        self.assertIn("没有文本内容", result.error_message)
        
        logger.info("  ✓ 空文档处理正常")

    def test_19_get_solution_count(self):
        """测试获取方案数量"""
        logger.info("测试19: 获取方案数量")
        
        count = self.service.get_solution_count()
        
        self.assertTrue(count >= 1)
        logger.info(f"  ✓ 方案数量: {count}")

    def test_20_get_statistics(self):
        """测试获取统计信息"""
        logger.info("测试20: 获取统计信息")
        
        stats = self.service.get_statistics()
        
        self.assertIn("total_count", stats)
        self.assertIn("status_distribution", stats)
        self.assertIn("priority_distribution", stats)
        
        logger.info(f"  ✓ 统计信息: {stats}")


if __name__ == '__main__':
    os.makedirs('logs', exist_ok=True)
    unittest.main(verbosity=2)