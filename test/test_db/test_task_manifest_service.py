"""任务清单服务测试

测试TaskManifestService的所有方法。
"""

import unittest
import os
import sys
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from data_storage_services.sql_db_services.task_manifest_service import TaskManifestService
from bo.task_manifest import TaskManifest


class TestTaskManifestService(unittest.TestCase):
    """任务清单服务测试类"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'test_task_manifest_service.log')
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
        cls.logger.info("开始TaskManifestService测试")
        cls.logger.info("=" * 60)

        test_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_data')
        os.makedirs(test_db_path, exist_ok=True)

        from . import ensure_tables_exist
        ensure_tables_exist(test_db_path, "test_manifest.db")

        cls.service = TaskManifestService(
            db_type="sqlite",
            db_config={"db_path": test_db_path, "db_name": "test_manifest.db"}
        )

    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        cls.service.disconnect()
        test_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_data')
        db_file = os.path.join(test_db_path, "test_manifest.db")
        if os.path.exists(db_file):
            os.remove(db_file)
        cls.logger.info("TaskManifestService测试完成")

    @staticmethod
    def _create_test_manifest(manifest_id, manifest_name, solution_id=None):
        """创建测试用任务清单对象"""
        return TaskManifest(
            manifest_id=manifest_id,
            manifest_name=manifest_name,
            description="测试清单描述",
            solution_id=solution_id,
            status="draft",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    def setUp(self):
        """每个测试前的准备"""
        self.logger.info("\n" + "-" * 60)

    def test_01_create(self):
        """测试01: 创建任务清单"""
        self.logger.info("测试01: 创建任务清单")
        manifest = self._create_test_manifest("MANIFEST_001", "测试清单")
        result = self.service.create(manifest)
        self.assertTrue(result)
        self.logger.info(f"创建任务清单成功: {manifest.manifest_id}")

    def test_02_read(self):
        """测试02: 读取任务清单"""
        self.logger.info("测试02: 读取任务清单")
        manifest = self._create_test_manifest("MANIFEST_002", "读取测试清单")
        self.service.create(manifest)
        read_manifest = self.service.read("MANIFEST_002")
        self.assertIsNotNone(read_manifest)
        self.assertEqual(read_manifest.manifest_name, "读取测试清单")
        self.logger.info(f"读取任务清单成功: {read_manifest.manifest_id}")

    def test_03_update(self):
        """测试03: 更新任务清单"""
        self.logger.info("测试03: 更新任务清单")
        manifest = self._create_test_manifest("MANIFEST_003", "更新前清单")
        self.service.create(manifest)
        manifest.manifest_name = "更新后清单"
        manifest.status = "active"
        count = self.service.update(manifest)
        self.assertEqual(count, 1)
        updated = self.service.read("MANIFEST_003")
        self.assertEqual(updated.manifest_name, "更新后清单")
        self.logger.info("更新任务清单测试通过")

    def test_04_delete(self):
        """测试04: 删除任务清单"""
        self.logger.info("测试04: 删除任务清单")
        manifest = self._create_test_manifest("MANIFEST_004", "待删除清单")
        self.service.create(manifest)
        count = self.service.delete("MANIFEST_004")
        self.assertEqual(count, 1)
        deleted = self.service.read("MANIFEST_004")
        self.assertIsNone(deleted)
        self.logger.info("删除任务清单测试通过")

    def test_05_exists(self):
        """测试05: 检查任务清单是否存在"""
        self.logger.info("测试05: 检查任务清单是否存在")
        manifest = self._create_test_manifest("MANIFEST_005", "存在性测试清单")
        self.service.create(manifest)
        exists = self.service.exists("MANIFEST_005")
        self.assertTrue(exists)
        not_exists = self.service.exists("MANIFEST_NONEXISTENT")
        self.assertFalse(not_exists)
        self.logger.info("存在性检查测试通过")

    def test_06_count(self):
        """测试06: 统计任务清单数量"""
        self.logger.info("测试06: 统计任务清单数量")
        before_count = self.service.count()
        manifest = self._create_test_manifest("MANIFEST_006", "统计测试清单")
        self.service.create(manifest)
        after_count = self.service.count()
        self.assertEqual(after_count, before_count + 1)
        self.logger.info(f"任务清单数量: {after_count}")

    def test_07_read_all(self):
        """测试07: 读取所有任务清单"""
        self.logger.info("测试07: 读取所有任务清单")
        manifests = self.service.read_all()
        self.assertIsInstance(manifests, list)
        self.logger.info(f"读取到 {len(manifests)} 个任务清单")

    def test_08_get_by_solution(self):
        """测试08: 按方案查询任务清单"""
        self.logger.info("测试08: 按方案查询任务清单")
        manifest = self._create_test_manifest("MANIFEST_008", "方案测试清单")
        manifest.solution_id = "SOL_001"
        self.service.create(manifest)
        manifests = self.service.get_by_solution("SOL_001")
        self.assertIsInstance(manifests, list)
        self.logger.info(f"方案任务清单数量: {len(manifests)}")

    def test_09_get_by_status(self):
        """测试09: 按状态查询任务清单"""
        self.logger.info("测试09: 按状态查询任务清单")
        manifest = self._create_test_manifest("MANIFEST_009", "状态测试清单")
        manifest.status = "active"
        self.service.create(manifest)
        manifests = self.service.get_by_status("active")
        self.assertIsInstance(manifests, list)
        self.logger.info(f"状态任务清单数量: {len(manifests)}")

    def test_10_create_many(self):
        """测试10: 批量创建任务清单"""
        self.logger.info("测试10: 批量创建任务清单")
        manifests = [
            self._create_test_manifest(f"MANIFEST_BATCH_{i}", f"批量清单{i}")
            for i in range(3)
        ]
        count = self.service.create_many(manifests)
        self.assertEqual(count, 3)
        self.logger.info(f"批量创建 {count} 个任务清单")


if __name__ == '__main__':
    unittest.main()