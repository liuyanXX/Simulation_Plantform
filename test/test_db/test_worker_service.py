"""员工服务测试

测试WorkerService的所有方法。
"""

import unittest
import os
import sys
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from data_storage_services.sql_db_services.worker_service import WorkerService
from bo.ai_worker import AIWorker


class TestWorkerService(unittest.TestCase):
    """员工服务测试类"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'test_worker_service.log')
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
        cls.logger.info("开始WorkerService测试")
        cls.logger.info("=" * 60)

        test_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_data')
        os.makedirs(test_db_path, exist_ok=True)

        from . import ensure_tables_exist
        ensure_tables_exist(test_db_path, "test_worker.db")

        cls.service = WorkerService(
            db_type="sqlite",
            db_config={"db_path": test_db_path, "db_name": "test_worker.db"}
        )

    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        cls.service.disconnect()
        test_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_data')
        db_file = os.path.join(test_db_path, "test_worker.db")
        if os.path.exists(db_file):
            os.remove(db_file)
        cls.logger.info("WorkerService测试完成")

    @staticmethod
    def _create_test_worker(employee_id, name, department="开发部"):
        """创建测试用员工对象"""
        return AIWorker(
            employee_id=employee_id,
            name=name,
            department=department,
            roles=["DEV", "TEST"],
            daily_work_hours=8.0,
            task_list=[]
        )

    def setUp(self):
        """每个测试前的准备"""
        self.logger.info("\n" + "-" * 60)

    def test_01_create(self):
        """测试01: 创建员工"""
        self.logger.info("测试01: 创建员工")
        worker = self._create_test_worker("EMP_001", "张三")
        result = self.service.create(worker)
        self.assertTrue(result)
        self.logger.info(f"创建员工成功: {worker.employee_id}")

    def test_02_read(self):
        """测试02: 读取员工"""
        self.logger.info("测试02: 读取员工")
        worker = self._create_test_worker("EMP_002", "李四")
        self.service.create(worker)
        read_worker = self.service.read("EMP_002")
        self.assertIsNotNone(read_worker)
        self.assertEqual(read_worker.name, "李四")
        self.logger.info(f"读取员工成功: {read_worker.employee_id}")

    def test_03_update(self):
        """测试03: 更新员工"""
        self.logger.info("测试03: 更新员工")
        worker = self._create_test_worker("EMP_003", "更新前员工")
        self.service.create(worker)
        worker.name = "更新后员工"
        worker.department = "测试部"
        count = self.service.update(worker)
        self.assertEqual(count, 1)
        updated = self.service.read("EMP_003")
        self.assertEqual(updated.name, "更新后员工")
        self.logger.info("更新员工测试通过")

    def test_04_delete(self):
        """测试04: 删除员工"""
        self.logger.info("测试04: 删除员工")
        worker = self._create_test_worker("EMP_004", "待删除员工")
        self.service.create(worker)
        count = self.service.delete("EMP_004")
        self.assertEqual(count, 1)
        deleted = self.service.read("EMP_004")
        self.assertIsNone(deleted)
        self.logger.info("删除员工测试通过")

    def test_05_exists(self):
        """测试05: 检查员工是否存在"""
        self.logger.info("测试05: 检查员工是否存在")
        worker = self._create_test_worker("EMP_005", "存在性测试员工")
        self.service.create(worker)
        exists = self.service.exists("EMP_005")
        self.assertTrue(exists)
        not_exists = self.service.exists("EMP_NONEXISTENT")
        self.assertFalse(not_exists)
        self.logger.info("存在性检查测试通过")

    def test_06_count(self):
        """测试06: 统计员工数量"""
        self.logger.info("测试06: 统计员工数量")
        before_count = self.service.count()
        worker = self._create_test_worker("EMP_006", "统计测试员工")
        self.service.create(worker)
        after_count = self.service.count()
        self.assertEqual(after_count, before_count + 1)
        self.logger.info(f"员工数量: {after_count}")

    def test_07_read_all(self):
        """测试07: 读取所有员工"""
        self.logger.info("测试07: 读取所有员工")
        workers = self.service.read_all()
        self.assertIsInstance(workers, list)
        self.logger.info(f"读取到 {len(workers)} 个员工")

    def test_08_get_by_department(self):
        """测试08: 按部门查询员工"""
        self.logger.info("测试08: 按部门查询员工")
        worker = self._create_test_worker("EMP_008", "部门测试员工", "测试部")
        self.service.create(worker)
        workers = self.service.get_by_department("测试部")
        self.assertIsInstance(workers, list)
        self.logger.info(f"部门员工数量: {len(workers)}")

    def test_09_get_by_org(self):
        """测试09: 按组织查询员工"""
        self.logger.info("测试09: 按组织查询员工")
        worker = self._create_test_worker("EMP_009", "组织测试员工")
        worker._org_id = "ORG_001"
        self.service.create(worker)
        workers = self.service.get_by_org("ORG_001")
        self.assertIsInstance(workers, list)
        self.logger.info(f"组织员工数量: {len(workers)}")

    def test_10_get_by_role(self):
        """测试10: 按角色查询员工"""
        self.logger.info("测试10: 按角色查询员工")
        worker = self._create_test_worker("EMP_010", "角色测试员工")
        worker.roles = ["PM", "DEV"]
        self.service.create(worker)
        workers = self.service.get_by_role("PM")
        self.assertIsInstance(workers, list)
        self.logger.info(f"角色员工数量: {len(workers)}")

    def test_11_create_many(self):
        """测试11: 批量创建员工"""
        self.logger.info("测试11: 批量创建员工")
        workers = [
            self._create_test_worker(f"EMP_BATCH_{i}", f"批量员工{i}")
            for i in range(3)
        ]
        count = self.service.create_many(workers)
        self.assertEqual(count, 3)
        self.logger.info(f"批量创建 {count} 个员工")


if __name__ == '__main__':
    unittest.main()