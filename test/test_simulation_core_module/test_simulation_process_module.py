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

from simulation_core_module.simulation_process_module import SimulationProcessModule
from bo.task_manifest import TaskManifest
from bo.task_flow_group import TaskFlowGroup
from bo.task import StartTask, EndTask, Task

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_simulation_process_module.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TestSimulationProcessModule(unittest.TestCase):
    """测试SimulationProcessModule类"""

    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        logger.info("=" * 60)
        logger.info("开始测试SimulationProcessModule")
        logger.info("=" * 60)

    def _create_test_org_manifest(self):
        """创建测试组织清单"""
        return {
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
                            "roles": ["DEV"],
                            "daily_work_hours": 8.0
                        },
                        {
                            "employee_id": "EMP002",
                            "name": "李四",
                            "department": "研发部",
                            "roles": ["TEST"],
                            "daily_work_hours": 8.0
                        }
                    ],
                    "children": []
                }
            ]
        }

    def _create_test_task_manifest(self):
        """创建测试任务清单"""
        now = datetime.now()
        
        start_task = StartTask(
            task_id="START001",
            task_name="开始",
            expected_start_time=now,
            expected_end_time=now,
            content="流程开始",
            task_source=None,
            execute_role="__START__",
            resource_consumption=0.0,
            priority="low",
            output_target_role="DEV",
            task_destinations=["T001"]
        )
        
        dev_task = Task(
            task_id="T001",
            task_name="开发任务",
            expected_start_time=now,
            expected_end_time=now,
            content="开发模块",
            task_source="START001",
            execute_role="DEV",
            resource_consumption=1.0,
            priority="high",
            output_target_role="TEST",
            task_destinations=["T002"]
        )
        
        test_task = Task(
            task_id="T002",
            task_name="测试任务",
            expected_start_time=now,
            expected_end_time=now,
            content="测试模块",
            task_source="T001",
            execute_role="TEST",
            resource_consumption=0.5,
            priority="high",
            output_target_role="",
            task_destinations=["END001"]
        )
        
        end_task = EndTask(
            task_id="END001",
            task_name="结束",
            expected_start_time=now,
            expected_end_time=now,
            content="流程结束",
            task_source="T002",
            execute_role="__END__",
            resource_consumption=0.0,
            priority="low",
            output_target_role="",
            task_destinations=[]
        )
        
        flow_group = TaskFlowGroup(
            flow_id="FLOW001",
            flow_name="开发流程",
            tasks=[start_task, dev_task, test_task, end_task]
        )
        
        return TaskManifest(
            manifest_id="TEST_MANIFEST_001",
            manifest_name="测试清单",
            flow_groups=[flow_group],
            status="active"
        )

    def test_01_start(self):
        """测试启动仿真流程模块"""
        logger.info("测试01: 启动仿真流程模块")
        
        module = SimulationProcessModule()
        
        result = module.start()
        
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "仿真流程模块已启动")
        
        logger.info("  ✓ 启动成功")

    def test_02_start_already_running(self):
        """测试启动已运行的模块"""
        logger.info("测试02: 启动已运行的模块")
        
        module = SimulationProcessModule()
        module.start()
        
        result = module.start()
        
        self.assertFalse(result["success"])
        self.assertIn("已启动", result["message"])
        
        logger.info("  ✓ 重复启动处理正常")

    def test_03_stop(self):
        """测试停止仿真流程模块"""
        logger.info("测试03: 停止仿真流程模块")
        
        module = SimulationProcessModule()
        module.start()
        
        result = module.stop()
        
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "仿真流程模块已停止")
        
        logger.info("  ✓ 停止成功")

    def test_04_stop_not_running(self):
        """测试停止未运行的模块"""
        logger.info("测试04: 停止未运行的模块")
        
        module = SimulationProcessModule()
        
        result = module.stop()
        
        self.assertFalse(result["success"])
        self.assertIn("未启动", result["message"])
        
        logger.info("  ✓ 错误处理正常")

    def test_05_get_status(self):
        """测试获取模块状态"""
        logger.info("测试05: 获取模块状态")
        
        module = SimulationProcessModule()
        
        status = module.get_status()
        
        self.assertIn("is_running", status)
        self.assertIn("process_engine_initialized", status)
        self.assertIn("dispatched_manifests", status)
        
        self.assertFalse(status["is_running"])
        
        logger.info("  ✓ 状态获取正常")

    def test_06_dispatch_manifest(self):
        """测试分派任务清单"""
        logger.info("测试06: 分派任务清单")
        
        org_manifest = self._create_test_org_manifest()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(org_manifest, f, ensure_ascii=False)
            org_file = f.name
        
        try:
            module = SimulationProcessModule()
            
            def run_module():
                module.start()
                while module._is_running:
                    time.sleep(0.1)
            
            thread = threading.Thread(target=run_module, daemon=True)
            thread.start()
            
            time.sleep(2)
            
            module.init_process_engine(org_file)
            
            task_manifest = self._create_test_task_manifest()
            
            result = module.dispatch_manifest(task_manifest)
            
            self.assertTrue(result["success"])
            self.assertEqual(result["manifest_id"], "TEST_MANIFEST_001")
            
            module.stop()
            time.sleep(1)
            
            logger.info("  ✓ 分派成功")
        finally:
            os.remove(org_file)

    def test_07_dispatch_manifest_without_init(self):
        """测试未初始化引擎时分派任务清单"""
        logger.info("测试07: 未初始化引擎时分派任务清单")
        
        module = SimulationProcessModule()
        module.start()
        
        task_manifest = self._create_test_task_manifest()
        
        result = module.dispatch_manifest(task_manifest)
        
        self.assertFalse(result["success"])
        self.assertIn("未初始化", result["message"])
        
        module.stop()
        
        logger.info("  ✓ 错误处理正常")

    def test_08_dispatch_manifest_not_running(self):
        """测试模块未运行时分派任务清单"""
        logger.info("测试08: 模块未运行时分派任务清单")
        
        module = SimulationProcessModule()
        
        task_manifest = self._create_test_task_manifest()
        
        result = module.dispatch_manifest(task_manifest)
        
        self.assertFalse(result["success"])
        self.assertIn("未启动", result["message"])
        
        logger.info("  ✓ 错误处理正常")

    def test_09_init_process_engine(self):
        """测试初始化流程引擎"""
        logger.info("测试09: 初始化流程引擎")
        
        org_manifest = self._create_test_org_manifest()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(org_manifest, f, ensure_ascii=False)
            org_file = f.name
        
        try:
            module = SimulationProcessModule()
            module.start()
            
            result = module.init_process_engine(org_file)
            
            self.assertTrue(result["success"])
            
            status = module.get_status()
            self.assertTrue(status["process_engine_initialized"])
            
            module.stop()
            
            logger.info("  ✓ 初始化成功")
        finally:
            os.remove(org_file)

    def test_10_init_process_engine_without_start(self):
        """测试模块未启动时初始化引擎"""
        logger.info("测试10: 模块未启动时初始化引擎")
        
        org_manifest = self._create_test_org_manifest()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(org_manifest, f, ensure_ascii=False)
            org_file = f.name
        
        try:
            module = SimulationProcessModule()
            
            result = module.init_process_engine(org_file)
            
            self.assertFalse(result["success"])
            self.assertIn("未启动", result["message"])
            
            logger.info("  ✓ 错误处理正常")
        finally:
            os.remove(org_file)

    def test_11_init_process_engine_invalid_path(self):
        """测试使用无效路径初始化引擎"""
        logger.info("测试11: 使用无效路径初始化引擎")
        
        module = SimulationProcessModule()
        module.start()
        
        result = module.init_process_engine("invalid_path.json")
        
        self.assertFalse(result["success"])
        self.assertIn("不存在", result["message"])
        
        module.stop()
        
        logger.info("  ✓ 错误处理正常")

    def test_12_reset(self):
        """测试重置模块"""
        logger.info("测试12: 重置模块")
        
        org_manifest = self._create_test_org_manifest()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(org_manifest, f, ensure_ascii=False)
            org_file = f.name
        
        try:
            module = SimulationProcessModule()
            module.start()
            module.init_process_engine(org_file)
            
            status = module.get_status()
            self.assertTrue(status["process_engine_initialized"])
            
            result = module.reset()
            
            self.assertTrue(result["success"])
            
            status = module.get_status()
            self.assertFalse(status["process_engine_initialized"])
            
            module.stop()
            
            logger.info("  ✓ 重置成功")
        finally:
            os.remove(org_file)

    def test_13_get_process_engine(self):
        """测试获取流程引擎"""
        logger.info("测试13: 获取流程引擎")
        
        module = SimulationProcessModule()
        
        engine = module.get_process_engine()
        
        self.assertIsNotNone(engine)
        
        logger.info("  ✓ 获取成功")

    def test_14_get_dispatch_engine(self):
        """测试获取分派引擎"""
        logger.info("测试14: 获取分派引擎")
        
        module = SimulationProcessModule()
        
        engine = module.get_dispatch_engine()
        
        self.assertIsNotNone(engine)
        
        logger.info("  ✓ 获取成功")

    def test_15_clear_dispatched_manifests(self):
        """测试清除已分派的清单"""
        logger.info("测试15: 清除已分派的清单")
        
        org_manifest = self._create_test_org_manifest()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(org_manifest, f, ensure_ascii=False)
            org_file = f.name
        
        try:
            module = SimulationProcessModule()
            
            def run_module():
                module.start()
                while module._is_running:
                    time.sleep(0.1)
            
            thread = threading.Thread(target=run_module, daemon=True)
            thread.start()
            
            time.sleep(2)
            
            module.init_process_engine(org_file)
            
            task_manifest = self._create_test_task_manifest()
            module.dispatch_manifest(task_manifest)
            
            status = module.get_status()
            self.assertEqual(len(status["dispatched_manifests"]), 1)
            
            module.clear_dispatched_manifests()
            
            status = module.get_status()
            self.assertEqual(len(status["dispatched_manifests"]), 0)
            
            module.stop()
            time.sleep(1)
            
            logger.info("  ✓ 清除成功")
        finally:
            os.remove(org_file)


if __name__ == '__main__':
    os.makedirs('logs', exist_ok=True)
    unittest.main(verbosity=2)