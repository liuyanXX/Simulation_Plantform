"""关系数据库基础服务类

提供屏蔽底层具体关系数据库实现细节的通用操作服务。
"""

import logging
import json
import os
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, TypeVar, Generic
from datetime import datetime
from pydantic import BaseModel

# 导入SQLite操作子模块
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from SQLite.sqlite_operator import SQLiteOperator, init_database

T = TypeVar('T', bound=BaseModel)


def get_db_config() -> Dict[str, Any]:
    """
    从配置文件读取数据库配置
    
    :return: 包含 db_type 和 db_config 的字典
    """
    config_path = os.path.join(os.path.dirname(__file__), "db_config.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    # 默认配置
    return {
        "db_type": "sqlite",
        "db_config": {
            "db_path": "DB/SQLite",
            "db_name": "simulation.db"
        }
    }


class SQLDatabaseService(ABC, Generic[T]):
    """
    关系数据库基础服务类
    
    提供通用的CRUD操作接口，屏蔽底层具体数据库实现细节。
    子类需要实现具体的业务对象转换逻辑。
    
    配置通过 db_config.json 文件读取。
    """
    
    def __init__(self, db_type: str = None, db_config: Dict[str, Any] = None):
        """
        初始化数据库服务
        
        配置优先从构造函数参数获取，如未提供则从配置文件读取。
        
        :param db_type: 数据库类型（可选，默认从配置文件读取）
        :param db_config: 数据库配置（可选，默认从配置文件读取）
        """
        # 如果未提供配置，则从配置文件读取
        if db_type is None or db_config is None:
            file_config = get_db_config()
            self.db_type = db_type or file_config.get("db_type", "sqlite")
            self.db_config = db_config or file_config.get("db_config", {})
        else:
            self.db_type = db_type
            self.db_config = db_config
        self.logger = logging.getLogger(self.__class__.__name__)
        self._db_operator = None
        
        # 初始化数据库连接
        self._init_connection()
    
    def _init_connection(self) -> None:
        """
        初始化数据库连接
        
        根据db_type选择具体的数据库操作器。
        """
        if self.db_type == "sqlite":
            db_path = self.db_config.get("db_path", "DB/SQLite")
            db_name = self.db_config.get("db_name", "simulation.db")
            self._db_operator = SQLiteOperator(db_path, db_name)
            self._db_operator.connect()
        else:
            raise ValueError(f"不支持的数据库类型: {self.db_type}")
    
    @property
    def db(self) -> SQLiteOperator:
        """获取数据库操作器"""
        return self._db_operator
    
    def disconnect(self) -> None:
        """断开数据库连接"""
        if self._db_operator:
            self._db_operator.disconnect()
    
    @abstractmethod
    def _get_table_name(self) -> str:
        """
        获取表名
        
        :return: 表名
        """
        pass
    
    @abstractmethod
    def _to_db_dict(self, obj: T) -> Dict[str, Any]:
        """
        将业务对象转换为数据库字典
        
        :param obj: 业务对象
        :return: 数据库字典
        """
        pass
    
    @abstractmethod
    def _from_db_dict(self, data: Dict[str, Any]) -> T:
        """
        将数据库字典转换为业务对象
        
        :param data: 数据库字典
        :return: 业务对象
        """
        pass
    
    def create(self, obj: T) -> bool:
        """
        创建记录
        
        :param obj: 业务对象
        :return: 成功返回True
        """
        try:
            data = self._to_db_dict(obj)
            self.db.insert(self._get_table_name(), data)
            self.logger.info(f"创建记录成功: {self._get_table_name()}")
            return True
        except Exception as e:
            self.logger.error(f"创建记录失败: {e}")
            raise
    
    def create_many(self, objs: List[T]) -> int:
        """
        批量创建记录
        
        :param objs: 业务对象列表
        :return: 创建的记录数
        """
        try:
            data_list = [self._to_db_dict(obj) for obj in objs]
            count = self.db.insert_many(self._get_table_name(), data_list)
            self.logger.info(f"批量创建记录成功: {self._get_table_name()}, 数量={count}")
            return count
        except Exception as e:
            self.logger.error(f"批量创建记录失败: {e}")
            raise
    
    def read(self, id_value: str, id_field: str = None) -> Optional[T]:
        """
        读取单条记录
        
        :param id_value: ID值
        :param id_field: ID字段名，默认使用主键字段
        :return: 业务对象，未找到返回None
        """
        try:
            id_field = id_field or self._get_id_field()
            data = self.db.select_one(self._get_table_name(), where={id_field: id_value})
            if data:
                return self._from_db_dict(data)
            return None
        except Exception as e:
            self.logger.error(f"读取记录失败: {e}")
            raise
    
    def read_all(self, where: Dict[str, Any] = None, 
                 order_by: str = None, limit: int = None) -> List[T]:
        """
        读取多条记录
        
        :param where: 查询条件
        :param order_by: 排序字段
        :param limit: 返回数量限制
        :return: 业务对象列表
        """
        try:
            data_list = self.db.select(
                self._get_table_name(), 
                where=where, 
                order_by=order_by,
                limit=limit
            )
            return [self._from_db_dict(data) for data in data_list]
        except Exception as e:
            self.logger.error(f"读取多条记录失败: {e}")
            raise
    
    def update(self, obj: T, id_value: str = None, id_field: str = None) -> int:
        """
        更新记录
        
        :param obj: 业务对象
        :param id_value: ID值，默认从对象中获取
        :param id_field: ID字段名
        :return: 更新的记录数
        """
        try:
            id_field = id_field or self._get_id_field()
            id_value = id_value or self._get_id_value(obj)
            
            data = self._to_db_dict(obj)
            # 移除ID字段，避免更新主键
            if id_field in data:
                del data[id_field]
            
            count = self.db.update(self._get_table_name(), data, where={id_field: id_value})
            self.logger.info(f"更新记录成功: {self._get_table_name()}, 数量={count}")
            return count
        except Exception as e:
            self.logger.error(f"更新记录失败: {e}")
            raise
    
    def delete(self, id_value: str, id_field: str = None) -> int:
        """
        删除记录
        
        :param id_value: ID值
        :param id_field: ID字段名
        :return: 删除的记录数
        """
        try:
            id_field = id_field or self._get_id_field()
            count = self.db.delete(self._get_table_name(), where={id_field: id_value})
            self.logger.info(f"删除记录成功: {self._get_table_name()}, 数量={count}")
            return count
        except Exception as e:
            self.logger.error(f"删除记录失败: {e}")
            raise
    
    def exists(self, id_value: str, id_field: str = None) -> bool:
        """
        检查记录是否存在
        
        :param id_value: ID值
        :param id_field: ID字段名
        :return: 存在返回True
        """
        id_field = id_field or self._get_id_field()
        return self.db.exists(self._get_table_name(), where={id_field: id_value})
    
    def count(self, where: Dict[str, Any] = None) -> int:
        """
        统计记录数
        
        :param where: 查询条件
        :return: 记录数
        """
        return self.db.count(self._get_table_name(), where=where)
    
    def _get_id_field(self) -> str:
        """
        获取主键字段名
        
        子类可以重写此方法。
        :return: 主键字段名
        """
        return "id"
    
    @abstractmethod
    def _get_id_value(self, obj: T) -> str:
        """
        获取对象的主键值
        
        :param obj: 业务对象
        :return: 主键值
        """
        pass


class DatabaseServiceFactory:
    """
    数据库服务工厂类
    
    用于创建各种业务对象的数据库服务实例。
    配置从 db_config.json 文件读取。
    """
    
    _services = {}
    _db_config = None
    
    @classmethod
    def get_db_config(cls) -> Dict[str, Any]:
        """
        获取数据库配置
        
        :return: 包含 db_type 和 db_config 的字典
        """
        if cls._db_config is None:
            cls._db_config = get_db_config()
        return cls._db_config
    
    @classmethod
    def set_db_config(cls, db_type: str = None, db_config: Dict[str, Any] = None) -> None:
        """
        设置数据库配置
        
        :param db_type: 数据库类型（可选）
        :param db_config: 数据库配置（可选）
        """
        if db_type is None and db_config is None:
            # 从配置文件读取
            cls._db_config = get_db_config()
        else:
            file_config = get_db_config()
            cls._db_config = {
                "db_type": db_type or file_config.get("db_type", "sqlite"),
                "db_config": db_config or file_config.get("db_config", {})
            }
    
    @classmethod
    def get_service(cls, service_class: type) -> SQLDatabaseService:
        """
        获取数据库服务实例
        
        配置从 db_config.json 文件读取。
        
        :param service_class: 服务类
        :return: 服务实例
        """
        if cls._db_config is None:
            cls._db_config = get_db_config()
        
        service_name = service_class.__name__
        if service_name not in cls._services:
            cls._services[service_name] = service_class(
                db_type=cls._db_config.get("db_type"),
                db_config=cls._db_config.get("db_config")
            )
        return cls._services[service_name]
    
    @classmethod
    def close_all(cls) -> None:
        """关闭所有数据库连接"""
        for service in cls._services.values():
            service.disconnect()
        cls._services.clear()


def init_all_tables(db_path: str = "DB/SQLite", db_name: str = "simulation.db") -> SQLiteOperator:
    """
    初始化所有数据表
    
    :param db_path: 数据库路径
    :param db_name: 数据库名称
    :return: SQLiteOperator实例
    """
    return init_database(db_path, db_name)


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 初始化数据库
    operator = init_all_tables()
    print(f"所有表: {operator.get_all_tables()}")
    operator.disconnect()
