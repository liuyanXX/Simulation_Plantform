import os
import sys
import logging
import unittest
import json
import shutil
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from solution_management_services import (
    SolutionManagementModule,
    SolutionManagementService,
    SolutionUnderstandingService,
    SolutionDecompositionService
)
from ai_modules.basic.llm_client import MockLLMClient, LLMRequest
from bo.solution import Solution, SolutionDocument, SolutionStatus, SolutionPriority
from bo.task import Task, TaskType, Priority
from bo.tasks_graph import TasksGraph

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_solution_management_integration.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TestIntegration(unittest.TestCase):
    """组合调用测试 - 验证方案管理服务模块各组件协作"""

    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        logger.info("=" * 80)
        logger.info("开始方案管理服务模块组合调用测试")
        logger.info("=" * 80)
        
        cls.test_storage = "test_integration_module_data"
        os.makedirs(cls.test_storage, exist_ok=True)
        
        cls.llm_client = MockLLMClient()
        cls.module = SolutionManagementModule(
            llm_client=cls.llm_client,
            storage_base_path=cls.test_storage
        )

    @classmethod
    def tearDownClass(cls):
        """清理测试数据"""
        if os.path.exists(cls.test_storage):
            shutil.rmtree(cls.test_storage)
        logger.info("测试数据已清理")

    def test_01_full_document_to_graph_workflow(self):
        """测试01: 完整流程 - 文档 -> 方案 -> 任务图谱"""
        logger.info("测试01: 完整流程 - 文档 -> 方案 -> 任务图谱")
        
        # 1. 创建文档
        doc = self.module.create_document_from_text(
            document_id="DOC_INTEGRATE_001",
            text_content="数字化转型实施方案。目标：实现业务流程数字化，提升运营效率。举措：引入云计算平台，建设大数据分析系统。",
            file_name="digital_transformation.txt",
            version="1.0"
        )
        logger.info(f"  1. 创建文档: {doc.document_id}")
        
        # 2. 验证文档存在
        self.assertIsNotNone(self.module.get_document("DOC_INTEGRATE_001"))
        
        # 3. 理解文档 -> 方案
        solution = self.module.understand_document("DOC_INTEGRATE_001")
        logger.info(f"  2. 理解文档 -> 方案: {solution.solution_id}")
        self.assertIsNotNone(solution)
        
        # 4. 验证方案存在
        self.assertIsNotNone(self.module.get_solution(solution.solution_id))
        
        # 5. 拆解方案 -> 任务图谱
        tasks_graph = self.module.decompose_solution(solution.solution_id)
        logger.info(f"  3. 拆解方案 -> 任务图谱: {tasks_graph.graph_id}, {len(tasks_graph.tasks)}个任务")
        self.assertIsNotNone(tasks_graph)
        self.assertTrue(len(tasks_graph.tasks) > 0)
        
        # 6. 验证任务图谱存在
        self.assertIsNotNone(self.module.get_tasks_graph(tasks_graph.graph_id))
        
        logger.info("  ✓ 完整流程测试通过")

    def test_02_multiple_documents_full_workflow(self):
        """测试02: 多文档完整工作流"""
        logger.info("测试02: 多文档完整工作流")
        
        doc_ids = ["DOC_MULTI_001", "DOC_MULTI_002"]
        solutions = []
        
        for doc_id in doc_ids:
            # 创建文档
            doc = self.module.create_document_from_text(
                document_id=doc_id,
                text_content=f"方案{doc_id}的内容描述。目标：提升效率。举措：引入新技术。"
            )
            
            # 理解 -> 方案
            solution = self.module.understand_document(doc_id)
            if solution:
                solutions.append(solution)
                
                # 拆解 -> 任务
                tasks_graph = self.module.decompose_solution(solution.solution_id)
                self.assertIsNotNone(tasks_graph)
        
        logger.info(f"  ✓ 处理了 {len(doc_ids)} 个文档，生成了 {len(solutions)} 个方案")
        
        # 验证统计信息
        stats = self.module.get_statistics()
        self.assertGreater(stats["documents"]["total_count"], 0)
        self.assertGreater(stats["solutions"]["total_count"], 0)
        self.assertGreater(stats["tasks_and_graphs"]["total_tasks"], 0)

    def test_03_document_crud_workflow(self):
        """测试03: 文档CRUD工作流"""
        logger.info("测试03: 文档CRUD工作流")
        
        # 创建
        doc = self.module.create_document_from_text(
            document_id="DOC_CRUD_001",
            text_content="CRUD测试内容"
        )
        self.assertIsNotNone(doc)
        logger.info("  1. 创建文档")
        
        # 读取
        retrieved = self.module.get_document("DOC_CRUD_001")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.document_id, "DOC_CRUD_001")
        logger.info("  2. 读取文档")
        
        # 更新
        doc_service = self.module.document_service
        updated = doc_service.update_document_content("DOC_CRUD_001", "更新后的内容")
        self.assertEqual(updated.text_content, "更新后的内容")
        logger.info("  3. 更新文档")
        
        # 删除
        result = doc_service.delete_document("DOC_CRUD_001")
        self.assertTrue(result)
        self.assertIsNone(self.module.get_document("DOC_CRUD_001"))
        logger.info("  4. 删除文档")
        
        logger.info("  ✓ CRUD工作流正常")

    def test_04_solution_crud_with_understanding_service(self):
        """测试04: 方案理解服务CRUD"""
        logger.info("测试04: 方案理解服务CRUD")
        
        understanding_service = self.module.understanding_service
        
        # 创建方案
        solution = Solution(
            solution_id="SOL_CRUD_001",
            name="CRUD方案",
            version="1.0",
            status=SolutionStatus.DRAFT,
            priority=SolutionPriority.HIGH,
            purpose="CRUD测试",
            objectives=["目标1", "目标2"]
        )
        
        created = understanding_service.create_solution(solution)
        self.assertIsNotNone(created)
        logger.info("  1. 创建方案")
        
        # 读取
        retrieved = understanding_service.get_solution("SOL_CRUD_001")
        self.assertIsNotNone(retrieved)
        logger.info("  2. 读取方案")
        
        # 更新
        updated = understanding_service.update_solution(
            "SOL_CRUD_001",
            version="2.0",
            status=SolutionStatus.REVIEW
        )
        self.assertEqual(updated.version, "2.0")
        self.assertEqual(updated.status, SolutionStatus.REVIEW)
        logger.info("  3. 更新方案")
        
        # 查询
        solutions = understanding_service.list_solutions(status=SolutionStatus.REVIEW)
        self.assertTrue(len(solutions) >= 1)
        logger.info("  4. 查询方案")
        
        # 删除
        understanding_service.delete_solution("SOL_CRUD_001")
        self.assertIsNone(understanding_service.get_solution("SOL_CRUD_001"))
        logger.info("  5. 删除方案")
        
        logger.info("  ✓ 方案CRUD工作流正常")

    def test_05_decomposition_crud(self):
        """测试05: 方案拆解CRUD"""
        logger.info("测试05: 方案拆解CRUD")
        
        decomposition_service = self.module.decomposition_service
        
        # 创建任务
        tasks = [
            Task(
                task_id="INT_TASK_001",
                task_name="任务1",
                task_type=TaskType.START,
                content="开始",
                execute_role="SYSTEM",
                resource_consumption=0.0,
                priority=Priority.LOW,
                task_destinations=["INT_TASK_002"]
            ),
            Task(
                task_id="INT_TASK_002",
                task_name="任务2",
                task_type=TaskType.NORMAL,
                content="执行",
                execute_role="PM",
                resource_consumption=1.0,
                priority=Priority.HIGH,
                task_destinations=["INT_TASK_003"]
            ),
            Task(
                task_id="INT_TASK_003",
                task_name="任务3",
                task_type=TaskType.END,
                content="结束",
                execute_role="SYSTEM",
                resource_consumption=0.0,
                priority=Priority.LOW
            )
        ]
        
        for task in tasks:
            created = decomposition_service.create_task(task)
            self.assertIsNotNone(created)
        logger.info("  1. 创建任务")
        
        # 读取
        retrieved = decomposition_service.get_task("INT_TASK_001")
        self.assertIsNotNone(retrieved)
        logger.info("  2. 读取任务")
        
        # 更新
        updated = decomposition_service.update_task(
            "INT_TASK_002",
            resource_consumption=2.0
        )
        self.assertEqual(updated.resource_consumption, 2.0)
        logger.info("  3. 更新任务")
        
        # 创建图谱
        tasks_graph = TasksGraph(
            graph_id="INT_GRAPH_001",
            graph_name="集成测试图谱",
            tasks=tasks
        )
        created_graph = decomposition_service.create_tasks_graph(tasks_graph)
        self.assertIsNotNone(created_graph)
        logger.info("  4. 创建任务图谱")
        
        # 删除
        decomposition_service.delete_tasks_graph("INT_GRAPH_001")
        for task in tasks:
            decomposition_service.delete_task(task.task_id)
        logger.info("  5. 删除任务和图谱")
        
        logger.info("  ✓ 拆解CRUD工作流正常")

    def test_06_service_interaction(self):
        """测试06: 服务间交互"""
        logger.info("测试06: 服务间交互")
        
        # 创建文档
        doc = self.module.create_document_from_text(
            document_id="DOC_INTERACT_001",
            text_content="交互测试文档。目的：测试服务间协作。目标：验证模块间通信。举措：创建文档并处理。"
        )
        
        # 文档服务 -> 理解服务
        solution = self.module.process_document_to_solution("DOC_INTERACT_001")
        self.assertIsNotNone(solution)
        logger.info("  1. 文档 -> 方案")
        
        # 理解服务 -> 拆解服务
        tasks_graph = self.module.process_solution_to_tasks(solution.solution_id)
        self.assertIsNotNone(tasks_graph)
        logger.info("  2. 方案 -> 任务图谱")
        
        # 验证所有数据可通过主模块访问
        self.assertIsNotNone(self.module.get_document("DOC_INTERACT_001"))
        self.assertIsNotNone(self.module.get_solution(solution.solution_id))
        self.assertIsNotNone(self.module.get_tasks_graph(tasks_graph.graph_id))
        logger.info("  3. 数据验证通过")
        
        logger.info("  ✓ 服务间交互正常")

    def test_07_save_and_load(self):
        """测试07: 保存和加载"""
        logger.info("测试07: 保存和加载")
        
        # 先处理一个文档
        doc = self.module.create_document_from_text(
            document_id="DOC_SAVE_001",
            text_content="保存测试文档"
        )
        solution = self.module.understand_document("DOC_SAVE_001")
        if solution:
            self.module.decompose_solution(solution.solution_id)
        
        # 保存所有
        paths = self.module.save_all()
        logger.info(f"  1. 保存所有数据")
        self.assertTrue(len(paths["documents"]) > 0)
        
        # 创建新模块并加载
        new_module = SolutionManagementModule(
            llm_client=self.llm_client,
            storage_base_path=self.test_storage
        )
        
        # 从文件加载
        new_module.document_service.load_all_documents()
        new_module.understanding_service.load_all_solutions()
        
        # 验证加载的数据
        self.assertIsNotNone(new_module.document_service.get_document("DOC_SAVE_001"))
        logger.info("  2. 加载数据并验证")
        
        logger.info("  ✓ 保存加载正常")

    def test_08_filter_and_search(self):
        """测试08: 过滤和搜索"""
        logger.info("测试08: 过滤和搜索")
        
        # 创建多个不同类型文档
        docs_data = [
            ("DOC_FILTER_001", "main_doc.txt", "这是主文档内容"),
            ("DOC_FILTER_002", "supplement.txt", "这是补充文档"),
        ]
        
        for doc_id, file_name, content in docs_data:
            self.module.create_document_from_text(
                document_id=doc_id,
                text_content=content,
                file_name=file_name
            )
        
        # 测试文档查询过滤
        from solution_management_services.solution_management_service import DocumentQueryFilter
        filter_condition = DocumentQueryFilter(keyword="主文档")
        results = self.module.document_service.list_documents(filter_condition)
        self.assertTrue(len(results) >= 1)
        logger.info(f"  1. 文档关键词搜索: {len(results)}个结果")
        
        # 测试方案查询
        # 先创建方案
        solution1 = Solution(
            solution_id="SOL_SEARCH_001",
            name="搜索测试方案",
            version="1.0",
            status=SolutionStatus.DRAFT,
            priority=SolutionPriority.HIGH,
            purpose="搜索测试",
            objectives=["目标1"]
        )
        self.module.understanding_service.create_solution(solution1)
        
        results = self.module.understanding_service.list_solutions(keyword="搜索")
        self.assertTrue(len(results) >= 1)
        logger.info(f"  2. 方案关键词搜索: {len(results)}个结果")
        
        logger.info("  ✓ 过滤搜索正常")

    def test_09_statistics(self):
        """测试09: 统计信息"""
        logger.info("测试09: 统计信息")
        
        stats = self.module.get_statistics()
        
        # 验证文档统计
        self.assertIn("total_count", stats["documents"])
        self.assertIn("type_distribution", stats["documents"])
        
        # 验证方案统计
        self.assertIn("total_count", stats["solutions"])
        self.assertIn("status_distribution", stats["solutions"])
        self.assertIn("priority_distribution", stats["solutions"])
        
        # 验证任务统计
        self.assertIn("total_tasks", stats["tasks_and_graphs"])
        self.assertIn("task_type_distribution", stats["tasks_and_graphs"])
        self.assertIn("priority_distribution", stats["tasks_and_graphs"])
        self.assertIn("role_distribution", stats["tasks_and_graphs"])
        
        logger.info(f"  ✓ 统计信息完整")

    def test_10_error_handling(self):
        """测试10: 错误处理"""
        logger.info("测试10: 错误处理")
        
        # 测试不存在的文档处理
        result = self.module.process_document_full("DOC_NOT_EXIST")
        self.assertFalse(result.success)
        self.assertTrue(len(result.errors) > 0)
        logger.info("  1. 不存在的文档处理正常")
        
        # 测试不存在的方案拆解
        tasks_graph = self.module.process_solution_to_tasks("SOL_NOT_EXIST")
        self.assertIsNone(tasks_graph)
        logger.info("  2. 不存在的方案处理正常")
        
        # 测试文档不存在时的获取
        doc = self.module.get_document("NONEXISTENT")
        self.assertIsNone(doc)
        logger.info("  3. 获取不存在的文档正常")
        
        # 测试删除不存在的文档
        with self.assertRaises(ValueError):
            self.module.document_service.delete_document("NONEXISTENT")
        logger.info("  4. 删除不存在的文档错误处理正常")
        
        logger.info("  ✓ 错误处理正常")


if __name__ == '__main__':
    os.makedirs('logs', exist_ok=True)
    unittest.main(verbosity=2)