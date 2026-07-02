import os
import sys
import logging
import unittest
import json
import tempfile
from datetime import datetime, timedelta
import threading
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from simulation_core_module.simulation_process_module import SimulationProcessModule
from simulation_core_module.simulation_process_engine import SimulationProcessEngine
from simulation_core_module.task_dispatch_engine import TaskDispatchEngine
from simulation_core_module.worker_type_registry import WorkerTypeRegistry
from simulation_core_module.simulation_task import SimulationEngine, SimulationTaskModule, create_sample_config
from bo.task_manifest import TaskManifest
from bo.task_flow_group import TaskFlowGroup
from bo.task import StartTask, EndTask, Task
from bo.ssys.aiworker import AIWorker
from bo.organization import Organization

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_integration.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TestIntegration(unittest.TestCase):
    """测试仿真核心模块各组件间的集成"""

    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        logger.info("=" * 60)
        logger.info("开始测试仿真核心模块集成")
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
                },
                {
                    "org_id": "PM",
                    "name": "项目管理部",
                    "workers": [
                        {
                            "employee_id": "EMP003",
                            "name": "王五",
                            "department": "项目管理部",
                            "roles": ["PM"],
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
            task_name="项目启动",
            expected_start_time=now,
            expected_end_time=now + timedelta(hours=1),
            content="项目开始",
            task_source=None,
            execute_role="__START__",
            resource_consumption=0.0,
            priority="low",
            output_target_role="PM",
            task_destinations=["T001"]
        )
        
        plan_task = Task(
            task_id="T001",
            task_name="需求分析",
            expected_start_time=now + timedelta(hours=1),
            expected_end_time=now + timedelta(hours=4),
            content="需求分析文档",
            task_source="START001",
            execute_role="PM",
            resource_consumption=2.0,
            priority="high",
            output_target_role="DEV",
            task_destinations=["T002"]
        )
        
        dev_task = Task(
            task_id="T002",
            task_name="开发实现",
            expected_start_time=now + timedelta(hours=4),
            expected_end_time=now + timedelta(hours=12),
            content="功能开发",
            task_source="T001",
            execute_role="DEV",
            resource_consumption=4.0,
            priority="high",
            output_target_role="TEST",
            task_destinations=["T003"]
        )
        
        test_task = Task(
            task_id="T003",
            task_name="测试验证",
            expected_start_time=now + timedelta(hours=12),
            expected_end_time=now + timedelta(hours=16),
            content="功能测试",
            task_source="T002",
            execute_role="TEST",
            resource_consumption=2.0,
            priority="high",
            output_target_role="",
            task_destinations=["END001"]
        )
        
        end_task = EndTask(
            task_id="END001",
            task_name="项目结束",
            expected_start_time=now + timedelta(hours=16),
            expected_end_time=now + timedelta(hours=17),
            content="项目完成",
            task_source="T003",
            execute_role="__END__",
            resource_consumption=0.0,
            priority="low",
            output_target_role="",
            task_destinations=[]
        )
        
        flow_group = TaskFlowGroup(
            flow_id="FLOW001",
            flow_name="项目流程",
            tasks=[start_task, plan_task, dev_task, test_task, end_task]
        )
        
        return TaskManifest(
            manifest_id="INTEGRATION_TEST_001",
            manifest_name="集成测试清单",
            flow_groups=[flow_group],
            status="active"
        )

    def test_01_full_simulation_process(self):
        """测试完整仿真流程：初始化组织 -> 启动引擎 -> 分派任务 -> 运行"""
        logger.info("测试01: 完整仿真流程")
        
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
            
            result = module.init_process_engine(org_file)
            self.assertTrue(result["success"])
            
            task_manifest = self._create_test_task_manifest()
            
            result = module.dispatch_manifest(task_manifest)
            self.assertTrue(result["success"])
            
            status = module.get_status()
            self.assertTrue(status["is_running"])
            self.assertTrue(status["process_engine_initialized"])
            self.assertEqual(len(status["dispatched_manifests"]), 1)
            
            time.sleep(3)
            
            process_engine = module.get_process_engine()
            workers = process_engine.get_all_workers()
            self.assertTrue(len(workers) > 0)
            
            dispatch_engine = module.get_dispatch_engine()
            dispatched = dispatch_engine.get_dispatched_manifests()
            self.assertIn("INTEGRATION_TEST_001", dispatched)
            
            module.stop()
            time.sleep(1)
            
            status = module.get_status()
            self.assertFalse(status["is_running"])
            
            logger.info("  ✓ 完整流程测试通过")
        finally:
            os.remove(org_file)

    def test_02_worker_type_registry_with_engine(self):
        """测试员工类型注册表与仿真引擎的集成"""
        logger.info("测试02: 员工类型注册表与仿真引擎集成")
        
        org_manifest = self._create_test_org_manifest()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(org_manifest, f, ensure_ascii=False)
            org_file = f.name
        
        try:
            class CustomWorker(AIWorker):
                pass
            
            WorkerTypeRegistry.register("CustomWorker", CustomWorker)
            
            process_engine = SimulationProcessEngine(org_file)
            
            def run_engine():
                process_engine.run()
            
            engine_thread = threading.Thread(target=run_engine, daemon=True)
            engine_thread.start()
            
            time.sleep(2)
            
            workers = process_engine.get_all_workers()
            
            self.assertIsNotNone(process_engine.get_worker("__START_WORKER__"))
            
            WorkerTypeRegistry.unregister("CustomWorker")
            
            process_engine.stop()
            time.sleep(1)
            
            logger.info("  ✓ 员工类型注册表集成测试通过")
        finally:
            os.remove(org_file)

    def test_03_simulation_task_module_with_process_engine(self):
        """测试仿真任务模块与流程引擎的集成"""
        logger.info("测试03: 仿真任务模块与流程引擎集成")
        
        config_dict = create_sample_config()
        
        task_module = SimulationTaskModule()
        config = task_module._engine.load_config_from_dict(config_dict)
        task_module.initialize(config)
        
        engine = task_module.get_engine()
        
        organizations = engine.get_all_organizations()
        workers = engine.get_all_workers()
        
        self.assertTrue(len(organizations) > 0)
        self.assertTrue(len(workers) > 0)
        
        task_module.start()
        
        self.assertTrue(engine.is_running())
        
        status = engine.get_simulation_status()
        self.assertTrue(status["is_running"])
        
        task_module.shutdown()
        
        self.assertFalse(engine.is_running())
        
        logger.info("  ✓ 仿真任务模块集成测试通过")

    def test_04_task_dispatch_engine_with_process_engine(self):
        """测试任务分派引擎与流程引擎的集成"""
        logger.info("测试04: 任务分派引擎与流程引擎集成")
        
        org_manifest = self._create_test_org_manifest()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(org_manifest, f, ensure_ascii=False)
            org_file = f.name
        
        try:
            process_engine = SimulationProcessEngine(org_file)
            
            def run_engine():
                process_engine.run()
            
            engine_thread = threading.Thread(target=run_engine, daemon=True)
            engine_thread.start()
            
            time.sleep(2)
            
            dispatch_engine = TaskDispatchEngine(process_engine=process_engine)
            
            task_manifest = self._create_test_task_manifest()
            
            result = dispatch_engine.dispatch_manifest(task_manifest)
            
            self.assertTrue(result["success"])
            self.assertEqual(result["manifest_id"], "INTEGRATION_TEST_001")
            
            starter_status = dispatch_engine.get_starter_worker_status()
            self.assertIsNotNone(starter_status)
            self.assertEqual(starter_status["employee_id"], "__START_WORKER__")
            
            dispatched = dispatch_engine.get_dispatched_manifests()
            self.assertIn("INTEGRATION_TEST_001", dispatched)
            
            dispatch_engine.clear_cache()
            
            process_engine.stop()
            time.sleep(1)
            
            logger.info("  ✓ 任务分派引擎集成测试通过")
        finally:
            os.remove(org_file)

    def test_05_multi_manifest_dispatch(self):
        """测试多任务清单分派"""
        logger.info("测试05: 多任务清单分派")
        
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
            
            manifest1 = self._create_test_task_manifest()
            
            now = datetime.now()
            start_task2 = StartTask(
                task_id="START002",
                task_name="项目启动2",
                expected_start_time=now,
                expected_end_time=now + timedelta(hours=1),
                content="项目开始2",
                task_source=None,
                execute_role="__START__",
                resource_consumption=0.0,
                priority="low",
                output_target_role="DEV",
                task_destinations=["T004"]
            )
            dev_task2 = Task(
                task_id="T004",
                task_name="开发任务2",
                expected_start_time=now + timedelta(hours=1),
                expected_end_time=now + timedelta(hours=5),
                content="开发内容2",
                task_source="START002",
                execute_role="DEV",
                resource_consumption=3.0,
                priority="medium",
                output_target_role="TEST",
                task_destinations=["END002"]
            )
            end_task2 = EndTask(
                task_id="END002",
                task_name="项目结束2",
                expected_start_time=now + timedelta(hours=5),
                expected_end_time=now + timedelta(hours=6),
                content="项目完成2",
                task_source="T004",
                execute_role="__END__",
                resource_consumption=0.0,
                priority="low",
                output_target_role="",
                task_destinations=[]
            )
            flow_group2 = TaskFlowGroup(
                flow_id="FLOW002",
                flow_name="项目流程2",
                tasks=[start_task2, dev_task2, end_task2]
            )
            manifest2 = TaskManifest(
                manifest_id="INTEGRATION_TEST_002",
                manifest_name="集成测试清单2",
                flow_groups=[flow_group2],
                status="active"
            )
            
            result1 = module.dispatch_manifest(manifest1)
            self.assertTrue(result1["success"])
            
            result2 = module.dispatch_manifest(manifest2)
            self.assertTrue(result2["success"])
            
            status = module.get_status()
            self.assertEqual(len(status["dispatched_manifests"]), 2)
            
            dispatch_engine = module.get_dispatch_engine()
            dispatched = dispatch_engine.get_dispatched_manifests()
            self.assertIn("INTEGRATION_TEST_001", dispatched)
            self.assertIn("INTEGRATION_TEST_002", dispatched)
            
            module.clear_dispatched_manifests()
            
            status = module.get_status()
            self.assertEqual(len(status["dispatched_manifests"]), 0)
            
            module.stop()
            time.sleep(1)
            
            logger.info("  ✓ 多任务清单分派测试通过")
        finally:
            os.remove(org_file)

    def test_06_organization_hierarchy_with_workers(self):
        """测试组织层级与员工的集成"""
        logger.info("测试06: 组织层级与员工集成")
        
        org_manifest = {
            "org_id": "ROOT",
            "name": "集团公司",
            "workers": [
                {
                    "employee_id": "EMP_ROOT",
                    "name": "董事长",
                    "department": "集团公司",
                    "roles": ["CEO"],
                    "daily_work_hours": 8.0
                }
            ],
            "children": [
                {
                    "org_id": "SUBSIDIARY",
                    "name": "子公司",
                    "workers": [
                        {
                            "employee_id": "EMP_SUB",
                            "name": "子公司总经理",
                            "department": "子公司",
                            "roles": ["GM"],
                            "daily_work_hours": 8.0
                        }
                    ],
                    "children": [
                        {
                            "org_id": "DEPT",
                            "name": "部门",
                            "workers": [
                                {
                                    "employee_id": "EMP_DEPT",
                                    "name": "部门经理",
                                    "department": "部门",
                                    "roles": ["MGR"],
                                    "daily_work_hours": 8.0
                                }
                            ],
                            "children": []
                        }
                    ]
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(org_manifest, f, ensure_ascii=False)
            org_file = f.name
        
        try:
            process_engine = SimulationProcessEngine(org_file)
            
            def run_engine():
                process_engine.run()
            
            engine_thread = threading.Thread(target=run_engine, daemon=True)
            engine_thread.start()
            
            time.sleep(2)
            
            organizations = process_engine.get_all_organizations()
            self.assertEqual(len(organizations), 3)
            
            root_org = process_engine.get_organization("ROOT")
            self.assertIsNotNone(root_org)
            self.assertEqual(root_org.name, "集团公司")
            
            workers = process_engine.get_all_workers()
            self.assertEqual(len(workers), 4)
            
            ceo = process_engine.get_worker("EMP_ROOT")
            self.assertIsNotNone(ceo)
            self.assertEqual(ceo.name, "董事长")
            self.assertIn("CEO", ceo.roles)
            
            role_registry = process_engine.get_role_registry()
            self.assertIn("CEO", role_registry)
            self.assertIn("GM", role_registry)
            self.assertIn("MGR", role_registry)
            
            process_engine.stop()
            time.sleep(1)
            
            logger.info("  ✓ 组织层级与员工集成测试通过")
        finally:
            os.remove(org_file)

    def test_07_task_flow_with_different_roles(self):
        """测试跨角色任务流转"""
        logger.info("测试07: 跨角色任务流转")
        
        org_manifest = {
            "org_id": "ROOT",
            "name": "公司",
            "workers": [],
            "children": [
                {
                    "org_id": "RD",
                    "name": "研发部",
                    "workers": [
                        {
                            "employee_id": "EMP_DEV",
                            "name": "开发者",
                            "department": "研发部",
                            "roles": ["DEV"],
                            "daily_work_hours": 8.0
                        }
                    ],
                    "children": []
                },
                {
                    "org_id": "QA",
                    "name": "测试部",
                    "workers": [
                        {
                            "employee_id": "EMP_TEST",
                            "name": "测试员",
                            "department": "测试部",
                            "roles": ["TEST"],
                            "daily_work_hours": 8.0
                        }
                    ],
                    "children": []
                },
                {
                    "org_id": "PM",
                    "name": "产品部",
                    "workers": [
                        {
                            "employee_id": "EMP_PM",
                            "name": "产品经理",
                            "department": "产品部",
                            "roles": ["PM"],
                            "daily_work_hours": 8.0
                        }
                    ],
                    "children": []
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(org_manifest, f, ensure_ascii=False)
            org_file = f.name
        
        try:
            process_engine = SimulationProcessEngine(org_file)
            
            def run_engine():
                process_engine.run()
            
            engine_thread = threading.Thread(target=run_engine, daemon=True)
            engine_thread.start()
            
            time.sleep(2)
            
            dispatch_engine = TaskDispatchEngine(process_engine=process_engine)
            
            now = datetime.now()
            
            tasks = [
                StartTask(
                    task_id="START",
                    task_name="开始",
                    expected_start_time=now,
                    expected_end_time=now,
                    content="开始",
                    task_source=None,
                    execute_role="__START__",
                    resource_consumption=0.0,
                    priority="low",
                    output_target_role="PM",
                    task_destinations=["T1"]
                ),
                Task(
                    task_id="T1",
                    task_name="需求分析",
                    expected_start_time=now,
                    expected_end_time=now,
                    content="分析需求",
                    task_source="START",
                    execute_role="PM",
                    resource_consumption=1.0,
                    priority="high",
                    output_target_role="DEV",
                    task_destinations=["T2"]
                ),
                Task(
                    task_id="T2",
                    task_name="开发",
                    expected_start_time=now,
                    expected_end_time=now,
                    content="开发功能",
                    task_source="T1",
                    execute_role="DEV",
                    resource_consumption=2.0,
                    priority="high",
                    output_target_role="TEST",
                    task_destinations=["T3"]
                ),
                Task(
                    task_id="T3",
                    task_name="测试",
                    expected_start_time=now,
                    expected_end_time=now,
                    content="测试功能",
                    task_source="T2",
                    execute_role="TEST",
                    resource_consumption=1.0,
                    priority="high",
                    output_target_role="",
                    task_destinations=["END"]
                ),
                EndTask(
                    task_id="END",
                    task_name="结束",
                    expected_start_time=now,
                    expected_end_time=now,
                    content="结束",
                    task_source="T3",
                    execute_role="__END__",
                    resource_consumption=0.0,
                    priority="low",
                    output_target_role="",
                    task_destinations=[]
                )
            ]
            
            flow_group = TaskFlowGroup(flow_id="FLOW", flow_name="跨角色流程", tasks=tasks)
            manifest = TaskManifest(
                manifest_id="CROSS_ROLE_TEST",
                manifest_name="跨角色测试",
                flow_groups=[flow_group],
                status="active"
            )
            
            result = dispatch_engine.dispatch_manifest(manifest)
            
            self.assertTrue(result["success"])
            
            role_registry = process_engine.get_role_registry()
            self.assertIn("PM", role_registry)
            self.assertIn("DEV", role_registry)
            self.assertIn("TEST", role_registry)
            
            pm_worker = role_registry["PM"]
            dev_worker = role_registry["DEV"]
            test_worker = role_registry["TEST"]
            
            self.assertEqual(pm_worker.employee_id, "EMP_PM")
            self.assertEqual(dev_worker.employee_id, "EMP_DEV")
            self.assertEqual(test_worker.employee_id, "EMP_TEST")
            
            process_engine.stop()
            time.sleep(1)
            
            logger.info("  ✓ 跨角色任务流转测试通过")
        finally:
            os.remove(org_file)

    def test_08_engine_status_and_worker_states(self):
        """测试引擎状态与员工状态的联动"""
        logger.info("测试08: 引擎状态与员工状态联动")
        
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
            
            status = module.get_status()
            self.assertTrue(status["is_running"])
            
            process_engine = module.get_process_engine()
            
            engine_status = process_engine.get_simulation_status()
            self.assertTrue(engine_status["is_running"])
            self.assertEqual(engine_status["organization_count"], 3)
            self.assertEqual(engine_status["worker_count"], 4)
            
            for worker_info in engine_status["workers"]:
                self.assertIn("employee_id", worker_info)
                self.assertIn("name", worker_info)
                self.assertIn("department", worker_info)
                self.assertIn("roles", worker_info)
                self.assertIn("has_pending_tasks", worker_info)
            
            task_manifest = self._create_test_task_manifest()
            module.dispatch_manifest(task_manifest)
            
            time.sleep(1)
            
            engine_status = process_engine.get_simulation_status()
            starter_worker = None
            for worker_info in engine_status["workers"]:
                if worker_info["employee_id"] == "__START_WORKER__":
                    starter_worker = worker_info
                    break
            
            self.assertIsNotNone(starter_worker)
            
            module.stop()
            time.sleep(1)
            
            status = module.get_status()
            self.assertFalse(status["is_running"])
            
            logger.info("  ✓ 引擎状态与员工状态联动测试通过")
        finally:
            os.remove(org_file)

    def test_09_error_handling_in_integration(self):
        """测试集成环境下的错误处理"""
        logger.info("测试09: 集成环境下的错误处理")
        
        org_manifest = self._create_test_org_manifest()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(org_manifest, f, ensure_ascii=False)
            org_file = f.name
        
        try:
            module = SimulationProcessModule()
            module.start()
            
            result = module.init_process_engine("invalid_path.json")
            self.assertFalse(result["success"])
            
            result = module.init_process_engine(org_file)
            self.assertTrue(result["success"])
            
            invalid_manifest = TaskManifest(
                manifest_id="",
                manifest_name="",
                flow_groups=[],
                status="active"
            )
            
            result = module.dispatch_manifest(invalid_manifest)
            self.assertFalse(result["success"])
            
            module.reset()
            
            status = module.get_status()
            self.assertFalse(status["process_engine_initialized"])
            
            module.stop()
            
            logger.info("  ✓ 集成错误处理测试通过")
        finally:
            os.remove(org_file)


if __name__ == '__main__':
    os.makedirs('logs', exist_ok=True)
    unittest.main(verbosity=2)