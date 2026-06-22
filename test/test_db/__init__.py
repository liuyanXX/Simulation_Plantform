"""数据存储服务测试包"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def ensure_tables_exist(db_path: str, db_name: str) -> None:
    """检查数据库表是否存在，如果不存在则抛出异常"""
    from data_storage_services.SQLite.init_db import init_database_from_sql
    init_database_from_sql(db_path, db_name)
    
    from data_storage_services.SQLite.sqlite_operator import SQLiteOperator
    
    operator = SQLiteOperator(db_path, db_name)
    operator.connect()
    try:
        required_tables = [
            'solutions', 'solution_documents', 'tasks', 'ai_workers',
            'organizations', 'roles', 'task_flow_groups', 'tasks_graphs',
            'task_manifests', 'evaluation_indices', 'knowledge',
            'worker_tasks', 'org_workers'
        ]
        missing_tables = []
        for table in required_tables:
            if not operator.table_exists(table):
                missing_tables.append(table)
        
        if missing_tables:
            raise RuntimeError(f"数据表不存在: {', '.join(missing_tables)}")
    finally:
        operator.disconnect()