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

from simulation_core_module.task_dispatch_engine import TaskDispatchEngine
from simulation_core_module.simulation_process_engine import SimulationProcessEngine
from bo.task_manifest import TaskManifest
from bo.task_flow_group import TaskFlowGroup
from bo.task import StartTask, EndTask, Task

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_task_dispatch_engine.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TestTaskDispatchEngine(unittest.TestCase):
    """测试TaskDispatchEngine类"""

    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        logger.info("=" * 60)
        logger.info("开始测试TaskDispatchEngine")
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

    def _create_test_manifest(self):
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

    def test_01_set_process_engine(self):
        """测试设置仿真流程引擎"""
        logger.info("测试01: 设置仿真流程引擎")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(self.sample_org_manifest, f, ensure_ascii=False)
            temp_file = f.name
        
        try:
            process_engine = SimulationProcessEngine(temp_file)
            dispatch_engine = TaskDispatchEngine()
            
            dispatch_engine.set_process_engine(process_engine)
            
            self.assertEqual(dispatch_engine._process_engine, process_engine)
            
            logger.info("  ✓ 设置成功")
        finally:
            os.remove(temp_file)

    def test_02_validate_manifest(self):
        """测试验证任务清单"""
        logger.info("测试02: 验证任务清单")
        
        manifest = self._create_test_manifest()
        dispatch_engine = TaskDispatchEngine()
        
        errors = dispatch_engine.validate_manifest(manifest)
        
        self.assertEqual(len(errors), 0)
        
        logger.info("  ✓ 验证通过")

    def test_03_validate_invalid_manifest(self):
        """测试验证无效任务清单"""
        logger.info("测试03: 验证无效任务清单")
        
        invalid_manifest = TaskManifest(
            manifest_id="",
            manifest_name="",
            flow_groups=[],
            status="active"
        )
        
        dispatch_engine = TaskDispatchEngine()
        
        errors = dispatch_engine.validate_manifest(invalid_manifest)
        
        self.assertTrue(len(errors) > 0)
        
        logger.info(f"  ✓ 验证失败，发现 {len(errors)} 个问题")

    def test_04_validate_manifest_missing_start_task(self):
        """测试验证缺少起始任务的清单"""
        logger.info("测试04: 验证缺少起始任务的清单")
        
        now = datetime.now()
        
        end_task = EndTask(
            task_id="END001",
            task_name="结束",
            expected_start_time=now,
            expected_end_time=now,
            content="流程结束",
            task_source=None,
            execute_role="__END__",
            resource_consumption=0.0,
            priority="low",
            output_target_role="",
            task_destinations=[]
        )
        
        flow_group = TaskFlowGroup(
            flow_id="FLOW001",
            flow_name="流程",
            tasks=[end_task]
        )
        
        manifest = TaskManifest(
            manifest_id="INVALID_001",
            manifest_name="无效清单",
            flow_groups=[flow_group],
            status="active"
        )
        
        dispatch_engine = TaskDispatchEngine()
        
        errors = dispatch_engine.validate_manifest(manifest)
        
        self.assertTrue(len(errors) > 0)
        
        logger.info("  ✓ 缺少起始任务检测正常")

    def test_05_split_manifest_to_flow_groups(self):
        """测试拆解清单为任务流组"""
        logger.info("测试05: 拆解清单为任务流组")
        
        manifest = self._create_test_manifest()
        dispatch_engine = TaskDispatchEngine()
        
        flow_groups = dispatch_engine.split_manifest_to_flow_groups(manifest)
        
        self.assertEqual(len(flow_groups), 1)
        self.assertEqual(flow_groups[0].flow_id, "FLOW001")
        
        logger.info("  ✓ 拆解成功")

    def test_06_extract_start_tasks(self):
        """测试提取起始任务"""
        logger.info("测试06: 提取起始任务")
        
        manifest = self._create_test_manifest()
        dispatch_engine = TaskDispatchEngine()
        
        flow_groups = dispatch_engine.split_manifest_to_flow_groups(manifest)
        start_tasks = dispatch_engine.extract_start_tasks(flow_groups[0])
        
        self.assertEqual(len(start_tasks), 1)
        self.assertEqual(start_tasks[0].task_id, "START001")
        
        logger.info("  ✓ 提取成功")

    def test_07_dispatch_start_tasks_to_starter(self):
        """测试分派起始任务到启动员工"""
        logger.info("测试07: 分派起始任务到启动员工")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(self.sample_org_manifest, f, ensure_ascii=False)
            temp_file = f.name
        
        try:
            process_engine = SimulationProcessEngine(temp_file)
            
            def run_engine():
                process_engine.run()
            
            engine_thread = threading.Thread(target=run_engine, daemon=True)
            engine_thread.start()
            
            time.sleep(2)
            
            dispatch_engine = TaskDispatchEngine(process_engine=process_engine)
            
            manifest = self._create_test_manifest()
            flow_groups = dispatch_engine.split_manifest_to_flow_groups(manifest)
            start_tasks = dispatch_engine.extract_start_tasks(flow_groups[0])
            
            count = dispatch_engine.dispatch_start_tasks_to_starter(start_tasks, "TEST_MANIFEST_001")
            
            self.assertEqual(count, 1)
            
            starter_worker = process_engine.get_worker("__START_WORKER__")
            self.assertTrue(starter_worker.has_pending_tasks())
            
            process_engine.stop()
            time.sleep(1)
            
            logger.info("  ✓ 分派成功")
        finally:
            os.remove(temp_file)

    def test_08_dispatch_start_tasks_without_engine(self):
        """测试未设置引擎时分派任务（应报错）"""
        logger.info("测试08: 未设置引擎时分派任务（应报错）")
        
        dispatch_engine = TaskDispatchEngine()
        
        now = datetime.now()
        start_task = StartTask(
            task_id="START001",
            task_name="开始",
            expected_start_time=now,
            expected_end_time=now,
            content="开始",
            task_source=None,
            execute_role="__START__",
            resource_consumption=0.0,
            priority="low",
            output_target_role="DEV",
            task_destinations=["T001"]
        )
        
        with self.assertRaises(ValueError):
            dispatch_engine.dispatch_start_tasks_to_starter([start_task], "TEST_MANIFEST_001")
        
        logger.info("  ✓ 错误处理正常")

    def test_09_dispatch_manifest(self):
        """测试分派任务清单"""
        logger.info("测试09: 分派任务清单")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(self.sample_org_manifest, f, ensure_ascii=False)
            temp_file = f.name
        
        try:
            process_engine = SimulationProcessEngine(temp_file)
            
            def run_engine():
                process_engine.run()
            
            engine_thread = threading.Thread(target=run_engine, daemon=True)
            engine_thread.start()
            
            time.sleep(2)
            
            dispatch_engine = TaskDispatchEngine(process_engine=process_engine)
            
            manifest = self._create_test_manifest()
            
            result = dispatch_engine.dispatch_manifest(manifest)
            
            self.assertTrue(result["success"])
            self.assertEqual(result["manifest_id"], "TEST_MANIFEST_001")
            self.assertEqual(result["total_flow_groups"], 1)
            self.assertEqual(result["total_start_tasks"], 1)
            
            process_engine.stop()
            time.sleep(1)
            
            logger.info("  ✓ 分派成功")
        finally:
            os.remove(temp_file)

    def test_10_dispatch_invalid_manifest(self):
        """测试分派无效任务清单"""
        logger.info("测试10: 分派无效任务清单")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(self.sample_org_manifest, f, ensure_ascii=False)
            temp_file = f.name
        
        try:
            process_engine = SimulationProcessEngine(temp_file)
            
            def run_engine():
                process_engine.run()
            
            engine_thread = threading.Thread(target=run_engine, daemon=True)
            engine_thread.start()
            
            time.sleep(2)
            
            dispatch_engine = TaskDispatchEngine(process_engine=process_engine)
            
            invalid_manifest = TaskManifest(
                manifest_id="",
                manifest_name="",
                flow_groups=[],
                status="active"
            )
            
            result = dispatch_engine.dispatch_manifest(invalid_manifest)
            
            self.assertFalse(result["success"])
            self.assertIn("validation_errors", result)
            
            process_engine.stop()
            time.sleep(1)
            
            logger.info("  ✓ 无效清单处理正常")
        finally:
            os.remove(temp_file)

    def test_11_get_starter_worker_status(self):
        """测试获取启动员工状态"""
        logger.info("测试11: 获取启动员工状态")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(self.sample_org_manifest, f, ensure_ascii=False)
            temp_file = f.name
        
        try:
            process_engine = SimulationProcessEngine(temp_file)
            
            def run_engine():
                process_engine.run()
            
            engine_thread = threading.Thread(target=run_engine, daemon=True)
            engine_thread.start()
            
            time.sleep(2)
            
            dispatch_engine = TaskDispatchEngine(process_engine=process_engine)
            
            status = dispatch_engine.get_starter_worker_status()
            
            self.assertIsNotNone(status)
            self.assertEqual(status["employee_id"], "__START_WORKER__")
            
            process_engine.stop()
            time.sleep(1)
            
            logger.info("  ✓ 状态获取成功")
        finally:
            os.remove(temp_file)

    def test_12_get_starter_worker_status_without_engine(self):
        """测试未设置引擎时获取状态"""
        logger.info("测试12: 未设置引擎时获取状态")
        
        dispatch_engine = TaskDispatchEngine()
        
        status = dispatch_engine.get_starter_worker_status()
        
        self.assertIsNone(status)
        
        logger.info("  ✓ 返回None")

    def test_13_get_dispatched_manifests(self):
        """测试获取已分派的任务清单"""
        logger.info("测试13: 获取已分派的任务清单")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(self.sample_org_manifest, f, ensure_ascii=False)
            temp_file = f.name
        
        try:
            process_engine = SimulationProcessEngine(temp_file)
            
            def run_engine():
                process_engine.run()
            
            engine_thread = threading.Thread(target=run_engine, daemon=True)
            engine_thread.start()
            
            time.sleep(2)
            
            dispatch_engine = TaskDispatchEngine(process_engine=process_engine)
            
            manifest = self._create_test_manifest()
            dispatch_engine.dispatch_manifest(manifest)
            
            dispatched = dispatch_engine.get_dispatched_manifests()
            
            self.assertIn("TEST_MANIFEST_001", dispatched)
            
            process_engine.stop()
            time.sleep(1)
            
            logger.info("  ✓ 获取成功")
        finally:
            os.remove(temp_file)

    def test_14_clear_cache(self):
        """测试清除缓存"""
        logger.info("测试14: 清除缓存")
        
        dispatch_engine = TaskDispatchEngine()
        
        manifest = self._create_test_manifest()
        dispatch_engine._manifest_cache["TEST_CACHE_001"] = manifest
        
        self.assertIn("TEST_CACHE_001", dispatch_engine._manifest_cache)
        
        dispatch_engine.clear_cache()
        
        self.assertNotIn("TEST_CACHE_001", dispatch_engine._manifest_cache)
        
        logger.info("  ✓ 缓存清除成功")

    def test_15_get_and_set_manifest_dir(self):
        """测试获取和设置清单目录"""
        logger.info("测试15: 获取和设置清单目录")
        
        dispatch_engine = TaskDispatchEngine()
        original_dir = dispatch_engine.get_manifest_dir()
        
        self.assertIsInstance(original_dir, str)
        
        new_dir = "test_manifests_dir"
        dispatch_engine.set_manifest_dir(new_dir)
        
        self.assertEqual(dispatch_engine.get_manifest_dir(), new_dir)
        self.assertTrue(os.path.exists(new_dir))
        
        import shutil
        shutil.rmtree(new_dir, ignore_errors=True)
        
        logger.info("  ✓ 目录设置正常")


if __name__ == '__main__':
    os.makedirs('logs', exist_ok=True)
    unittest.main(verbosity=2)