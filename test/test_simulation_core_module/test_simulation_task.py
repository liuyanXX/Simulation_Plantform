import os
import sys
import logging
import unittest
import json
import tempfile
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from simulation_core_module.simulation_task import (
    SimulationEngine,
    SimulationTaskModule,
    SimulationConfig,
    OrganizationConfig,
    WorkerConfig,
    ConfigFormat,
    create_sample_config
)
from bo.ai_worker import AIWorker
from bo.task import Task, StartTask, EndTask

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_simulation_task.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TestSimulationConfig(unittest.TestCase):
    """测试SimulationConfig模型"""

    def test_01_create_config_from_dict(self):
        """测试从字典创建配置"""
        logger.info("测试01: 创建SimulationConfig")
        
        config_dict = {
            "simulation_name": "测试仿真",
            "start_time": datetime.now().isoformat(),
            "organizations": []
        }
        
        config = SimulationConfig(**config_dict)
        
        self.assertEqual(config.simulation_name, "测试仿真")
        self.assertIsInstance(config.start_time, datetime)
        
        logger.info("  ✓ 创建成功")

    def test_02_config_with_organizations(self):
        """测试包含组织的配置"""
        logger.info("测试02: 包含组织的配置")
        
        config_dict = {
            "simulation_name": "测试仿真",
            "organizations": [
                {
                    "org_id": "ORG001",
                    "name": "研发部",
                    "parent_org_id": None,
                    "workers": []
                }
            ]
        }
        
        config = SimulationConfig(**config_dict)
        
        self.assertEqual(len(config.organizations), 1)
        self.assertEqual(config.organizations[0].org_id, "ORG001")
        
        logger.info("  ✓ 组织配置正常")


