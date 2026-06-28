"""SQLite操作类

提供SQLite数据库的基础CRUD操作服务。
"""

import sqlite3
import os
import json
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from contextlib import contextmanager


class SQLiteOperator:
    """
    SQLite操作类
    
    提供SQLite数据库的基础操作服务，包括创建表、插入、删除、修改、查询等。
    
    :param db_path: 数据库文件路径
    :param db_name: 数据库名称
    
    示例用法：
        operator = SQLiteOperator(db_path="DB/SQLite", db_name="simulation.db")
        operator.connect()
        operator.create_table("users", {"id": "TEXT PRIMARY KEY", "name": "TEXT"})
        operator.insert("users", {"id": "1", "name": "张三"})
        results = operator.select("users", where={"id": "1"})
        operator.disconnect()
    """
    
    def __init__(self, db_path: str = "DB/SQLite", db_name: str = "simulation.db"):
        """
        初始化SQLite操作器
        
        :param db_path: 数据库文件存放目录（相对路径会解析为相对于SQLite目录的绝对路径）
        :param db_name: 数据库文件名
        """
        # 统一解析为绝对路径：以 sqlite_operator.py 所在目录为基准，
        # 即 Simulation_Plantform/data_storage_services/SQLite/
        # 向上两级到 data_storage_services，再向上一级到 Simulation_Plantform/
        sqlite_dir = os.path.dirname(os.path.abspath(__file__))          # .../data_storage_services/SQLite
        services_dir = os.path.dirname(sqlite_dir)                       # .../data_storage_services
        project_root = os.path.dirname(services_dir)                      # .../Simulation_Plantform
        abs_db_path = os.path.abspath(os.path.join(project_root, db_path))
        
        self.db_path = abs_db_path
        self.db_name = db_name
        self.db_file = os.path.join(self.db_path, db_name)
        self.connection: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self.logger = logging.getLogger(__name__)
        
        # 确保数据库目录存在
        os.makedirs(self.db_path, exist_ok=True)
    
    def connect(self) -> None:
        """
        连接到SQLite数据库
        
        如果数据库文件不存在，会自动创建。
        """
        try:
            self.connection = sqlite3.connect(self.db_file)
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
            self.logger.info(f"成功连接到数据库: {self.db_file}")
        except sqlite3.Error as e:
            self.logger.error(f"连接数据库失败: {e}")
            raise
    
    def disconnect(self) -> None:
        """
        断开与SQLite数据库的连接
        """
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.info(f"已断开数据库连接: {self.db_file}")
    
    @contextmanager
    def transaction(self):
        """
        事务上下文管理器
        
        用法：
            with operator.transaction():
                operator.insert(...)
                operator.update(...)
        """
        try:
            yield
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"事务执行失败，已回滚: {e}")
            raise
    
    def execute(self, sql: str, params: Tuple = ()) -> sqlite3.Cursor:
        """
        执行SQL语句
        
        :param sql: SQL语句
        :param params: 参数元组
        :return: 游标对象
        """
        try:
            self.cursor.execute(sql, params)
            self.connection.commit()
            return self.cursor
        except sqlite3.Error as e:
            self.logger.error(f"执行SQL失败: {sql}, 错误: {e}")
            raise
    
    def execute_script(self, script: str) -> None:
        """
        执行SQL脚本（多条语句）
        
        :param script: SQL脚本
        """
        try:
            self.cursor.executescript(script)
            self.connection.commit()
            self.logger.info("SQL脚本执行成功")
        except sqlite3.Error as e:
            self.logger.error(f"执行SQL脚本失败: {e}")
            raise
    
    def table_exists(self, table_name: str) -> bool:
        """
        检查表是否存在
        
        :param table_name: 表名
        :return: 存在返回True，否则返回False
        """
        sql = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        self.cursor.execute(sql, (table_name,))
        return self.cursor.fetchone() is not None
    
    def create_table(self, table_name: str, columns: Dict[str, str], 
                     if_not_exists: bool = True) -> None:
        """
        创建数据表
        
        :param table_name: 表名
        :param columns: 列定义字典，键为列名，值为列类型和约束
        :param if_not_exists: 如果表已存在是否跳过
        
        示例：
            create_table("users", {
                "id": "TEXT PRIMARY KEY",
                "name": "TEXT NOT NULL",
                "age": "INTEGER DEFAULT 0"
            })
        """
        exists_clause = "IF NOT EXISTS " if if_not_exists else ""
        columns_def = ", ".join([f"{col} {dtype}" for col, dtype in columns.items()])
        sql = f"CREATE TABLE {exists_clause}{table_name} ({columns_def})"
        
        try:
            self.execute(sql)
            self.logger.info(f"创建表成功: {table_name}")
        except sqlite3.Error as e:
            self.logger.error(f"创建表失败: {table_name}, 错误: {e}")
            raise
    
    def drop_table(self, table_name: str, if_exists: bool = True) -> None:
        """
        删除数据表
        
        :param table_name: 表名
        :param if_exists: 如果表不存在是否跳过
        """
        exists_clause = "IF EXISTS " if if_exists else ""
        sql = f"DROP TABLE {exists_clause}{table_name}"
        
        try:
            self.execute(sql)
            self.logger.info(f"删除表成功: {table_name}")
        except sqlite3.Error as e:
            self.logger.error(f"删除表失败: {table_name}, 错误: {e}")
            raise
    
    def add_column(self, table_name: str, column_name: str, 
                   column_type: str, default_value: Any = None) -> None:
        """
        添加列到现有表
        
        :param table_name: 表名
        :param column_name: 列名
        :param column_type: 列类型
        :param default_value: 默认值
        """
        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        if default_value is not None:
            if isinstance(default_value, str):
                sql += f" DEFAULT '{default_value}'"
            else:
                sql += f" DEFAULT {default_value}"
        
        try:
            self.execute(sql)
            self.logger.info(f"添加列成功: {table_name}.{column_name}")
        except sqlite3.Error as e:
            self.logger.error(f"添加列失败: {table_name}.{column_name}, 错误: {e}")
            raise
    
    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """
        获取表结构信息
        
        :param table_name: 表名
        :return: 列信息列表
        """
        sql = f"PRAGMA table_info({table_name})"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]
    
    def insert(self, table_name: str, data: Dict[str, Any]) -> int:
        """
        插入数据
        
        :param table_name: 表名
        :param data: 数据字典
        :return: 插入的行ID
        """
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        values = self._serialize_values(data)
        
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        
        try:
            self.cursor.execute(sql, values)
            self.connection.commit()
            row_id = self.cursor.lastrowid
            self.logger.debug(f"插入数据成功: {table_name}, row_id={row_id}")
            return row_id
        except sqlite3.Error as e:
            self.logger.error(f"插入数据失败: {table_name}, 错误: {e}")
            raise
    
    def insert_many(self, table_name: str, data_list: List[Dict[str, Any]]) -> int:
        """
        批量插入数据
        
        :param table_name: 表名
        :param data_list: 数据字典列表
        :return: 插入的行数
        """
        if not data_list:
            return 0
        
        columns = ", ".join(data_list[0].keys())
        placeholders = ", ".join(["?" for _ in data_list[0]])
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        
        values_list = [self._serialize_values(data) for data in data_list]
        
        try:
            self.cursor.executemany(sql, values_list)
            self.connection.commit()
            row_count = self.cursor.rowcount
            self.logger.debug(f"批量插入数据成功: {table_name}, 行数={row_count}")
            return row_count
        except sqlite3.Error as e:
            self.logger.error(f"批量插入数据失败: {table_name}, 错误: {e}")
            raise
    
    def select(self, table_name: str, columns: List[str] = None,
               where: Dict[str, Any] = None, order_by: str = None,
               limit: int = None, offset: int = None) -> List[Dict[str, Any]]:
        """
        查询数据
        
        :param table_name: 表名
        :param columns: 要查询的列名列表，None表示所有列
        :param where: 条件字典
        :param order_by: 排序字段
        :param limit: 返回行数限制
        :param offset: 偏移量
        :return: 查询结果列表
        """
        col_str = ", ".join(columns) if columns else "*"
        sql = f"SELECT {col_str} FROM {table_name}"
        params = []
        
        if where:
            where_clause, params = self._build_where_clause(where)
            sql += f" WHERE {where_clause}"
        
        if order_by:
            sql += f" ORDER BY {order_by}"
        
        if limit:
            sql += f" LIMIT {limit}"
            if offset:
                sql += f" OFFSET {offset}"
        
        try:
            self.cursor.execute(sql, params)
            rows = self.cursor.fetchall()
            results = [self._deserialize_row(row) for row in rows]
            self.logger.debug(f"查询数据成功: {table_name}, 行数={len(results)}")
            return results
        except sqlite3.Error as e:
            self.logger.error(f"查询数据失败: {table_name}, 错误: {e}")
            raise
    
    def select_one(self, table_name: str, columns: List[str] = None,
                   where: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        查询单条数据
        
        :param table_name: 表名
        :param columns: 要查询的列名列表
        :param where: 条件字典
        :return: 查询结果字典，未找到返回None
        """
        results = self.select(table_name, columns, where, limit=1)
        return results[0] if results else None
    
    def update(self, table_name: str, data: Dict[str, Any],
               where: Dict[str, Any]) -> int:
        """
        更新数据
        
        :param table_name: 表名
        :param data: 要更新的数据字典
        :param where: 条件字典
        :return: 更新的行数
        """
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        set_values = self._serialize_values(data)
        
        where_clause, where_values = self._build_where_clause(where)
        
        sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
        params = set_values + where_values
        
        try:
            self.cursor.execute(sql, params)
            self.connection.commit()
            row_count = self.cursor.rowcount
            self.logger.debug(f"更新数据成功: {table_name}, 行数={row_count}")
            return row_count
        except sqlite3.Error as e:
            self.logger.error(f"更新数据失败: {table_name}, 错误: {e}")
            raise
    
    def delete(self, table_name: str, where: Dict[str, Any]) -> int:
        """
        删除数据
        
        :param table_name: 表名
        :param where: 条件字典
        :return: 删除的行数
        """
        where_clause, params = self._build_where_clause(where)
        sql = f"DELETE FROM {table_name} WHERE {where_clause}"
        
        try:
            self.cursor.execute(sql, params)
            self.connection.commit()
            row_count = self.cursor.rowcount
            self.logger.debug(f"删除数据成功: {table_name}, 行数={row_count}")
            return row_count
        except sqlite3.Error as e:
            self.logger.error(f"删除数据失败: {table_name}, 错误: {e}")
            raise
    
    def count(self, table_name: str, where: Dict[str, Any] = None) -> int:
        """
        统计行数
        
        :param table_name: 表名
        :param where: 条件字典
        :return: 行数
        """
        sql = f"SELECT COUNT(*) as count FROM {table_name}"
        params = []
        
        if where:
            where_clause, params = self._build_where_clause(where)
            sql += f" WHERE {where_clause}"
        
        self.cursor.execute(sql, params)
        result = self.cursor.fetchone()
        return result['count'] if result else 0
    
    def exists(self, table_name: str, where: Dict[str, Any]) -> bool:
        """
        检查数据是否存在
        
        :param table_name: 表名
        :param where: 条件字典
        :return: 存在返回True，否则返回False
        """
        return self.count(table_name, where) > 0
    
    def _build_where_clause(self, where: Dict[str, Any]) -> Tuple[str, List]:
        """
        构建WHERE子句
        
        :param where: 条件字典
        :return: (WHERE子句字符串, 参数列表)
        """
        conditions = []
        params = []
        
        for key, value in where.items():
            if value is None:
                conditions.append(f"{key} IS NULL")
            elif isinstance(value, (list, tuple)):
                placeholders = ", ".join(["?" for _ in value])
                conditions.append(f"{key} IN ({placeholders})")
                params.extend(value)
            else:
                conditions.append(f"{key} = ?")
                params.append(value)
        
        return " AND ".join(conditions), params
    
    def _serialize_values(self, data: Dict[str, Any]) -> List:
        """
        序列化值列表
        
        将Python对象转换为SQLite可存储的格式。
        
        :param data: 数据字典
        :return: 值列表
        """
        values = []
        for v in data.values():
            if isinstance(v, (dict, list)):
                values.append(json.dumps(v, ensure_ascii=False))
            elif isinstance(v, datetime):
                values.append(v.isoformat())
            elif v is None:
                values.append(None)
            else:
                values.append(v)
        return values
    
    def _deserialize_row(self, row: sqlite3.Row) -> Dict[str, Any]:
        """
        反序列化行数据
        
        将SQLite存储的数据转换回Python对象。
        
        :param row: 数据库行
        :return: 数据字典
        """
        result = dict(row)
        return result
    
    def begin_transaction(self) -> None:
        """开始事务"""
        self.execute("BEGIN TRANSACTION")
    
    def commit(self) -> None:
        """提交事务"""
        self.connection.commit()
    
    def rollback(self) -> None:
        """回滚事务"""
        self.connection.rollback()
    
    def get_all_tables(self) -> List[str]:
        """
        获取所有表名
        
        :return: 表名列表
        """
        sql = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        self.cursor.execute(sql)
        return [row['name'] for row in self.cursor.fetchall()]
    
    def vacuum(self) -> None:
        """执行VACUUM操作，优化数据库"""
        self.execute("VACUUM")
        self.logger.info("数据库VACUUM完成")


# 预定义的表结构
TABLE_DEFINITIONS = {
    # 方案表
    "solutions": {
        "solution_id": "TEXT PRIMARY KEY",
        "name": "TEXT NOT NULL",
        "version": "TEXT NOT NULL DEFAULT '1.0'",
        "status": "TEXT NOT NULL DEFAULT 'draft'",
        "priority": "TEXT NOT NULL DEFAULT 'medium'",
        "purpose": "TEXT",
        "objectives": "TEXT",  # JSON
        "initiatives": "TEXT",  # JSON
        "working_mechanism": "TEXT",
        "organization": "TEXT",  # JSON
        "personnel": "TEXT",  # JSON
        "roles": "TEXT",  # JSON
        "work_content": "TEXT",
        "constraints": "TEXT",  # JSON
        "risks": "TEXT",  # JSON
        "issues": "TEXT",  # JSON
        "other_notes": "TEXT",
        "main_document_id": "TEXT",
        "auxiliary_document_ids": "TEXT",  # JSON
        "description": "TEXT",
        "owner": "TEXT",
        "created_by": "TEXT",
        "created_at": "TEXT NOT NULL",
        "updated_at": "TEXT NOT NULL",
        "effective_date": "TEXT",
        "expiry_date": "TEXT",
        "tags": "TEXT",  # JSON
        "metadata": "TEXT"  # JSON
    },
    
    # 方案文档表
    "solution_documents": {
        "document_id": "TEXT PRIMARY KEY",
        "file_name": "TEXT NOT NULL",
        "version": "TEXT NOT NULL",
        "document_type": "TEXT NOT NULL DEFAULT 'attachment'",
        "file_content": "BLOB",
        "text_content": "TEXT",
        "description": "TEXT",
        "format": "TEXT",
        "size": "INTEGER",
        "created_by": "TEXT",
        "created_at": "TEXT NOT NULL",
        "updated_at": "TEXT NOT NULL",
        "related_solution_ids": "TEXT",  # JSON
        "metadata": "TEXT"  # JSON
    },
    
    # 任务表
    "tasks": {
        "task_id": "TEXT PRIMARY KEY",
        "task_name": "TEXT NOT NULL",
        "task_type": "TEXT NOT NULL DEFAULT 'normal'",
        "expected_start_time": "TEXT NOT NULL",
        "expected_end_time": "TEXT NOT NULL",
        "scheduled_start_time": "TEXT",
        "scheduled_end_time": "TEXT",
        "actual_start_time": "TEXT",
        "actual_end_time": "TEXT",
        "content": "TEXT NOT NULL",
        "execute_role": "TEXT NOT NULL",
        "resource_consumption": "REAL NOT NULL",
        "priority": "TEXT NOT NULL DEFAULT 'medium'",
        "output_target_role": "TEXT",
        "next_task_info": "TEXT",  # JSON
        "is_completed": "INTEGER NOT NULL DEFAULT 0",
        "task_source": "TEXT",
        "task_destinations": "TEXT",  # JSON
        "flow_group_id": "TEXT",
        "graph_id": "TEXT",
        "manifest_id": "TEXT"
    },
    
    # 智能员工表
    "ai_workers": {
        "employee_id": "TEXT PRIMARY KEY",
        "name": "TEXT NOT NULL",
        "department": "TEXT NOT NULL",
        "roles": "TEXT NOT NULL",  # JSON
        "daily_work_hours": "REAL NOT NULL DEFAULT 8.0",
        "org_id": "TEXT",
        "created_at": "TEXT NOT NULL",
        "updated_at": "TEXT NOT NULL"
    },
    
    # 组织表
    "organizations": {
        "org_id": "TEXT PRIMARY KEY",
        "name": "TEXT NOT NULL",
        "parent_id": "TEXT",
        "created_at": "TEXT NOT NULL",
        "updated_at": "TEXT NOT NULL"
    },
    
    # 角色表
    "roles": {
        "name": "TEXT PRIMARY KEY",
        "description": "TEXT NOT NULL",
        "created_at": "TEXT NOT NULL",
        "updated_at": "TEXT NOT NULL"
    },
    
    # 任务流组表
    "task_flow_groups": {
        "flow_id": "TEXT PRIMARY KEY",
        "flow_name": "TEXT NOT NULL",
        "description": "TEXT",
        "manifest_id": "TEXT",
        "created_at": "TEXT NOT NULL",
        "updated_at": "TEXT NOT NULL"
    },
    
    # 任务图谱表
    "tasks_graphs": {
        "graph_id": "TEXT PRIMARY KEY",
        "graph_name": "TEXT NOT NULL",
        "description": "TEXT",
        "manifest_id": "TEXT",
        "created_at": "TEXT NOT NULL",
        "updated_at": "TEXT NOT NULL"
    },
    
    # 任务清单表
    "task_manifests": {
        "manifest_id": "TEXT PRIMARY KEY",
        "manifest_name": "TEXT NOT NULL",
        "description": "TEXT",
        "solution_id": "TEXT",
        "status": "TEXT NOT NULL DEFAULT 'draft'",
        "created_at": "TEXT NOT NULL",
        "updated_at": "TEXT NOT NULL"
    },
    
    # 评价指标表
    "evaluation_indices": {
        "index_id": "TEXT PRIMARY KEY",
        "name": "TEXT NOT NULL",
        "description": "TEXT NOT NULL",
        "evaluation_method": "TEXT NOT NULL",
        "agent_ids": "TEXT NOT NULL",  # JSON
        "index_type": "TEXT NOT NULL",
        "index_level": "TEXT NOT NULL",
        "parent_id": "TEXT",
        "weight": "REAL NOT NULL DEFAULT 1.0",
        "score_range": "TEXT NOT NULL DEFAULT '(0, 100)'",
        "created_at": "TEXT NOT NULL",
        "updated_at": "TEXT NOT NULL",
        "is_active": "INTEGER NOT NULL DEFAULT 1"
    },
    
    # 知识表
    "knowledge": {
        "knowledge_id": "TEXT PRIMARY KEY",
        "title": "TEXT NOT NULL",
        "summary": "TEXT NOT NULL",
        "content": "TEXT NOT NULL",
        "index_ids": "TEXT",  # JSON
        "tags": "TEXT",  # JSON
        "category": "TEXT NOT NULL DEFAULT 'evaluation'",
        "created_at": "TEXT NOT NULL",
        "updated_at": "TEXT NOT NULL",
        "is_active": "INTEGER NOT NULL DEFAULT 1"
    },
    
    # 员工-任务关联表
    "worker_tasks": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "employee_id": "TEXT NOT NULL",
        "task_id": "TEXT NOT NULL",
        "assigned_at": "TEXT NOT NULL",
        "status": "TEXT NOT NULL DEFAULT 'pending'"
    },
    
    # 组织-员工关联表
    "org_workers": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "org_id": "TEXT NOT NULL",
        "employee_id": "TEXT NOT NULL"
    },

    # 拆分行为表：记录每次方案拆分的过程和结果
    "decomposition_behaviors": {
        "behavior_id": "TEXT PRIMARY KEY",
        "solution_id": "TEXT NOT NULL",
        "solution_name": "TEXT",
        "strategy": "TEXT NOT NULL DEFAULT 'auto'",
        "status": "TEXT NOT NULL DEFAULT 'completed'",
        "organizations": "TEXT",
        "personnel": "TEXT",
        "roles": "TEXT",
        "task_manifest_id": "TEXT",
        "tasks_graph_id": "TEXT",
        "flow_groups": "TEXT",
        "tasks": "TEXT",
        "process_log": "TEXT",
        "result_summary": "TEXT",
        "created_by": "TEXT",
        "created_at": "TEXT NOT NULL",
        "updated_at": "TEXT NOT NULL"
    },

    # 系统空间 · 组织对象表
    "ssys_organization": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "org_code": "TEXT NOT NULL",
        "org_name": "TEXT NOT NULL",
        "org_type": "TEXT NOT NULL DEFAULT 'ORG'",
        "description": "TEXT",
        "parent_id": "INTEGER",
        "parent_name": "TEXT",
        "sort_order": "INTEGER NOT NULL DEFAULT 0",
        "status": "TEXT NOT NULL DEFAULT 'active'",
        "extra_info": "TEXT",
        "created_at": "TEXT NOT NULL",
        "updated_at": "TEXT NOT NULL"
    }
}


def init_database(db_path: str = "DB/SQLite", db_name: str = "simulation.db") -> SQLiteOperator:
    """
    初始化数据库，创建所有预定义的表
    
    :param db_path: 数据库文件路径
    :param db_name: 数据库名称
    :return: SQLiteOperator 实例
    """
    operator = SQLiteOperator(db_path, db_name)
    operator.connect()
    
    for table_name, columns in TABLE_DEFINITIONS.items():
        if not operator.table_exists(table_name):
            operator.create_table(table_name, columns)
    
    operator.logger.info("数据库初始化完成")
    return operator


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 初始化数据库
    operator = init_database()
    
    # 测试基本操作
    print("=== 测试SQLite操作 ===")
    print(f"所有表: {operator.get_all_tables()}")
    
    # 测试插入
    operator.insert("roles", {
        "name": "DEV",
        "description": "开发人员",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    })
    
    # 测试查询
    roles = operator.select("roles")
    print(f"角色列表: {roles}")
    
    operator.disconnect()
