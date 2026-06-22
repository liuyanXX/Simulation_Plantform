"""组织服务类

提供组织对象的数据库CRUD操作服务。
"""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from .base_service import SQLDatabaseService
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from bo.organization import Organization


class OrganizationService(SQLDatabaseService[Organization]):
    """
    组织服务类
    
    提供组织对象的数据库CRUD操作服务。
    """
    
    def _get_table_name(self) -> str:
        return "organizations"
    
    def _get_id_field(self) -> str:
        return "org_id"
    
    def _get_id_value(self, obj: Organization) -> str:
        return obj.org_id
    
    def _to_db_dict(self, obj: Organization) -> Dict[str, Any]:
        """将组织对象转换为数据库字典"""
        return {
            "org_id": obj.org_id,
            "name": obj.name,
            "parent_id": obj.parent.org_id if obj.parent else None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    def _from_db_dict(self, data: Dict[str, Any]) -> Organization:
        """将数据库字典转换为组织对象"""
        return Organization(
            org_id=data["org_id"],
            name=data["name"],
            parent=None,  # 父组织需要单独加载
            children=[],  # 子组织需要单独加载
            workers=[]  # 员工需要单独加载
        )
    
    def get_root_organizations(self) -> List[Organization]:
        """
        获取根组织列表
        
        :return: 根组织列表
        """
        return self.read_all(where={"parent_id": None})
    
    def get_children(self, org_id: str) -> List[Organization]:
        """
        获取子组织列表
        
        :param org_id: 组织ID
        :return: 子组织列表
        """
        return self.read_all(where={"parent_id": org_id})
    
    def get_organization_tree(self, org_id: str) -> Dict[str, Any]:
        """
        获取组织树结构
        
        :param org_id: 组织ID
        :return: 组织树字典
        """
        org = self.read(org_id)
        if not org:
            return None
        
        def build_tree(organization: Organization) -> Dict[str, Any]:
            children = self.get_children(organization.org_id)
            return {
                "org_id": organization.org_id,
                "name": organization.name,
                "children": [build_tree(child) for child in children]
            }
        
        return build_tree(org)
    
    def add_worker_to_org(self, org_id: str, employee_id: str) -> bool:
        """
        将员工添加到组织
        
        :param org_id: 组织ID
        :param employee_id: 员工ID
        :return: 成功返回True
        """
        try:
            self.db.insert("org_workers", {
                "org_id": org_id,
                "employee_id": employee_id
            })
            return True
        except Exception as e:
            self.logger.error(f"添加员工到组织失败: {e}")
            return False
    
    def remove_worker_from_org(self, org_id: str, employee_id: str) -> bool:
        """
        从组织移除员工
        
        :param org_id: 组织ID
        :param employee_id: 员工ID
        :return: 成功返回True
        """
        try:
            self.db.delete("org_workers", where={"org_id": org_id, "employee_id": employee_id})
            return True
        except Exception as e:
            self.logger.error(f"从组织移除员工失败: {e}")
            return False
    
    def get_org_workers(self, org_id: str) -> List[str]:
        """
        获取组织的员工ID列表
        
        :param org_id: 组织ID
        :return: 员工ID列表
        """
        results = self.db.select("org_workers", where={"org_id": org_id})
        return [r["employee_id"] for r in results]


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试组织服务
    service = OrganizationService()
    
    # 创建测试组织
    org = Organization(
        org_id="ORG001",
        name="研发部"
    )
    
    # 保存
    service.create(org)
    print(f"创建组织: {org.org_id}")
    
    # 读取
    loaded = service.read("ORG001")
    print(f"读取组织: {loaded}")
    
    # 删除
    service.delete("ORG001")
    print("删除组织成功")
    
    service.disconnect()
