import os
import sys
import logging
import unittest
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from solution_management_services.solution_management_service import (
    SolutionManagementService,
    DocumentQueryFilter
)
from bo.solution import SolutionDocument, DocumentType

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_solution_management_service.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TestSolutionManagementService(unittest.TestCase):
    """测试SolutionManagementService"""

    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        logger.info("=" * 60)
        logger.info("开始测试SolutionManagementService")
        logger.info("=" * 60)
        
        cls.test_storage = "test_doc_service_data"
        os.makedirs(cls.test_storage, exist_ok=True)
        
        cls.service = SolutionManagementService(storage_path=cls.test_storage)
        
        cls.test_doc = SolutionDocument(
            document_id="DOC_TEST_001",
            file_name="test_document.txt",
            version="1.0",
            document_type=DocumentType.MAIN,
            text_content="这是测试文档内容",
            description="测试文档描述"
        )

    @classmethod
    def tearDownClass(cls):
        """清理测试数据"""
        import shutil
        if os.path.exists(cls.test_storage):
            shutil.rmtree(cls.test_storage)
        logger.info("测试数据已清理")

    def test_01_create_document(self):
        """测试创建文档"""
        logger.info("测试01: 创建文档")
        
        doc = self.service.create_document(self.test_doc)
        
        self.assertIsNotNone(doc)
        self.assertEqual(doc.document_id, "DOC_TEST_001")
        self.assertEqual(doc.file_name, "test_document.txt")
        
        logger.info(f"  ✓ 创建成功: {doc.document_id}")

    def test_02_create_duplicate_document(self):
        """测试创建重复文档"""
        logger.info("测试02: 创建重复文档（应报错）")
        
        with self.assertRaises(ValueError):
            self.service.create_document(self.test_doc)
        
        logger.info("  ✓ 重复文档检测正常")

    def test_03_get_document(self):
        """测试获取文档"""
        logger.info("测试03: 获取文档")
        
        doc = self.service.get_document("DOC_TEST_001")
        
        self.assertIsNotNone(doc)
        self.assertEqual(doc.document_id, "DOC_TEST_001")
        
        logger.info(f"  ✓ 获取成功: {doc.file_name}")

    def test_04_get_nonexistent_document(self):
        """测试获取不存在的文档"""
        logger.info("测试04: 获取不存在的文档")
        
        doc = self.service.get_document("DOC_NOT_EXIST")
        
        self.assertIsNone(doc)
        logger.info("  ✓ 返回None")

    def test_05_list_documents(self):
        """测试查询文档列表"""
        logger.info("测试05: 查询文档列表")
        
        docs = self.service.list_documents()
        
        self.assertTrue(len(docs) > 0)
        logger.info(f"  ✓ 查询到 {len(docs)} 个文档")

    def test_06_list_documents_with_filter(self):
        """测试带条件查询"""
        logger.info("测试06: 带条件查询文档列表")
        
        # 添加更多测试文档
        doc2 = SolutionDocument(
            document_id="DOC_TEST_002",
            file_name="other_doc.txt",
            version="1.0",
            document_type=DocumentType.SUPPLEMENTARY,
            text_content="补充文档内容",
            description="补充文档"
        )
        self.service.create_document(doc2)
        
        # 按类型过滤
        filter_condition = DocumentQueryFilter(document_type=DocumentType.MAIN)
        docs = self.service.list_documents(filter_condition)
        
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].document_id, "DOC_TEST_001")
        
        logger.info("  ✓ 类型过滤正常")

    def test_07_list_documents_with_keyword(self):
        """测试关键词搜索"""
        logger.info("测试07: 关键词搜索")
        
        filter_condition = DocumentQueryFilter(keyword="测试")
        docs = self.service.list_documents(filter_condition)
        
        self.assertTrue(len(docs) > 0)
        logger.info(f"  ✓ 关键词搜索找到 {len(docs)} 个文档")

    def test_08_get_all_documents(self):
        """测试获取所有文档"""
        logger.info("测试08: 获取所有文档")
        
        docs = self.service.get_all_documents()
        
        self.assertTrue(len(docs) >= 2)
        logger.info(f"  ✓ 共有 {len(docs)} 个文档")

    def test_09_document_exists(self):
        """测试文档存在检查"""
        logger.info("测试09: 文档存在检查")
        
        exists = self.service.document_exists("DOC_TEST_001")
        not_exists = self.service.document_exists("DOC_NOT_EXIST")
        
        self.assertTrue(exists)
        self.assertFalse(not_exists)
        
        logger.info("  ✓ 存在检查正常")

    def test_10_update_document(self):
        """测试更新文档"""
        logger.info("测试10: 更新文档")
        
        updated = self.service.update_document(
            "DOC_TEST_001",
            version="2.0",
            description="更新后的描述"
        )
        
        self.assertEqual(updated.version, "2.0")
        self.assertEqual(updated.description, "更新后的描述")
        
        logger.info(f"  ✓ 更新成功: {updated.version}")

    def test_11_update_document_content(self):
        """测试更新文档内容"""
        logger.info("测试11: 更新文档内容")
        
        updated = self.service.update_document_content(
            "DOC_TEST_001",
            "更新后的文本内容"
        )
        
        self.assertEqual(updated.text_content, "更新后的文本内容")
        logger.info("  ✓ 内容更新成功")

    def test_12_update_document_version(self):
        """测试更新文档版本"""
        logger.info("测试12: 更新文档版本")
        
        updated = self.service.update_document_version("DOC_TEST_001", "3.0")
        
        self.assertEqual(updated.version, "3.0")
        logger.info(f"  ✓ 版本更新成功: {updated.version}")

    def test_13_update_nonexistent_document(self):
        """测试更新不存在的文档"""
        logger.info("测试13: 更新不存在的文档（应报错）")
        
        with self.assertRaises(ValueError):
            self.service.update_document("DOC_NOT_EXIST", version="2.0")
        
        logger.info("  ✓ 错误处理正常")

    def test_14_delete_document(self):
        """测试删除文档"""
        logger.info("测试14: 删除文档")
        
        result = self.service.delete_document("DOC_TEST_002")
        
        self.assertTrue(result)
        self.assertFalse(self.service.document_exists("DOC_TEST_002"))
        
        logger.info("  ✓ 删除成功")

    def test_15_delete_nonexistent_document(self):
        """测试删除不存在的文档"""
        logger.info("测试15: 删除不存在的文档（应报错）")
        
        with self.assertRaises(ValueError):
            self.service.delete_document("DOC_NOT_EXIST")
        
        logger.info("  ✓ 错误处理正常")

    def test_16_save_document(self):
        """测试保存文档"""
        logger.info("测试16: 保存文档")
        
        path = self.service.save_document("DOC_TEST_001")
        
        self.assertTrue(os.path.exists(path))
        logger.info(f"  ✓ 保存成功: {path}")

    def test_17_save_all_documents(self):
        """测试保存所有文档"""
        logger.info("测试17: 保存所有文档")
        
        paths = self.service.save_all_documents()
        
        self.assertTrue(len(paths) > 0)
        logger.info(f"  ✓ 保存了 {len(paths)} 个文档")

    def test_18_load_document(self):
        """测试加载文档"""
        logger.info("测试18: 加载文档")
        
        # 创建一个新的service实例来测试加载
        new_service = SolutionManagementService(storage_path=self.test_storage)
        count = new_service.load_all_documents()
        
        self.assertTrue(count > 0)
        loaded_doc = new_service.get_document("DOC_TEST_001")
        self.assertIsNotNone(loaded_doc)
        
        logger.info(f"  ✓ 加载了 {count} 个文档")

    def test_19_to_plain_text(self):
        """测试转换为纯文本"""
        logger.info("测试19: 转换为纯文本")
        
        text = self.service.to_plain_text("DOC_TEST_001")
        
        self.assertIsNotNone(text)
        self.assertIn("更新后的文本内容", text)
        
        logger.info("  ✓ 文本转换成功")

    def test_20_to_plain_text_with_metadata(self):
        """测试转换为带元数据的纯文本"""
        logger.info("测试20: 转换为带元数据的纯文本")
        
        text = self.service.to_plain_text_with_metadata("DOC_TEST_001")
        
        self.assertIsNotNone(text)
        self.assertIn("文档ID:", text)
        self.assertIn("文件名:", text)
        self.assertIn("版本:", text)
        
        logger.info("  ✓ 带元数据文本转换成功")

    def test_21_get_document_count(self):
        """测试获取文档数量"""
        logger.info("测试21: 获取文档数量")
        
        count = self.service.get_document_count()
        
        self.assertTrue(count >= 1)
        logger.info(f"  ✓ 文档数量: {count}")

    def test_22_get_statistics(self):
        """测试获取统计信息"""
        logger.info("测试22: 获取统计信息")
        
        stats = self.service.get_statistics()
        
        self.assertIn("total_count", stats)
        self.assertIn("type_distribution", stats)
        self.assertIn("format_distribution", stats)
        
        logger.info(f"  ✓ 统计信息: {stats}")

    def test_23_create_document_from_file(self):
        """测试从文件创建文档"""
        logger.info("测试23: 从文件创建文档")
        
        # 创建临时测试文件
        temp_file = "temp_test.txt"
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write("文件内容")
        
        doc = self.service.create_document_from_file(
            document_id="DOC_FILE_001",
            file_path=temp_file,
            version="1.0",
            description="从文件创建"
        )
        
        self.assertIsNotNone(doc)
        self.assertEqual(doc.document_id, "DOC_FILE_001")
        self.assertEqual(doc.text_content, "文件内容")
        
        # 清理临时文件
        os.remove(temp_file)
        logger.info(f"  ✓ 从文件创建成功: {doc.file_name}")


if __name__ == '__main__':
    os.makedirs('logs', exist_ok=True)
    unittest.main(verbosity=2)