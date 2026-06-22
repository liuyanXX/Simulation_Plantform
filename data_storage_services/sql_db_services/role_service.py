"""角色服务类

提供角色对象的数据库CRUD操作服务。
"""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from .base_service import SQLDatabaseService
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from bo.role import Role


class RoleService(SQLDatabaseService[Role]):
    """
    角色服务类
    
    提供角色对象的数据库CRUD操作服务。
    """
    
    def _get_table_name(self) -> str:
        return "roles"
    
    def _get_id_field(self) -> str:
        return "name"
    
    def _get_id_value(self, obj: Role) -> str:
        return obj.name
    
    def _to_db_dict(self, obj: Role) -> Dict[str, Any]:
        """将角色对象转换为数据库字典"""
        return {
            "name": obj.name,
            "description": obj.description,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    def _from_db_dict(self, data: Dict[str, Any]) -> Role:
        """将数据库字典转换为角色对象"""
        return Role(
            name=data["name"],
            description=data["description"]
        )
    
    def get_all_names(self) -> List[str]:
        """
        获取所有角色名称
        
        :return: 角色名称列表
        """
        roles = self.read_all()
        return [r.name for r in roles]


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试角色服务
    service = RoleService()
    
    # 创建测试角色
    role = Role(
        name="DEV",
        description="开发人员，负责编写项目代码，实现项目功能。"
    )
    
    # 保存
    service.create(role)
    print(f"创建角色: {role.name}")
    
    # 读取
    loaded = service.read("DEV")
    print(f"读取角色: {loaded}")
    
    # 删除
    service.delete("DEV")
    print("删除角色成功")
    
    service.disconnect()
