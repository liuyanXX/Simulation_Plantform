"""组织服务测试

测试OrganizationService的所有方法。
"""

import unittest
import os
import sys
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from data_storage_services.sql_db_services.organization_service import OrganizationService
from bo.organization import Organization


class TestOrganizationService(unittest.TestCase):
    """组织服务测试类"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'test_organization_service.log')
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
        cls.logger.info("开始OrganizationService测试")
        cls.logger.info("=" * 60)

        test_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_data')
        os.makedirs(test_db_path, exist_ok=True)

        from . import ensure_tables_exist
        ensure_tables_exist(test_db_path, "test_org.db")

        cls.service = OrganizationService(
            db_type="sqlite",
            db_config={"db_path": test_db_path, "db_name": "test_org.db"}
        )

    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        cls.service.disconnect()
        test_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_data')
        db_file = os.path.join(test_db_path, "test_org.db")
        if os.path.exists(db_file):
            os.remove(db_file)
        cls.logger.info("OrganizationService测试完成")

    @staticmethod
    def _create_test_org(org_id, name, parent=None):
        """创建测试用组织对象"""
        return Organization(
            org_id=org_id,
            name=name,
            parent=parent,
            children=[],
            workers=[]
        )

    def setUp(self):
        """每个测试前的准备"""
        self.logger.info("\n" + "-" * 60)

    def test_01_create(self):
        """测试01: 创建组织"""
        self.logger.info("测试01: 创建组织")
        org = self._create_test_org("ORG_001", "测试组织")
        result = self.service.create(org)
        self.assertTrue(result)
        self.logger.info(f"创建组织成功: {org.org_id}")

    def test_02_read(self):
        """测试02: 读取组织"""
        self.logger.info("测试02: 读取组织")
        org = self._create_test_org("ORG_002", "读取测试组织")
        self.service.create(org)
        read_org = self.service.read("ORG_002")
        self.assertIsNotNone(read_org)
        self.assertEqual(read_org.name, "读取测试组织")
        self.logger.info(f"读取组织成功: {read_org.org_id}")

    def test_03_update(self):
        """测试03: 更新组织"""
        self.logger.info("测试03: 更新组织")
        org = self._create_test_org("ORG_003", "更新前组织")
        self.service.create(org)
        org.name = "更新后组织"
        count = self.service.update(org)
        self.assertEqual(count, 1)
        updated = self.service.read("ORG_003")
        self.assertEqual(updated.name, "更新后组织")
        self.logger.info("更新组织测试通过")

    def test_04_delete(self):
        """测试04: 删除组织"""
        self.logger.info("测试04: 删除组织")
        org = self._create_test_org("ORG_004", "待删除组织")
        self.service.create(org)
        count = self.service.delete("ORG_004")
        self.assertEqual(count, 1)
        deleted = self.service.read("ORG_004")
        self.assertIsNone(deleted)
        self.logger.info("删除组织测试通过")

    def test_05_exists(self):
        """测试05: 检查组织是否存在"""
        self.logger.info("测试05: 检查组织是否存在")
        org = self._create_test_org("ORG_005", "存在性测试组织")
        self.service.create(org)
        exists = self.service.exists("ORG_005")
        self.assertTrue(exists)
        not_exists = self.service.exists("ORG_NONEXISTENT")
        self.assertFalse(not_exists)
        self.logger.info("存在性检查测试通过")

    def test_06_count(self):
        """测试06: 统计组织数量"""
        self.logger.info("测试06: 统计组织数量")
        before_count = self.service.count()
        org = self._create_test_org("ORG_006", "统计测试组织")
        self.service.create(org)
        after_count = self.service.count()
        self.assertEqual(after_count, before_count + 1)
        self.logger.info(f"组织数量: {after_count}")

    def test_07_read_all(self):
        """测试07: 读取所有组织"""
        self.logger.info("测试07: 读取所有组织")
        orgs = self.service.read_all()
        self.assertIsInstance(orgs, list)
        self.logger.info(f"读取到 {len(orgs)} 个组织")

    def test_08_get_root_organizations(self):
        """测试08: 获取根组织列表"""
        self.logger.info("测试08: 获取根组织列表")
        org = self._create_test_org("ORG_008_ROOT", "根组织测试")
        org.parent = None
        self.service.create(org)
        roots = self.service.get_root_organizations()
        self.assertIsInstance(roots, list)
        self.logger.info(f"根组织数量: {len(roots)}")

    def test_09_get_children(self):
        """测试09: 获取子组织"""
        self.logger.info("测试09: 获取子组织")
        parent_org = self._create_test_org("ORG_009_PARENT", "父组织")
        self.service.create(parent_org)
        child_org = self._create_test_org("ORG_009_CHILD", "子组织")
        child_org.parent = parent_org
        self.service.create(child_org)
        children = self.service.get_children("ORG_009_PARENT")
        self.assertIsInstance(children, list)
        self.logger.info(f"子组织数量: {len(children)}")

    def test_10_create_many(self):
        """测试11: 批量创建组织"""
        self.logger.info("测试11: 批量创建组织")
        orgs = [
            self._create_test_org(f"ORG_BATCH_{i}", f"批量组织{i}")
            for i in range(3)
        ]
        count = self.service.create_many(orgs)
        self.assertEqual(count, 3)
        self.logger.info(f"批量创建 {count} 个组织")


if __name__ == '__main__':
    unittest.main()