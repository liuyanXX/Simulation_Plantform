"""角色模块

定义 Role 类，用于表示业务角色。
"""
from typing import Optional, List, Dict, Any
import json

from pydantic import BaseModel, Field


class Role(BaseModel):
    """
    角色类
    
    表示一个业务角色，定义了该角色在任务执行中的职责和权限。
    
    :param name: 角色名称（唯一标识）
    :param description: 角色描述
    
    示例用法：
        dev_role = Role(
            name="DEV",
            description="开发人员，负责编写项目代码，实现项目功能。"
        )
        
        test_role = Role(
            name="TEST",
            description="测试人员，负责测试项目功能，确保系统质量。"
        )
    """
    name: str = Field(description="角色名称（唯一标识）")
    description: Optional[str] = Field(default=None, description="角色描述")

    def save(self) -> bool:
        """
        保存角色到数据库（新增或更新）
        
        数据库配置从 db_config.json 文件读取。
        
        :return: 保存成功返回True
        """
        from data_storage_services.sql_db_services.role_service import RoleService
        
        service = RoleService()
        try:
            if service.exists(self.name):
                service.update(self)
            else:
                service.create(self)
            return True
        finally:
            service.disconnect()

    def delete(self) -> bool:
        """
        从数据库删除角色
        
        数据库配置从 db_config.json 文件读取。
        
        :return: 删除成功返回True
        """
        from data_storage_services.sql_db_services.role_service import RoleService
        
        service = RoleService()
        try:
            return service.delete(self.name) == 1
        finally:
            service.disconnect()

    @classmethod
    def get_by_name(cls, name: str) -> Optional['Role']:
        """
        按角色名称查询角色
        
        数据库配置从 db_config.json 文件读取。
        
        :param name: 角色名称
        :return: 角色对象，未找到返回None
        """
        from data_storage_services.sql_db_services.role_service import RoleService
        
        service = RoleService()
        try:
            return service.read(name)
        finally:
            service.disconnect()

    @classmethod
    def query(cls, where: Dict[str, Any] = None, order_by: str = None, 
              limit: int = None) -> List['Role']:
        """
        按条件查询角色
        
        数据库配置从 db_config.json 文件读取。
        
        :param where: 查询条件，如 {"name": "DEV"}
        :param order_by: 排序字段
        :param limit: 返回数量限制
        :return: 角色列表
        """
        from data_storage_services.sql_db_services.role_service import RoleService
        
        service = RoleService()
        try:
            return service.read_all(where=where, order_by=order_by, limit=limit)
        finally:
            service.disconnect()

    @classmethod
    def get_all(cls, order_by: str = None, limit: int = None) -> List['Role']:
        """
        全量查询角色
        
        数据库配置从 db_config.json 文件读取。
        
        :param order_by: 排序字段
        :param limit: 返回数量限制
        :return: 角色列表
        """
        from data_storage_services.sql_db_services.role_service import RoleService
        
        service = RoleService()
        try:
            return service.read_all(order_by=order_by, limit=limit)
        finally:
            service.disconnect()

    @classmethod
    def exists(cls, name: str) -> bool:
        """
        检查角色是否存在
        
        数据库配置从 db_config.json 文件读取。
        
        :param name: 角色名称
        :return: 存在返回True
        """
        from data_storage_services.sql_db_services.role_service import RoleService
        
        service = RoleService()
        try:
            return service.exists(name)
        finally:
            service.disconnect()

    @classmethod
    def count(cls, where: Dict[str, Any] = None) -> int:
        """
        统计角色数量
        
        数据库配置从 db_config.json 文件读取。
        
        :param where: 查询条件
        :return: 角色数量
        """
        from data_storage_services.sql_db_services.role_service import RoleService
        
        service = RoleService()
        try:
            return service.count(where=where)
        finally:
            service.disconnect()

    @classmethod
    def get_all_names(cls) -> List[str]:
        """
        获取所有角色名称
        
        数据库配置从 db_config.json 文件读取。
        
        :return: 角色名称列表
        """
        from data_storage_services.sql_db_services.role_service import RoleService
        
        service = RoleService()
        try:
            return service.get_all_names()
        finally:
            service.disconnect()

    def to_json(self) -> str:
        """导出角色为JSON格式"""
        return json.dumps(self.model_dump(mode='json'), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Role':
        """
        从JSON字符串加载角色
        
        :param json_str: JSON格式的字符串
        :return: Role 对象
        """
        data = json.loads(json_str)
        return cls(**data)