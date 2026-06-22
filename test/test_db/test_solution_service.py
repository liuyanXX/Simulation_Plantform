"""方案服务测试

测试SolutionService的所有方法。
"""

import unittest
import os
import sys
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from data_storage_services.sql_db_services.solution_service import SolutionService
from bo.solution import Solution, SolutionStatus, SolutionPriority


class TestSolutionService(unittest.TestCase):
    """方案服务测试类"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'test_solution_service.log')
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
        cls.logger.info("开始SolutionService测试")
        cls.logger.info("=" * 60)

        test_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_data')
        os.makedirs(test_db_path, exist_ok=True)

        from . import ensure_tables_exist
        ensure_tables_exist(test_db_path, "test_solution.db")

        cls.service = SolutionService(
            db_type="sqlite",
            db_config={"db_path": test_db_path, "db_name": "test_solution.db"}
        )
        cls.test_solution_id = "SOL_TEST_001"
        cls.test_solution = cls._create_test_solution(cls.test_solution_id, "测试方案1")

    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        cls.service.disconnect()
        test_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_data')
        db_file = os.path.join(test_db_path, "test_solution.db")
        if os.path.exists(db_file):
            os.remove(db_file)
        cls.logger.info("SolutionService测试完成")

    @staticmethod
    def _create_test_solution(solution_id, name):
        """创建测试用方案对象"""
        return Solution(
            solution_id=solution_id,
            name=name,
            version="1.0",
            status=SolutionStatus.DRAFT,
            priority=SolutionPriority.MEDIUM,
            purpose="测试目的",
            objectives=["目标1", "目标2"],
            initiatives=["举措1", "举措2"],
            working_mechanism="工作机制描述",
            organization=["org1", "org2"],
            personnel=["person1", "person2"],
            roles=["PM", "DEV"],
            work_content="工作内容",
            constraints=["约束1"],
            risks=["风险1"],
            issues=["问题1"],
            other_notes="其他说明",
            main_document_id=None,
            auxiliary_document_ids=[],
            description="方案描述",
            owner="test_owner",
            created_by="test_creator",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            effective_date=None,
            expiry_date=None,
            tags=["tag1", "tag2"],
            metadata={"key": "value"}
        )

    def setUp(self):
        """每个测试前的准备"""
        self.logger.info("\n" + "-" * 60)

    def test_01_create(self):
        """测试01: 创建方案"""
        self.logger.info("测试01: 创建方案")
        solution = self._create_test_solution("SOL_001", "测试方案")
        result = self.service.create(solution)
        self.assertTrue(result)
        self.logger.info(f"创建方案成功: {solution.solution_id}")

    def test_02_read(self):
        """测试02: 读取方案"""
        self.logger.info("测试02: 读取方案")
        solution = self._create_test_solution("SOL_002", "读取测试方案")
        self.service.create(solution)
        read_solution = self.service.read("SOL_002")
        self.assertIsNotNone(read_solution)
        self.assertEqual(read_solution.name, "读取测试方案")
        self.logger.info(f"读取方案成功: {read_solution.solution_id}")

    def test_03_update(self):
        """测试03: 更新方案"""
        self.logger.info("测试03: 更新方案")
        solution = self._create_test_solution("SOL_003", "更新前方案")
        self.service.create(solution)
        solution.name = "更新后方案"
        solution.status = SolutionStatus.APPROVED
        count = self.service.update(solution)
        self.assertEqual(count, 1)
        updated = self.service.read("SOL_003")
        self.assertEqual(updated.name, "更新后方案")
        self.logger.info("更新方案测试通过")

    def test_04_delete(self):
        """测试04: 删除方案"""
        self.logger.info("测试04: 删除方案")
        solution = self._create_test_solution("SOL_004", "待删除方案")
        self.service.create(solution)
        count = self.service.delete("SOL_004")
        self.assertEqual(count, 1)
        deleted = self.service.read("SOL_004")
        self.assertIsNone(deleted)
        self.logger.info("删除方案测试通过")

    def test_05_exists(self):
        """测试05: 检查方案是否存在"""
        self.logger.info("测试05: 检查方案是否存在")
        solution = self._create_test_solution("SOL_005", "存在性测试方案")
        self.service.create(solution)
        exists = self.service.exists("SOL_005")
        self.assertTrue(exists)
        not_exists = self.service.exists("SOL_NONEXISTENT")
        self.assertFalse(not_exists)
        self.logger.info("存在性检查测试通过")

    def test_06_count(self):
        """测试06: 统计方案数量"""
        self.logger.info("测试06: 统计方案数量")
        before_count = self.service.count()
        solution = self._create_test_solution("SOL_006", "统计测试方案")
        self.service.create(solution)
        after_count = self.service.count()
        self.assertEqual(after_count, before_count + 1)
        self.logger.info(f"方案数量: {after_count}")

    def test_07_read_all(self):
        """测试07: 读取所有方案"""
        self.logger.info("测试07: 读取所有方案")
        solutions = self.service.read_all()
        self.assertIsInstance(solutions, list)
        self.logger.info(f"读取到 {len(solutions)} 个方案")

    def test_08_get_by_status(self):
        """测试08: 按状态查询方案"""
        self.logger.info("测试08: 按状态查询方案")
        solution = self._create_test_solution("SOL_008", "草稿方案")
        solution.status = SolutionStatus.DRAFT
        self.service.create(solution)
        draft_solutions = self.service.get_by_status(SolutionStatus.DRAFT)
        self.assertIsInstance(draft_solutions, list)
        self.logger.info(f"草稿状态方案数量: {len(draft_solutions)}")

    def test_09_get_by_owner(self):
        """测试09: 按负责人查询方案"""
        self.logger.info("测试09: 按负责人查询方案")
        solution = self._create_test_solution("SOL_009", "负责人测试方案")
        solution.owner = "test_owner_xxx"
        self.service.create(solution)
        owner_solutions = self.service.get_by_owner("test_owner_xxx")
        self.assertIsInstance(owner_solutions, list)
        self.logger.info(f"负责人方案数量: {len(owner_solutions)}")

    def test_10_search_by_name(self):
        """测试10: 按名称模糊查询"""
        self.logger.info("测试10: 按名称模糊查询")
        solution = self._create_test_solution("SOL_010", "模糊搜索测试方案")
        self.service.create(solution)
        results = self.service.search_by_name("模糊搜索")
        self.assertIsInstance(results, list)
        self.logger.info(f"模糊搜索结果数量: {len(results)}")

    def test_11_create_many(self):
        """测试11: 批量创建方案"""
        self.logger.info("测试11: 批量创建方案")
        solutions = [
            self._create_test_solution(f"SOL_BATCH_{i}", f"批量方案{i}")
            for i in range(3)
        ]
        count = self.service.create_many(solutions)
        self.assertEqual(count, 3)
        self.logger.info(f"批量创建 {count} 个方案")

    def test_12_read_all_with_where(self):
        """测试12: 带条件读取所有方案"""
        self.logger.info("测试12: 带条件读取所有方案")
        solution = self._create_test_solution("SOL_012", "条件读取测试")
        solution.priority = SolutionPriority.HIGH
        self.service.create(solution)
        results = self.service.read_all(where={"priority": "high"})
        self.assertIsInstance(results, list)
        self.logger.info(f"条件读取结果数量: {len(results)}")


if __name__ == '__main__':
    unittest.main()