class TestSimulationEngine(unittest.TestCase):
    """测试SimulationEngine类"""

    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        logger.info("=" * 60)
        logger.info("开始测试SimulationEngine")
        logger.info("=" * 60)
        cls.engine = SimulationEngine()

    def test_01_load_config_from_dict(self):
        """测试从字典加载配置"""
        logger.info("测试01: 从字典加载配置")
        
        config = self.engine.load_config_from_dict(create_sample_config())
        
        self.assertIsInstance(config, SimulationConfig)
        self.assertEqual(config.simulation_name, "项目仿真任务")
        
        logger.info("  ✓ 加载成功")

    def test_02_load_config_from_file(self):
        """测试从文件加载配置"""
        logger.info("测试02: 从文件加载配置")
        
        config_dict = create_sample_config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(config_dict, f, ensure_ascii=False)
            temp_file = f.name
        
        try:
            config = self.engine.load_config_from_file(temp_file)
            
            self.assertIsInstance(config, SimulationConfig)
            self.assertEqual(config.simulation_name, "项目仿真任务")
            
            logger.info("  ✓ 文件加载成功")
        finally:
            os.remove(temp_file)

    def test_03_initialize_with_config(self):
        """测试初始化仿真环境"""
        logger.info("测试03: 初始化仿真环境")
        
        config = self.engine.load_config_from_dict(create_sample_config())
        self.engine.initialize(config)
        
        organizations = self.engine.get_all_organizations()
        workers = self.engine.get_all_workers()
        
        self.assertTrue(len(organizations) > 0)
        self.assertTrue(len(workers) > 0)
        
        logger.info(f"  ✓ 初始化完成: {len(organizations)}个组织, {len(workers)}名员工")

    def test_04_start_and_stop(self):
        """测试启动和停止仿真引擎"""
        logger.info("测试04: 启动和停止仿真引擎")
        
        config = self.engine.load_config_from_dict(create_sample_config())
        self.engine.initialize(config)
        
        self.engine.start()
        
        self.assertTrue(self.engine.is_running())
        
        self.engine.stop()
        
        self.assertFalse(self.engine.is_running())
        
        logger.info("  ✓ 启动停止正常")

    def test_05_get_organization(self):
        """测试获取组织"""
        logger.info("测试05: 获取组织")
        
        config = self.engine.load_config_from_dict(create_sample_config())
        self.engine.initialize(config)
        
        org = self.engine.get_organization("ORG001")
        
        self.assertIsNotNone(org)
        self.assertEqual(org.org_id, "ORG001")
        
        logger.info(f"  ✓ 获取成功: {org.name}")

    def test_06_get_nonexistent_organization(self):
        """测试获取不存在的组织"""
        logger.info("测试06: 获取不存在的组织")
        
        config = self.engine.load_config_from_dict(create_sample_config())
        self.engine.initialize(config)
        
        org = self.engine.get_organization("NONEXISTENT")
        
        self.assertIsNone(org)
        logger.info("  ✓ 返回None")

    def test_07_get_worker(self):
        """测试获取员工"""
        logger.info("测试07: 获取员工")
        
        config = self.engine.load_config_from_dict(create_sample_config())
        self.engine.initialize(config)
        
        worker = self.engine.get_worker("EMP001")
        
        self.assertIsNotNone(worker)
        self.assertEqual(worker.employee_id, "EMP001")
        
        logger.info(f"  ✓ 获取成功: {worker.name}")

    def test_08_get_nonexistent_worker(self):
        """测试获取不存在的员工"""
        logger.info("测试08: 获取不存在的员工")
        
        config = self.engine.load_config_from_dict(create_sample_config())
        self.engine.initialize(config)
        
        worker = self.engine.get_worker("NONEXISTENT")
        
        self.assertIsNone(worker)
        logger.info("  ✓ 返回None")

    def test_09_assign_task_to_worker(self):
        """测试给员工分配任务"""
        logger.info("测试09: 给员工分配任务")
        
        config = self.engine.load_config_from_dict(create_sample_config())
        self.engine.initialize(config)
        
        task = Task(
            task_id="TASK001",
            task_name="测试任务",
            expected_start_time=datetime.now(),
            expected_end_time=datetime.now(),
            content="测试内容",
            execute_role="DEV",
            resource_consumption=1.0,
            priority="high",
            output_target_role="TEST"
        )
        
        result = self.engine.assign_task_to_worker("EMP001", task)
        
        self.assertTrue(result)
        
        worker = self.engine.get_worker("EMP001")
        self.assertTrue(worker.has_pending_tasks())
        
        logger.info("  ✓ 任务分配成功")

    def test_10_assign_task_to_nonexistent_worker(self):
        """测试给不存在的员工分配任务"""
        logger.info("测试10: 给不存在的员工分配任务")
        
        config = self.engine.load_config_from_dict(create_sample_config())
        self.engine.initialize(config)
        
        task = Task(
            task_id="TASK002",
            task_name="测试任务2",
            expected_start_time=datetime.now(),
            expected_end_time=datetime.now(),
            content="测试内容",
            execute_role="DEV",
            resource_consumption=1.0,
            priority="high",
            output_target_role="TEST"
        )
        
        result = self.engine.assign_task_to_worker("NONEXISTENT", task)
        
        self.assertFalse(result)
        logger.info("  ✓ 返回False")

    def test_11_assign_task_by_role(self):
        """测试按角色分配任务"""
        logger.info("测试11: 按角色分配任务")
        
        config = self.engine.load_config_from_dict(create_sample_config())
        self.engine.initialize(config)
        
        task = Task(
            task_id="TASK003",
            task_name="角色分配任务",
            expected_start_time=datetime.now(),
            expected_end_time=datetime.now(),
            content="测试内容",
            execute_role="DEV",
            resource_consumption=1.0,
            priority="high",
            output_target_role="TEST"
        )
        
        result = self.engine.assign_task_by_role("DEV", task)
        
        self.assertTrue(result)
        
        worker = self.engine.get_worker("EMP001")
        self.assertTrue(worker.has_pending_tasks())
        
        logger.info("  ✓ 角色分配成功")

    def test_12_assign_task_to_nonexistent_role(self):
        """测试给不存在的角色分配任务"""
        logger.info("测试12: 给不存在的角色分配任务")
        
        config = self.engine.load_config_from_dict(create_sample_config())
        self.engine.initialize(config)
        
        task = Task(
            task_id="TASK004",
            task_name="角色分配任务2",
            expected_start_time=datetime.now(),
            expected_end_time=datetime.now(),
            content="测试内容",
            execute_role="NONEXISTENT",
            resource_consumption=1.0,
            priority="high",
            output_target_role="TEST"
        )
        
        result = self.engine.assign_task_by_role("NONEXISTENT", task)
        
        self.assertFalse(result)
        logger.info("  ✓ 返回False")

    def test_13_get_role_registry(self):
        """测试获取角色注册表"""
        logger.info("测试13: 获取角色注册表")
        
        config = self.engine.load_config_from_dict(create_sample_config())
        self.engine.initialize(config)
        
        registry = self.engine.get_role_registry()
        
        self.assertIsInstance(registry, dict)
        self.assertIn("DEV", registry)
        self.assertIn("TEST", registry)
        
        logger.info(f"  ✓ 角色注册表: {list(registry.keys())}")

    def test_14_get_simulation_status(self):
        """测试获取仿真状态"""
        logger.info("测试14: 获取仿真状态")
        
        config = self.engine.load_config_from_dict(create_sample_config())
        self.engine.initialize(config)
        self.engine.start()
        
        status = self.engine.get_simulation_status()
        
        self.assertIn("is_running", status)
        self.assertIn("organization_count", status)
        self.assertIn("worker_count", status)
        self.assertIn("workers", status)
        
        self.assertTrue(status["is_running"])
        
        self.engine.stop()
        
        logger.info("  ✓ 状态获取正常")


