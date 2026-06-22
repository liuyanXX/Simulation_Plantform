"""SQLite操作器测试

测试SQLiteOperator的所有方法。
"""

import unittest
import os
import sys
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from data_storage_services.SQLite.sqlite_operator import SQLiteOperator


class TestSQLiteOperator(unittest.TestCase):
    """SQLite操作器测试类"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'test_sqlite_operator.log')
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
        cls.logger.info("开始SQLiteOperator测试")
        cls.logger.info("=" * 60)

        cls.test_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_data')
        os.makedirs(cls.test_db_path, exist_ok=True)
        cls.test_db_file = os.path.join(cls.test_db_path, 'test_sqlite.db')
        if os.path.exists(cls.test_db_file):
            os.remove(cls.test_db_file)
        cls.operator = SQLiteOperator(cls.test_db_path, 'test_sqlite.db')
        cls.operator.connect()
        cls.logger.info(f"测试数据库: {cls.operator.db_file}")

    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        cls.operator.disconnect()
        if os.path.exists(cls.test_db_file):
            os.remove(cls.test_db_file)
        cls.logger.info("SQLiteOperator测试完成")

    def setUp(self):
        """每个测试前的准备"""
        self.logger.info("\n" + "-" * 60)
        if self.operator.table_exists('test_table'):
            self.operator.drop_table('test_table')

    def tearDown(self):
        """每个测试后的清理"""
        if self.operator.table_exists('test_table'):
            self.operator.drop_table('test_table')

    def test_01_connect_disconnect(self):
        """测试01: 连接与断开数据库"""
        self.logger.info("测试01: 连接与断开数据库")
        op = SQLiteOperator(self.test_db_path, 'test_conn.db')
        op.connect()
        self.assertIsNotNone(op.connection)
        self.assertIsNotNone(op.cursor)
        op.disconnect()
        self.assertIsNone(op.connection)
        self.assertIsNone(op.cursor)
        self.logger.info("连接与断开测试通过")

    def test_02_create_table(self):
        """测试02: 创建数据表"""
        self.logger.info("测试02: 创建数据表")
        columns = {
            "id": "TEXT PRIMARY KEY",
            "name": "TEXT NOT NULL",
            "age": "INTEGER DEFAULT 0",
            "score": "REAL DEFAULT 0.0"
        }
        self.operator.create_table('test_table', columns)
        self.assertTrue(self.operator.table_exists('test_table'))
        self.logger.info("创建表测试通过")

    def test_03_insert(self):
        """测试03: 插入单条数据"""
        self.logger.info("测试03: 插入单条数据")
        self.operator.create_table('test_table', {
            "id": "TEXT PRIMARY KEY",
            "name": "TEXT NOT NULL",
            "age": "INTEGER DEFAULT 0"
        })
        data = {"id": "001", "name": "张三", "age": 25}
        row_id = self.operator.insert('test_table', data)
        self.assertGreater(row_id, 0)
        self.logger.info(f"插入数据成功, row_id={row_id}")

    def test_04_insert_many(self):
        """测试04: 批量插入数据"""
        self.logger.info("测试04: 批量插入数据")
        self.operator.create_table('test_table', {
            "id": "TEXT PRIMARY KEY",
            "name": "TEXT NOT NULL",
            "age": "INTEGER DEFAULT 0"
        })
        data_list = [
            {"id": "001", "name": "张三", "age": 25},
            {"id": "002", "name": "李四", "age": 30},
            {"id": "003", "name": "王五", "age": 28}
        ]
        count = self.operator.insert_many('test_table', data_list)
        self.assertEqual(count, 3)
        self.logger.info(f"批量插入{count}条数据")

    def test_05_select(self):
        """测试05: 查询数据"""
        self.logger.info("测试05: 查询数据")
        self.operator.create_table('test_table', {
            "id": "TEXT PRIMARY KEY",
            "name": "TEXT NOT NULL",
            "age": "INTEGER DEFAULT 0"
        })
        self.operator.insert('test_table', {"id": "001", "name": "张三", "age": 25})
        self.operator.insert('test_table', {"id": "002", "name": "李四", "age": 30})
        results = self.operator.select('test_table')
        self.assertEqual(len(results), 2)
        self.logger.info(f"查询到{len(results)}条数据")

    def test_06_select_with_where(self):
        """测试06: 带条件查询"""
        self.logger.info("测试06: 带条件查询")
        self.operator.create_table('test_table', {
            "id": "TEXT PRIMARY KEY",
            "name": "TEXT NOT NULL",
            "age": "INTEGER DEFAULT 0"
        })
        self.operator.insert('test_table', {"id": "001", "name": "张三", "age": 25})
        self.operator.insert('test_table', {"id": "002", "name": "李四", "age": 30})
        results = self.operator.select('test_table', where={"name": "张三"})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], "张三")
        self.logger.info("条件查询测试通过")

    def test_07_select_one(self):
        """测试07: 查询单条数据"""
        self.logger.info("测试07: 查询单条数据")
        self.operator.create_table('test_table', {
            "id": "TEXT PRIMARY KEY",
            "name": "TEXT NOT NULL",
            "age": "INTEGER DEFAULT 0"
        })
        self.operator.insert('test_table', {"id": "001", "name": "张三", "age": 25})
        result = self.operator.select_one('test_table', where={"id": "001"})
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], "张三")
        self.logger.info("查询单条测试通过")

    def test_08_update(self):
        """测试08: 更新数据"""
        self.logger.info("测试08: 更新数据")
        self.operator.create_table('test_table', {
            "id": "TEXT PRIMARY KEY",
            "name": "TEXT NOT NULL",
            "age": "INTEGER DEFAULT 0"
        })
        self.operator.insert('test_table', {"id": "001", "name": "张三", "age": 25})
        count = self.operator.update('test_table', {"age": 26}, where={"id": "001"})
        self.assertEqual(count, 1)
        result = self.operator.select_one('test_table', where={"id": "001"})
        self.assertEqual(result['age'], 26)
        self.logger.info("更新数据测试通过")

    def test_09_delete(self):
        """测试09: 删除数据"""
        self.logger.info("测试09: 删除数据")
        self.operator.create_table('test_table', {
            "id": "TEXT PRIMARY KEY",
            "name": "TEXT NOT NULL",
            "age": "INTEGER DEFAULT 0"
        })
        self.operator.insert('test_table', {"id": "001", "name": "张三", "age": 25})
        count = self.operator.delete('test_table', where={"id": "001"})
        self.assertEqual(count, 1)
        result = self.operator.select_one('test_table', where={"id": "001"})
        self.assertIsNone(result)
        self.logger.info("删除数据测试通过")

    def test_10_count(self):
        """测试10: 统计行数"""
        self.logger.info("测试10: 统计行数")
        self.operator.create_table('test_table', {
            "id": "TEXT PRIMARY KEY",
            "name": "TEXT NOT NULL",
            "age": "INTEGER DEFAULT 0"
        })
        self.operator.insert('test_table', {"id": "001", "name": "张三", "age": 25})
        self.operator.insert('test_table', {"id": "002", "name": "李四", "age": 30})
        count = self.operator.count('test_table')
        self.assertEqual(count, 2)
        self.logger.info(f"统计行数: {count}")

    def test_11_exists(self):
        """测试11: 检查数据是否存在"""
        self.logger.info("测试11: 检查数据是否存在")
        self.operator.create_table('test_table', {
            "id": "TEXT PRIMARY KEY",
            "name": "TEXT NOT NULL",
            "age": "INTEGER DEFAULT 0"
        })
        self.operator.insert('test_table', {"id": "001", "name": "张三", "age": 25})
        exists = self.operator.exists('test_table', where={"id": "001"})
        self.assertTrue(exists)
        not_exists = self.operator.exists('test_table', where={"id": "999"})
        self.assertFalse(not_exists)
        self.logger.info("检查存在性测试通过")

    def test_12_get_table_info(self):
        """测试12: 获取表结构信息"""
        self.logger.info("测试12: 获取表结构信息")
        self.operator.create_table('test_table', {
            "id": "TEXT PRIMARY KEY",
            "name": "TEXT NOT NULL",
            "age": "INTEGER DEFAULT 0"
        })
        info = self.operator.get_table_info('test_table')
        self.assertGreaterEqual(len(info), 3)
        self.logger.info(f"表结构信息: {info}")

    def test_13_drop_table(self):
        """测试13: 删除数据表"""
        self.logger.info("测试13: 删除数据表")
        self.operator.create_table('test_table', {
            "id": "TEXT PRIMARY KEY",
            "name": "TEXT NOT NULL"
        })
        self.assertTrue(self.operator.table_exists('test_table'))
        self.operator.drop_table('test_table')
        self.assertFalse(self.operator.table_exists('test_table'))
        self.logger.info("删除表测试通过")

    def test_14_transaction(self):
        """测试14: 事务操作"""
        self.logger.info("测试14: 事务操作")
        self.operator.create_table('test_table', {
            "id": "TEXT PRIMARY KEY",
            "name": "TEXT NOT NULL",
            "age": "INTEGER DEFAULT 0"
        })
        try:
            with self.operator.transaction():
                self.operator.insert('test_table', {"id": "001", "name": "张三", "age": 25})
                self.operator.insert('test_table', {"id": "002", "name": "李四", "age": 30})
            count = self.operator.count('test_table')
            self.assertEqual(count, 2)
            self.logger.info("事务提交测试通过")
        except Exception as e:
            self.logger.error(f"事务测试失败: {e}")

    def test_15_transaction_rollback(self):
        """测试15: 事务回滚"""
        self.logger.info("测试15: 事务回滚")
        self.operator.create_table('test_table', {
            "id": "TEXT PRIMARY KEY",
            "name": "TEXT NOT NULL",
            "age": "INTEGER DEFAULT 0"
        })
        try:
            with self.operator.transaction():
                self.operator.insert('test_table', {"id": "001", "name": "张三", "age": 25})
                raise Exception("模拟错误")
        except:
            pass
        count = self.operator.count('test_table')
        self.assertEqual(count, 0)
        self.logger.info("事务回滚测试通过")

    def test_16_select_with_order_by(self):
        """测试16: 带排序查询"""
        self.logger.info("测试16: 带排序查询")
        self.operator.create_table('test_table', {
            "id": "TEXT PRIMARY KEY",
            "name": "TEXT NOT NULL",
            "age": "INTEGER DEFAULT 0"
        })
        self.operator.insert('test_table', {"id": "001", "name": "张三", "age": 25})
        self.operator.insert('test_table', {"id": "002", "name": "李四", "age": 30})
        self.operator.insert('test_table', {"id": "003", "name": "王五", "age": 20})
        results = self.operator.select('test_table', order_by='age DESC')
        self.assertEqual(results[0]['name'], "李四")
        self.logger.info("带排序查询测试通过")

    def test_17_select_with_limit(self):
        """测试17: 带限制查询"""
        self.logger.info("测试17: 带限制查询")
        self.operator.create_table('test_table', {
            "id": "TEXT PRIMARY KEY",
            "name": "TEXT NOT NULL",
            "age": "INTEGER DEFAULT 0"
        })
        for i in range(10):
            self.operator.insert('test_table', {"id": f"00{i}", "name": f"用户{i}", "age": 20 + i})
        results = self.operator.select('test_table', limit=5)
        self.assertEqual(len(results), 5)
        self.logger.info("带限制查询测试通过")


if __name__ == '__main__':
    unittest.main()