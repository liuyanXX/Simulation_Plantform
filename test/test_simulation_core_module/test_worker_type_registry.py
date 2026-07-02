import os
import sys
import logging
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from simulation_core_module.worker_type_registry import WorkerTypeRegistry
from bo.ssys.aiworker import AIWorker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_worker_type_registry.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TestWorkerTypeRegistry(unittest.TestCase):
    """测试WorkerTypeRegistry类"""

    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        logger.info("=" * 60)
        logger.info("开始测试WorkerTypeRegistry")
        logger.info("=" * 60)

    def test_01_default_registration(self):
        """测试默认注册的AIWorker类型"""
        logger.info("测试01: 默认注册的AIWorker类型")
        
        self.assertTrue(WorkerTypeRegistry.is_registered("AIWorker"))
        worker_class = WorkerTypeRegistry.get("AIWorker")
        self.assertEqual(worker_class, AIWorker)
        
        logger.info("  ✓ AIWorker已默认注册")

    def test_02_register_new_type(self):
        """测试注册新类型"""
        logger.info("测试02: 注册新类型")
        
        class TestWorker(AIWorker):
            pass
        
        WorkerTypeRegistry.register("TestWorker", TestWorker)
        
        self.assertTrue(WorkerTypeRegistry.is_registered("TestWorker"))
        self.assertEqual(WorkerTypeRegistry.get("TestWorker"), TestWorker)
        
        logger.info("  ✓ 新类型注册成功")

    def test_03_register_duplicate_type(self):
        """测试注册重复类型（应报错）"""
        logger.info("测试03: 注册重复类型（应报错）")
        
        with self.assertRaises(ValueError):
            WorkerTypeRegistry.register("AIWorker", AIWorker)
        
        logger.info("  ✓ 重复注册检测正常")

    def test_04_register_non_aiworker_subclass(self):
        """测试注册非AIWorker子类（应报错）"""
        logger.info("测试04: 注册非AIWorker子类（应报错）")
        
        class NonWorker:
            pass
        
        with self.assertRaises(ValueError):
            WorkerTypeRegistry.register("NonWorker", NonWorker)
        
        logger.info("  ✓ 类型检查正常")

    def test_05_get_registered_type(self):
        """测试获取已注册类型"""
        logger.info("测试05: 获取已注册类型")
        
        worker_class = WorkerTypeRegistry.get("AIWorker")
        self.assertIsNotNone(worker_class)
        self.assertEqual(worker_class, AIWorker)
        
        logger.info("  ✓ 获取成功")

    def test_06_get_unregistered_type(self):
        """测试获取未注册类型（应报错）"""
        logger.info("测试06: 获取未注册类型（应报错）")
        
        with self.assertRaises(ValueError):
            WorkerTypeRegistry.get("NonExistentType")
        
        logger.info("  ✓ 错误处理正常")

    def test_07_is_registered(self):
        """测试类型注册检查"""
        logger.info("测试07: 类型注册检查")
        
        self.assertTrue(WorkerTypeRegistry.is_registered("AIWorker"))
        self.assertFalse(WorkerTypeRegistry.is_registered("NonExistentType"))
        
        logger.info("  ✓ 注册检查正常")

    def test_08_unregister_type(self):
        """测试注销类型"""
        logger.info("测试08: 注销类型")
        
        class TempWorker(AIWorker):
            pass
        
        WorkerTypeRegistry.register("TempWorker", TempWorker)
        self.assertTrue(WorkerTypeRegistry.is_registered("TempWorker"))
        
        WorkerTypeRegistry.unregister("TempWorker")
        self.assertFalse(WorkerTypeRegistry.is_registered("TempWorker"))
        
        logger.info("  ✓ 注销成功")

    def test_09_unregister_nonexistent_type(self):
        """测试注销不存在的类型（应报错）"""
        logger.info("测试09: 注销不存在的类型（应报错）")
        
        with self.assertRaises(ValueError):
            WorkerTypeRegistry.unregister("NonExistentType")
        
        logger.info("  ✓ 错误处理正常")

    def test_10_get_all_types(self):
        """测试获取所有已注册类型"""
        logger.info("测试10: 获取所有已注册类型")
        
        types = WorkerTypeRegistry.get_all_types()
        
        self.assertIsInstance(types, dict)
        self.assertIn("AIWorker", types)
        
        logger.info(f"  ✓ 已注册类型: {list(types.keys())}")

    def test_11_create_worker(self):
        """测试创建员工实例"""
        logger.info("测试11: 创建员工实例")
        
        worker = WorkerTypeRegistry.create_worker(
            "AIWorker",
            employee_id="TEST_WORKER_001",
            name="测试员工",
            department="测试部",
            roles=["TEST"]
        )
        
        self.assertIsInstance(worker, AIWorker)
        self.assertEqual(worker.employee_id, "TEST_WORKER_001")
        self.assertEqual(worker.name, "测试员工")
        self.assertEqual(worker.department, "测试部")
        self.assertIn("TEST", worker.roles)
        
        logger.info(f"  ✓ 创建成功: {worker.name}")

    def test_12_create_worker_with_invalid_type(self):
        """测试使用无效类型创建员工（应报错）"""
        logger.info("测试12: 使用无效类型创建员工（应报错）")
        
        with self.assertRaises(ValueError):
            WorkerTypeRegistry.create_worker("NonExistentType", employee_id="TEST_001")
        
        logger.info("  ✓ 错误处理正常")


if __name__ == '__main__':
    os.makedirs('logs', exist_ok=True)
    unittest.main(verbosity=2)