class TestSimulationTaskModule(unittest.TestCase):
    """测试SimulationTaskModule类"""

    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        logger.info("=" * 60)
        logger.info("开始测试SimulationTaskModule")
        logger.info("=" * 60)

    def test_01_load_config(self):
        """测试加载配置"""
        logger.info("测试01: 加载配置")
        
        config_dict = create_sample_config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(config_dict, f, ensure_ascii=False)
            temp_file = f.name
        
        try:
            module = SimulationTaskModule()
            module.load_config(temp_file)
            
            self.assertIsNotNone(module._config)
            self.assertEqual(module._config.simulation_name, "项目仿真任务")
            
            logger.info("  ✓ 配置加载成功")
        finally:
            os.remove(temp_file)

    def test_02_initialize(self):
        """测试初始化"""
        logger.info("测试02: 初始化")
        
        module = SimulationTaskModule()
        config = module._engine.load_config_from_dict(create_sample_config())
        module.initialize(config)
        
        engine = module.get_engine()
        organizations = engine.get_all_organizations()
        workers = engine.get_all_workers()
        
        self.assertTrue(len(organizations) > 0)
        self.assertTrue(len(workers) > 0)
        
        logger.info("  ✓ 初始化成功")

    def test_03_start_and_shutdown(self):
        """测试启动和关闭"""
        logger.info("测试03: 启动和关闭")
        
        module = SimulationTaskModule()
        config = module._engine.load_config_from_dict(create_sample_config())
        module.initialize(config)
        
        module.start()
        
        engine = module.get_engine()
        self.assertTrue(engine.is_running())
        
        module.shutdown()
        
        self.assertFalse(engine.is_running())
        
        logger.info("  ✓ 启动关闭正常")

    def test_04_get_engine(self):
        """测试获取引擎"""
        logger.info("测试04: 获取引擎")
        
        module = SimulationTaskModule()
        
        engine = module.get_engine()
        
        self.assertIsInstance(engine, SimulationEngine)
        
        logger.info("  ✓ 获取成功")


if __name__ == '__main__':
    os.makedirs('logs', exist_ok=True)
    unittest.main(verbosity=2)