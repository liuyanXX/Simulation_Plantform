import os
import sqlite3
from typing import Optional


def init_database_from_sql(db_path: str = "Simulation_Plantform/DB/SQLite", db_name: str = "simulation.db") -> None:
    """
    通过执行 SQL 文件初始化数据库
    
    :param db_path: 数据库文件路径
    :param db_name: 数据库名称
    """
    os.makedirs(db_path, exist_ok=True)
    db_file = os.path.join(db_path, db_name)
    
    sql_file_path = os.path.join(os.path.dirname(__file__), "sqlite_db_init.sql")
    
    try:
        with open(sql_file_path, "r", encoding="utf-8") as f:
            sql_content = f.read()
        
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            cursor.executescript(sql_content)
            conn.commit()
        
        print(f"数据库初始化完成: {db_file}")
    except FileNotFoundError:
        raise RuntimeError(f"SQL 文件不存在: {sql_file_path}")
    except sqlite3.Error as e:
        raise RuntimeError(f"数据库初始化失败: {str(e)}")


if __name__ == "__main__":
    init_database_from_sql()