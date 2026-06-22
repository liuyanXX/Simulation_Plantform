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

from solution_management_services.solution_management_module import (
    SolutionManagementModule,
    SolutionProcessResult
)
from ai_modules.basic.llm_client import MockLLMClient
from bo.solution import SolutionDocument, Solution, SolutionStatus, SolutionPriority

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, 'test_solution_management_module.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TestSolutionManagementModule(unittest.TestCase):
    """测试SolutionManagementModule"""

    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        logger.info("=" * 60)
        logger.info("开始测试SolutionManagementModule")
        logger.info("=" * 60)
        
        cls.test_storage = "test_module_data"
        os.makedirs(cls.test_storage, exist_ok=True)
        
        cls.llm_client = MockLLMClient()
        cls.module = SolutionManagementModule(
            llm_client=cls.llm_client,
            storage_base_path=cls.test_storage
        )

    @classmethod
    def tearDownClass(cls):
        """清理测试数据"""
        import shutil
        if os.path.exists(cls.test_storage):
            shutil.rmtree(cls.test_storage)
        logger.info("测试数据已清理")

    def test_01_create_document_from_text(self):
        """测试从文本创建文档"""
        logger.info("测试01: 从文本创建文档")
        
        doc = self.module.create_document_from_text(
            document_id="DOC_MOD_001",
            text_content="这是测试文档内容，用于测试方案管理模块的完整流程。",
            file_name="test_doc.txt",
            version="1.0"
        )
        
        self.assertIsNotNone(doc)
        self.assertEqual(doc.document_id, "DOC_MOD_001")
        self.assertEqual(doc.text_content, "这是测试文档内容，用于测试方案管理模块的完整流程。")
        
        logger.info(f"  ✓ 创建成功: {doc.document_id}")

    def test_02_import_document(self):
        """测试导入文档"""
        logger.info("测试02: 导入文档")
        
        # 创建临时文件
        temp_file = "temp_import.txt"
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write("导入文件内容")
        
        doc = self.module.import_document(
            file_path=temp_file,
            document_id="DOC_MOD_002",
            version="1.0",
            description="导入的文档"
        )
        
        self.assertIsNotNone(doc)
        self.assertEqual(doc.document_id, "DOC_MOD_002")
        self.assertEqual(doc.text_content, "导入文件内容")
        
        # 清理临时文件
        os.remove(temp_file)
        logger.info(f"  ✓ 导入成功: {doc.file_name}")

    def test_03_get_document(self):
        """测试获取文档"""
        logger.info("测试03: 获取文档")
        
        doc = self.module.get_document("DOC_MOD_001")
        
        self.assertIsNotNone(doc)
        self.assertEqual(doc.document_id, "DOC_MOD_001")
        
        logger.info(f"  ✓ 获取成功")

    def test_04_get_nonexistent_document(self):
        """测试获取不存在的文档"""
        logger.info("测试04: 获取不存在的文档")
        
        doc = self.module.get_document("DOC_NOT_EXIST")
        
        self.assertIsNone(doc)
        logger.info("  ✓ 返回None")

    def test_05_understand_document(self):
        """测试理解文档"""
        logger.info("测试05: 理解文档")
        
        solution = self.module.understand_document("DOC_MOD_001")
        
        self.assertIsNotNone(solution)
        self.assertEqual(solution.solution_id, "SOL_DOC_MOD_001")
        
        logger.info(f"  ✓ 理解成功: {solution.solution_id}")

    def test_06_get_solution(self):
        """测试获取方案"""
        logger.info("测试06: 获取方案")
        
        solution = self.module.get_solution("SOL_DOC_MOD_001")
        
        self.assertIsNotNone(solution)
        self.assertEqual(solution.solution_id, "SOL_DOC_MOD_001")
        
        logger.info(f"  ✓ 获取成功: {solution.name}")

    def test_07_get_nonexistent_solution(self):
        """测试获取不存在的方案"""
        logger.info("测试07: 获取不存在的方案")
        
        solution = self.module.get_solution("SOL_NOT_EXIST")
        
        self.assertIsNone(solution)
        logger.info("  ✓ 返回None")

    def test_08_decompose_solution(self):
        """测试拆解方案"""
        logger.info("测试08: 拆解方案")
        
        tasks_graph = self.module.decompose_solution("SOL_DOC_MOD_001")
        
        self.assertIsNotNone(tasks_graph)
        self.assertTrue(len(tasks_graph.tasks) > 0)
        
        logger.info(f"  ✓ 拆解成功: {tasks_graph.graph_id}, {len(tasks_graph.tasks)}个任务")

    def test_09_get_tasks_graph(self):
        """测试获取任务图谱"""
        logger.info("测试09: 获取任务图谱")
        
        tasks_graph = self.module.decompose_solution("SOL_DOC_MOD_001")
        
        if tasks_graph:
            retrieved = self.module.get_tasks_graph(tasks_graph.graph_id)
            
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.graph_id, tasks_graph.graph_id)
            
            logger.info(f"  ✓ 获取成功: {retrieved.graph_name}")

    def test_10_get_task(self):
        """测试获取任务"""
        logger.info("测试10: 获取任务")
        
        tasks_graph = self.module.decompose_solution("SOL_DOC_MOD_001")
        
        if tasks_graph and tasks_graph.tasks:
            first_task = tasks_graph.tasks[0]
            retrieved = self.module.get_task(first_task.task_id)
            
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.task_id, first_task.task_id)
            
            logger.info(f"  ✓ 获取成功: {retrieved.task_name}")

    def test_11_process_document_to_solution(self):
        """测试处理文档到方案"""
        logger.info("测试11: 处理文档到方案")
        
        # 创建新文档
        doc = self.module.create_document_from_text(
            document_id="DOC_TO_SOL_001",
            text_content="测试文档内容"
        )
        
        solution = self.module.process_document_to_solution("DOC_TO_SOL_001")
        
        self.assertIsNotNone(solution)
        self.assertEqual(solution.solution_id, "SOL_DOC_TO_SOL_001")
        
        logger.info(f"  ✓ 处理成功: {solution.name}")

    def test_12_process_solution_to_tasks(self):
        """测试处理方案到任务图谱"""
        logger.info("测试12: 处理方案到任务图谱")
        
        tasks_graph = self.module.process_solution_to_tasks("SOL_DOC_TO_SOL_001")
        
        self.assertIsNotNone(tasks_graph)
        self.assertTrue(len(tasks_graph.tasks) > 0)
        
        logger.info(f"  ✓ 处理成功: {len(tasks_graph.tasks)}个任务")

    def test_13_process_document_full(self):
        """测试完整处理流程"""
        logger.info("测试13: 完整处理流程")
        
        # 创建新文档
        doc = self.module.create_document_from_text(
            document_id="DOC_FULL_001",
            text_content="完整流程测试文档"
        )
        
        result = self.module.process_document_full("DOC_FULL_001")
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.document_id)
        self.assertIsNotNone(result.solution_id)
        self.assertIsNotNone(result.tasks_graph_id)
        self.assertTrue(result.task_count > 0)
        
        logger.info(f"  ✓ 完整流程成功: {result.message}")

    def test_14_process_document_full_failure(self):
        """测试完整流程失败情况"""
        logger.info("测试14: 完整流程失败情况（文档不存在）")
        
        result = self.module.process_document_full("DOC_NOT_EXIST")
        
        self.assertFalse(result.success)
        self.assertTrue(len(result.errors) > 0)
        
        logger.info("  ✓ 失败处理正常")

    def test_15_get_statistics(self):
        """测试获取统计信息"""
        logger.info("测试15: 获取统计信息")
        
        stats = self.module.get_statistics()
        
        self.assertIn("documents", stats)
        self.assertIn("solutions", stats)
        self.assertIn("tasks_and_graphs", stats)
        
        logger.info(f"  ✓ 统计信息正常")

    def test_16_save_all(self):
        """测试保存所有数据"""
        logger.info("测试16: 保存所有数据")
        
        paths = self.module.save_all()
        
        self.assertIn("documents", paths)
        self.assertIn("solutions", paths)
        self.assertIn("tasks_graphs", paths)
        
        logger.info(f"  ✓ 保存成功")

    def test_17_submodule_accessors(self):
        """测试子模块访问器"""
        logger.info("测试17: 子模块访问器")
        
        doc_service = self.module.document_service
        understanding_service = self.module.understanding_service
        decomposition_service = self.module.decomposition_service
        
        self.assertIsNotNone(doc_service)
        self.assertIsNotNone(understanding_service)
        self.assertIsNotNone(decomposition_service)
        
        logger.info("  ✓ 子模块访问正常")


if __name__ == '__main__':
    os.makedirs('logs', exist_ok=True)
    unittest.main(verbosity=2)