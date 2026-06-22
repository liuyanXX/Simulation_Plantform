import os
import sys
import logging
import unittest
import json
import tempfile
from datetime import datetime
import threading
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from simulation_core_module.simulation_process_engine import SimulationProcessEngine
from bo.task import Task, StartTask, EndTask

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_simulation_process_engine.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TestSimulationProcessEngine(unittest.TestCase):
    """测试SimulationProcessEngine类"""

    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        logger.info("=" * 60)
        logger.info("开始测试SimulationProcessEngine")
        logger.info("=" * 60)
        
        cls.sample_org_manifest = {
            "org_id": "ROOT",
            "name": "总公司",
            "workers": [],
            "children": [
                {
                    "org_id": "RD",
                    "name": "研发部",
                    "workers": [
                        {
                            "employee_id": "EMP001",
                            "name": "张三",
                            "department": "研发部",
                            "roles": ["DEV", "TEST"],
                            "daily_work_hours": 8.0
                        },
                        {
                            "employee_id": "EMP002",
                            "name": "李四",
                            "department": "研发部",
                            "roles": ["DEV"],
                            "daily_work_hours": 8.0
                        }
                    ],
                    "children": [
                        {
                            "org_id": "RD-FE",
                            "name": "前端开发组",
                            "workers": [
                                {
                                    "employee_id": "EMP003",
                                    "name": "王五",
                                    "department": "前端开发组",
                                    "roles": ["DEV"],
                                    "daily_work_hours": 8.0
                                }
                            ],
                            "children": []
                        }
                    ]
                },
                {
                    "org_id": "QA",
                    "name": "测试部",
                    "workers": [
                        {
                            "employee_id": "EMP004",
                            "name": "赵六",
                            "department": "测试部",
                            "roles": ["TEST", "QA"],
                            "daily_work_hours": 8.0
                        }
                    ],
                    "children": []
                }
            ]
        }

    def test_01_parse_organization_manifest(self):
        """测试解析组织清单"""
        logger.info("测试01: 解析组织清单")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(self.sample_org_manifest, f, ensure_ascii=False)
            temp_file = f.name
        
        try:
            engine = SimulationProcessEngine()
            root_org = engine.parse_organization_manifest(temp_file)
            
            self.assertIsNotNone(root_org)
            self.assertEqual(root_org.org_id, "ROOT")
            
            organizations = engine.get_all_organizations()
            self.assertEqual(len(organizations), 4)
            
            logger.info(f"  ✓ 解析完成: {len(organizations)}个组织")
        finally:
            os.remove(temp_file)

    def test_02_parse_invalid_manifest(self):
        """测试解析无效清单（应报错）"""
        logger.info("测试02: 解析无效清单（应报错）")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            f.write("invalid json")
            temp_file = f.name
        
        try:
            engine = SimulationProcessEngine()
            with self.assertRaises(ValueError):
                engine.parse_organization_manifest(temp_file)
            
            logger.info("  ✓ JSON解析错误处理正常")
        finally:
            os.remove(temp_file)

    def test_03_parse_missing_fields_manifest(self):
        """测试解析缺少字段的清单（应报错）"""
        logger.info("测试03: 解析缺少字段的清单（应报错）")
        
        invalid_manifest = {"name": "测试"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(invalid_manifest, f, ensure_ascii=False)
            temp_file = f.name
        
        try:
            engine = SimulationProcessEngine()
            with self.assertRaises(ValueError):
                engine.parse_organization_manifest(temp_file)
            
            logger.info("  ✓ 字段检查错误处理正常")
        finally:
            os.remove(temp_file)

    def test_04_initialize_workers(self):
        """测试初始化员工"""
        logger.info("测试04: 初始化员工")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(self.sample_org_manifest, f, ensure_ascii=False)
            temp_file = f.name
        
        try:
            engine = SimulationProcessEngine()
            engine.parse_organization_manifest(temp_file)
            engine.initialize_workers()
            
            workers = engine.get_all_workers()
            self.assertEqual(len(workers), 5)
            
            role_registry = engine.get_role_registry()
            self.assertIn("DEV", role_registry)
            self.assertIn("TEST", role_registry)
            self.assertIn("__START__", role_registry)
            
            start_worker = engine.get_worker("__START_WORKER__")
            self.assertIsNotNone(start_worker)
            
            logger.info(f"  ✓ 初始化完成: {len(workers)}名员工, {len(role_registry)}个角色")
        finally:
            os.remove(temp_file)

    def test_05_initialize_workers_without_manifest(self):
        """测试未解析清单时初始化员工（应报错）"""
        logger.info("测试05: 未解析清单时初始化员工（应报错）")
        
        engine = SimulationProcessEngine()
        
        with self.assertRaises(ValueError):
            engine.initialize_workers()
        
        logger.info("  ✓ 错误处理正常")

    def test_06_get_organization(self):
        """测试获取组织"""
        logger.info("测试06: 获取组织")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(self.sample_org_manifest, f, ensure_ascii=False)
            temp_file = f.name
        
        try:
            engine = SimulationProcessEngine()
            engine.parse_organization_manifest(temp_file)
            
            org = engine.get_organization("RD")
            
            self.assertIsNotNone(org)
            self.assertEqual(org.org_id, "RD")
            self.assertEqual(org.name, "研发部")
            
            logger.info(f"  ✓ 获取成功: {org.name}")
        finally:
            os.remove(temp_file)

    def test_07_get_worker(self):
        """测试获取员工"""
        logger.info("测试07: 获取员工")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(self.sample_org_manifest, f, ensure_ascii=False)
            temp_file = f.name
        
        try:
            engine = SimulationProcessEngine()
            engine.parse_organization_manifest(temp_file)
            engine.initialize_workers()
            
            worker = engine.get_worker("EMP001")
            
            self.assertIsNotNone(worker)
            self.assertEqual(worker.employee_id, "EMP001")
            self.assertEqual(worker.name, "张三")
            
            logger.info(f"  ✓ 获取成功: {worker.name}")
        finally:
            os.remove(temp_file)

    def test_08_assign_initial_tasks(self):
        """测试分配初始任务"""
        logger.info("测试08: 分配初始任务")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(self.sample_org_manifest, f, ensure_ascii=False)
            temp_file = f.name
        
        try:
            engine = SimulationProcessEngine()
            engine.parse_organization_manifest(temp_file)
            engine.initialize_workers()
            
            now = datetime.now()
            task = Task(
                task_id="TASK001",
                task_name="开发任务",
                expected_start_time=now,
                expected_end_time=now,
                content="开发内容",
                execute_role="DEV",
                resource_consumption=1.0,
                priority="high",
                output_target_role="TEST"
            )
            
            engine.assign_initial_tasks([task])
            
            worker = engine.get_worker("EMP001")
            self.assertTrue(worker.has_pending_tasks())
            
            logger.info("  ✓ 任务分配成功")
        finally:
            os.remove(temp_file)

    def test_09_assign_start_task(self):
        """测试分配启动任务"""
        logger.info("测试09: 分配启动任务")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(self.sample_org_manifest, f, ensure_ascii=False)
            temp_file = f.name
        
        try:
            engine = SimulationProcessEngine()
            engine.parse_organization_manifest(temp_file)
            engine.initialize_workers()
            
            now = datetime.now()
            start_task = StartTask(
                task_id="START001",
                task_name="开始任务",
                expected_start_time=now,
                expected_end_time=now,
                content="开始",
                task_source=None,
                execute_role="__START__",
                resource_consumption=0.0,
                priority="low",
                output_target_role="DEV",
                task_destinations=["TASK001"]
            )
            
            engine.assign_initial_tasks([start_task])
            
            start_worker = engine.get_worker("__START_WORKER__")
            self.assertTrue(start_worker.has_pending_tasks())
            
            logger.info("  ✓ 启动任务分配成功")
        finally:
            os.remove(temp_file)

    def test_10_assign_task_to_nonexistent_role(self):
        """测试分配任务给不存在的角色"""
        logger.info("测试10: 分配任务给不存在的角色")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(self.sample_org_manifest, f, ensure_ascii=False)
            temp_file = f.name
        
        try:
            engine = SimulationProcessEngine()
            engine.parse_organization_manifest(temp_file)
            engine.initialize_workers()
            
            now = datetime.now()
            task = Task(
                task_id="TASK_NONEXIST",
                task_name="无效角色任务",
                expected_start_time=now,
                expected_end_time=now,
                content="内容",
                execute_role="NONEXISTENT",
                resource_consumption=1.0,
                priority="high",
                output_target_role="TEST"
            )
            
            engine.assign_initial_tasks([task])
            
            logger.info("  ✓ 无效角色任务处理正常（日志警告）")
        finally:
            os.remove(temp_file)

    def test_11_get_simulation_status(self):
        """测试获取仿真状态"""
        logger.info("测试11: 获取仿真状态")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(self.sample_org_manifest, f, ensure_ascii=False)
            temp_file = f.name
        
        try:
            engine = SimulationProcessEngine()
            engine.parse_organization_manifest(temp_file)
            engine.initialize_workers()
            
            status = engine.get_simulation_status()
            
            self.assertIn("is_running", status)
            self.assertIn("organization_count", status)
            self.assertIn("worker_count", status)
            self.assertIn("role_count", status)
            self.assertIn("organizations", status)
            self.assertIn("workers", status)
            
            self.assertEqual(status["organization_count"], 4)
            self.assertEqual(status["worker_count"], 5)
            
            logger.info("  ✓ 状态获取正常")
        finally:
            os.remove(temp_file)

    def test_12_is_running(self):
        """测试运行状态检查"""
        logger.info("测试12: 运行状态检查")
        
        engine = SimulationProcessEngine()
        
        self.assertFalse(engine.is_running())
        
        logger.info("  ✓ 状态检查正常")


if __name__ == '__main__':
    os.makedirs('logs', exist_ok=True)
    unittest.main(verbosity=2)