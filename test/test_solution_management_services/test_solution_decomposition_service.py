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

from solution_management_services.solution_decomposition_service import (
    SolutionDecompositionService,
    DecompositionResult,
    TaskTemplate
)
from ai_modules.basic.llm_client import MockLLMClient
from bo.solution import Solution, SolutionStatus, SolutionPriority
from bo.task import Task, TaskType, Priority
from bo.tasks_graph import TasksGraph

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, 'test_solution_decomposition_service.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TestSolutionDecompositionService(unittest.TestCase):
    """测试SolutionDecompositionService"""

    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        logger.info("=" * 60)
        logger.info("开始测试SolutionDecompositionService")
        logger.info("=" * 60)
        
        cls.test_storage = "test_decomposition_data"
        os.makedirs(cls.test_storage, exist_ok=True)
        
        cls.llm_client = MockLLMClient()
        cls.service = SolutionDecompositionService(
            llm_client=cls.llm_client,
            storage_path=cls.test_storage
        )
        
        cls.test_solution = Solution(
            solution_id="SOL_DECOMPOSE_001",
            name="数字化转型方案",
            version="1.0",
            status=SolutionStatus.DRAFT,
            priority=SolutionPriority.HIGH,
            purpose="推动企业数字化转型",
            objectives=["实现业务流程数字化", "提升运营效率"],
            initiatives=["引入云计算平台", "建设大数据分析系统"],
            work_content="完成数字化转型的规划、实施和推广",
            organization=["研发部", "运营部"],
            roles=["项目经理", "技术负责人"]
        )
        
        cls.test_task = Task(
            task_id="TASK_TEST_001",
            task_name="测试任务",
            task_type=TaskType.NORMAL,
            content="测试任务内容",
            execute_role="PM",
            resource_consumption=2.0,
            priority=Priority.HIGH,
            output_target_role="DEV",
            task_destinations=["TASK_TEST_002"]
        )

    @classmethod
    def tearDownClass(cls):
        """清理测试数据"""
        import shutil
        if os.path.exists(cls.test_storage):
            shutil.rmtree(cls.test_storage)
        logger.info("测试数据已清理")

    def test_01_create_task(self):
        """测试创建任务"""
        logger.info("测试01: 创建任务")
        
        task = self.service.create_task(self.test_task)
        
        self.assertIsNotNone(task)
        self.assertEqual(task.task_id, "TASK_TEST_001")
        self.assertEqual(task.task_name, "测试任务")
        
        logger.info(f"  ✓ 创建成功: {task.task_id}")

    def test_02_create_duplicate_task(self):
        """测试创建重复任务"""
        logger.info("测试02: 创建重复任务（应报错）")
        
        with self.assertRaises(ValueError):
            self.service.create_task(self.test_task)
        
        logger.info("  ✓ 重复检测正常")

    def test_03_get_task(self):
        """测试获取任务"""
        logger.info("测试03: 获取任务")
        
        task = self.service.get_task("TASK_TEST_001")
        
        self.assertIsNotNone(task)
        self.assertEqual(task.task_id, "TASK_TEST_001")
        
        logger.info(f"  ✓ 获取成功: {task.task_name}")

    def test_04_get_nonexistent_task(self):
        """测试获取不存在的任务"""
        logger.info("测试04: 获取不存在的任务")
        
        task = self.service.get_task("TASK_NOT_EXIST")
        
        self.assertIsNone(task)
        logger.info("  ✓ 返回None")

    def test_05_list_tasks(self):
        """测试查询任务列表"""
        logger.info("测试05: 查询任务列表")
        
        tasks = self.service.list_tasks()
        
        self.assertTrue(len(tasks) > 0)
        logger.info(f"  ✓ 查询到 {len(tasks)} 个任务")

    def test_06_list_tasks_by_type(self):
        """测试按类型过滤任务"""
        logger.info("测试06: 按类型过滤任务")
        
        tasks = self.service.list_tasks(task_type=TaskType.NORMAL)
        
        self.assertTrue(len(tasks) >= 1)
        logger.info(f"  ✓ 找到 {len(tasks)} 个NORMAL类型任务")

    def test_07_update_task(self):
        """测试更新任务"""
        logger.info("测试07: 更新任务")
        
        updated = self.service.update_task(
            "TASK_TEST_001",
            priority=Priority.MEDIUM,
            resource_consumption=3.0
        )
        
        self.assertEqual(updated.priority, Priority.MEDIUM)
        self.assertEqual(updated.resource_consumption, 3.0)
        
        logger.info(f"  ✓ 更新成功")

    def test_08_update_nonexistent_task(self):
        """测试更新不存在的任务"""
        logger.info("测试08: 更新不存在的任务（应报错）")
        
        with self.assertRaises(ValueError):
            self.service.update_task("TASK_NOT_EXIST", priority=Priority.LOW)
        
        logger.info("  ✓ 错误处理正常")

    def test_09_delete_task(self):
        """测试删除任务"""
        logger.info("测试09: 删除任务")
        
        result = self.service.delete_task("TASK_TEST_001")
        
        self.assertTrue(result)
        self.assertIsNone(self.service.get_task("TASK_TEST_001"))
        
        logger.info("  ✓ 删除成功")

    def test_10_delete_nonexistent_task(self):
        """测试删除不存在的任务"""
        logger.info("测试10: 删除不存在的任务（应报错）")
        
        with self.assertRaises(ValueError):
            self.service.delete_task("TASK_NOT_EXIST")
        
        logger.info("  ✓ 错误处理正常")

    def test_11_create_tasks_graph(self):
        """测试创建任务图谱"""
        logger.info("测试11: 创建任务图谱")
        
        tasks = [
            Task(
                task_id="START001",
                task_name="开始",
                task_type=TaskType.START,
                content="流程开始",
                execute_role="SYSTEM",
                resource_consumption=0.0,
                priority=Priority.LOW,
                task_destinations=["TASK001"]
            ),
            Task(
                task_id="TASK001",
                task_name="执行任务",
                task_type=TaskType.NORMAL,
                content="执行测试",
                execute_role="PM",
                resource_consumption=2.0,
                priority=Priority.HIGH,
                task_destinations=["END001"]
            ),
            Task(
                task_id="END001",
                task_name="结束",
                task_type=TaskType.END,
                content="流程结束",
                execute_role="SYSTEM",
                resource_consumption=0.0,
                priority=Priority.LOW
            )
        ]
        
        tasks_graph = TasksGraph(
            graph_id="GRAPH_TEST_001",
            graph_name="测试图谱",
            tasks=tasks
        )
        
        created = self.service.create_tasks_graph(tasks_graph)
        
        self.assertIsNotNone(created)
        self.assertEqual(created.graph_id, "GRAPH_TEST_001")
        self.assertEqual(len(created.tasks), 3)
        
        logger.info(f"  ✓ 创建成功: {created.graph_id}")

    def test_12_create_duplicate_graph(self):
        """测试创建重复图谱"""
        logger.info("测试12: 创建重复图谱（应报错）")
        
        tasks_graph = TasksGraph(
            graph_id="GRAPH_TEST_001",
            graph_name="重复图谱",
            tasks=[]
        )
        
        with self.assertRaises(ValueError):
            self.service.create_tasks_graph(tasks_graph)
        
        logger.info("  ✓ 重复检测正常")

    def test_13_get_tasks_graph(self):
        """测试获取任务图谱"""
        logger.info("测试13: 获取任务图谱")
        
        tasks_graph = self.service.get_tasks_graph("GRAPH_TEST_001")
        
        self.assertIsNotNone(tasks_graph)
        self.assertEqual(tasks_graph.graph_id, "GRAPH_TEST_001")
        
        logger.info(f"  ✓ 获取成功: {tasks_graph.graph_name}")

    def test_14_get_nonexistent_graph(self):
        """测试获取不存在的图谱"""
        logger.info("测试14: 获取不存在的图谱")
        
        tasks_graph = self.service.get_tasks_graph("GRAPH_NOT_EXIST")
        
        self.assertIsNone(tasks_graph)
        logger.info("  ✓ 返回None")

    def test_15_list_tasks_graphs(self):
        """测试获取所有图谱"""
        logger.info("测试15: 获取所有任务图谱")
        
        graphs = self.service.list_tasks_graphs()
        
        self.assertTrue(len(graphs) > 0)
        logger.info(f"  ✓ 共有 {len(graphs)} 个图谱")

    def test_16_delete_tasks_graph(self):
        """测试删除任务图谱"""
        logger.info("测试16: 删除任务图谱")
        
        result = self.service.delete_tasks_graph("GRAPH_TEST_001")
        
        self.assertTrue(result)
        self.assertIsNone(self.service.get_tasks_graph("GRAPH_TEST_001"))
        
        logger.info("  ✓ 删除成功")

    def test_17_delete_nonexistent_graph(self):
        """测试删除不存在的图谱"""
        logger.info("测试17: 删除不存在的图谱（应报错）")
        
        with self.assertRaises(ValueError):
            self.service.delete_tasks_graph("GRAPH_NOT_EXIST")
        
        logger.info("  ✓ 错误处理正常")

    def test_18_decompose_solution(self):
        """测试拆解方案"""
        logger.info("测试18: 拆解方案")
        
        result = self.service.decompose_solution(self.test_solution)
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.tasks_graph)
        self.assertTrue(len(result.tasks) > 0)
        
        logger.info(f"  ✓ 拆解成功: {len(result.tasks)}个任务, 图谱ID: {result.tasks_graph.graph_id}")

    def test_19_enhance_tasks(self):
        """测试优化任务"""
        logger.info("测试19: 优化任务")
        
        # 先拆解方案获取任务
        decompose_result = self.service.decompose_solution(self.test_solution)
        
        if decompose_result.success and decompose_result.tasks:
            enhance_result = self.service.enhance_tasks(
                decompose_result.tasks,
                self.test_solution
            )
            
            self.assertTrue(enhance_result.success)
            logger.info(f"  ✓ 任务优化成功: {len(enhance_result.tasks)}个任务")
        else:
            logger.info("  - 跳过优化测试（拆解失败）")

    def test_20_save_tasks_graph(self):
        """测试保存任务图谱"""
        logger.info("测试20: 保存任务图谱")
        
        # 确保有图谱可保存
        result = self.service.decompose_solution(self.test_solution)
        
        if result.success:
            path = self.service.save_tasks_graph(result.tasks_graph.graph_id)
            
            self.assertTrue(os.path.exists(path))
            logger.info(f"  ✓ 保存成功: {path}")

    def test_21_save_all_tasks_graphs(self):
        """测试保存所有任务图谱"""
        logger.info("测试21: 保存所有任务图谱")
        
        paths = self.service.save_all_tasks_graphs()
        
        self.assertTrue(len(paths) >= 1)
        logger.info(f"  ✓ 保存了 {len(paths)} 个图谱")

    def test_22_load_tasks_graph(self):
        """测试加载任务图谱"""
        logger.info("测试22: 加载任务图谱")
        
        new_service = SolutionDecompositionService(
            llm_client=self.llm_client,
            storage_path=self.test_storage
        )
        
        # 查找并加载一个图谱文件
        for file_name in os.listdir(self.test_storage):
            if file_name.endswith('.json'):
                file_path = os.path.join(self.test_storage, file_name)
                loaded = new_service.load_tasks_graph(file_path)
                
                self.assertIsNotNone(loaded)
                self.assertTrue(len(loaded.tasks) > 0)
                logger.info(f"  ✓ 加载成功: {loaded.graph_id}")
                break

    def test_23_get_task_count(self):
        """测试获取任务数量"""
        logger.info("测试23: 获取任务数量")
        
        count = self.service.get_task_count()
        
        self.assertTrue(count >= 1)
        logger.info(f"  ✓ 任务数量: {count}")

    def test_24_get_tasks_graph_count(self):
        """测试获取图谱数量"""
        logger.info("测试24: 获取图谱数量")
        
        count = self.service.get_tasks_graph_count()
        
        self.assertTrue(count >= 1)
        logger.info(f"  ✓ 图谱数量: {count}")

    def test_25_get_statistics(self):
        """测试获取统计信息"""
        logger.info("测试25: 获取统计信息")
        
        stats = self.service.get_statistics()
        
        self.assertIn("total_tasks", stats)
        self.assertIn("total_graphs", stats)
        self.assertIn("task_type_distribution", stats)
        self.assertIn("priority_distribution", stats)
        self.assertIn("role_distribution", stats)
        
        logger.info(f"  ✓ 统计信息: {stats}")


if __name__ == '__main__':
    os.makedirs('logs', exist_ok=True)
    unittest.main(verbosity=2)