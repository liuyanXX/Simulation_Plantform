"""角色服务测试

测试RoleService的所有方法。
"""

import unittest
import os
import sys
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from data_storage_services.sql_db_services.role_service import RoleService
from bo.role import Role


class TestRoleService(unittest.TestCase):
    """角色服务测试类"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'test_role_service.log')
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
        cls.logger.info("开始RoleService测试")
        cls.logger.info("=" * 60)

        test_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_data')
        os.makedirs(test_db_path, exist_ok=True)

        from . import ensure_tables_exist
        ensure_tables_exist(test_db_path, "test_role.db")

        cls.service = RoleService(
            db_type="sqlite",
            db_config={"db_path": test_db_path, "db_name": "test_role.db"}
        )

    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        cls.service.disconnect()
        test_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_data')
        db_file = os.path.join(test_db_path, "test_role.db")
        if os.path.exists(db_file):
            os.remove(db_file)
        cls.logger.info("RoleService测试完成")

    @staticmethod
    def _create_test_role(name, description="测试角色描述"):
        """创建测试用角色对象"""
        return Role(
            name=name,
            description=description,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    def setUp(self):
        """每个测试前的准备"""
        self.logger.info("\n" + "-" * 60)

    def test_01_create(self):
        """测试01: 创建角色"""
        self.logger.info("测试01: 创建角色")
        role = self._create_test_role("TEST_ROLE_001", "测试角色")
        result = self.service.create(role)
        self.assertTrue(result)
        self.logger.info(f"创建角色成功: {role.name}")

    def test_02_read(self):
        """测试02: 读取角色"""
        self.logger.info("测试02: 读取角色")
        role = self._create_test_role("TEST_ROLE_002", "读取测试角色")
        self.service.create(role)
        read_role = self.service.read("TEST_ROLE_002")
        self.assertIsNotNone(read_role)
        self.assertEqual(read_role.name, "TEST_ROLE_002")
        self.logger.info(f"读取角色成功: {read_role.name}")

    def test_03_update(self):
        """测试03: 更新角色"""
        self.logger.info("测试03: 更新角色")
        role = self._create_test_role("TEST_ROLE_003", "更新前角色")
        self.service.create(role)
        role.description = "更新后描述"
        count = self.service.update(role)
        self.assertEqual(count, 1)
        updated = self.service.read("TEST_ROLE_003")
        self.assertEqual(updated.description, "更新后描述")
        self.logger.info("更新角色测试通过")

    def test_04_delete(self):
        """测试04: 删除角色"""
        self.logger.info("测试04: 删除角色")
        role = self._create_test_role("TEST_ROLE_004", "待删除角色")
        self.service.create(role)
        count = self.service.delete("TEST_ROLE_004")
        self.assertEqual(count, 1)
        deleted = self.service.read("TEST_ROLE_004")
        self.assertIsNone(deleted)
        self.logger.info("删除角色测试通过")

    def test_05_exists(self):
        """测试05: 检查角色是否存在"""
        self.logger.info("测试05: 检查角色是否存在")
        role = self._create_test_role("TEST_ROLE_005", "存在性测试角色")
        self.service.create(role)
        exists = self.service.exists("TEST_ROLE_005")
        self.assertTrue(exists)
        not_exists = self.service.exists("TEST_ROLE_NONEXISTENT")
        self.assertFalse(not_exists)
        self.logger.info("存在性检查测试通过")

    def test_06_count(self):
        """测试06: 统计角色数量"""
        self.logger.info("测试06: 统计角色数量")
        before_count = self.service.count()
        role = self._create_test_role("TEST_ROLE_006", "统计测试角色")
        self.service.create(role)
        after_count = self.service.count()
        self.assertEqual(after_count, before_count + 1)
        self.logger.info(f"角色数量: {after_count}")

    def test_07_read_all(self):
        """测试07: 读取所有角色"""
        self.logger.info("测试07: 读取所有角色")
        roles = self.service.read_all()
        self.assertIsInstance(roles, list)
        self.logger.info(f"读取到 {len(roles)} 个角色")

    def test_08_create_many(self):
        """测试08: 批量创建角色"""
        self.logger.info("测试08: 批量创建角色")
        roles = [
            self._create_test_role(f"TEST_ROLE_BATCH_{i}", f"批量角色{i}")
            for i in range(3)
        ]
        count = self.service.create_many(roles)
        self.assertEqual(count, 3)
        self.logger.info(f"批量创建 {count} 个角色")


if __name__ == '__main__':
    unittest.main()