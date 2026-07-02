"""智能员工服务类

提供智能员工对象的数据库CRUD操作服务。
"""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from .base_service import SQLDatabaseService
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from bo.ssys.aiworker import AIWorker


class WorkerService(SQLDatabaseService[AIWorker]):
    """
    智能员工服务类
    
    提供智能员工对象的数据库CRUD操作服务。
    """
    
    def _get_table_name(self) -> str:
        return "ai_workers"
    
    def _get_id_field(self) -> str:
        return "employee_id"
    
    def _get_id_value(self, obj: AIWorker) -> str:
        return obj.employee_id
    
    def _to_db_dict(self, obj: AIWorker) -> Dict[str, Any]:
        """将员工对象转换为数据库字典"""
        return {
            "employee_id": obj.employee_id,
            "name": obj.name,
            "department": obj.department,
            "roles": json.dumps(obj.roles, ensure_ascii=False) if obj.roles else "[]",
            "daily_work_hours": obj.daily_work_hours,
            "org_id": getattr(obj, '_org_id', None),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    def _from_db_dict(self, data: Dict[str, Any]) -> AIWorker:
        """将数据库字典转换为员工对象"""
        def parse_json(value, default=None):
            if value is None:
                return default or []
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except:
                    return value
            return value
        
        return AIWorker(
            employee_id=data["employee_id"],
            name=data["name"],
            department=data["department"],
            roles=parse_json(data.get("roles"), []),
            daily_work_hours=data.get("daily_work_hours", 8.0),
            task_list=[]  # 任务列表需要单独加载
        )
    
    def get_by_department(self, department: str) -> List[AIWorker]:
        """
        按部门查询员工
        
        :param department: 部门名称
        :return: 员工列表
        """
        return self.read_all(where={"department": department})
    
    def get_by_org(self, org_id: str) -> List[AIWorker]:
        """
        按组织查询员工
        
        :param org_id: 组织ID
        :return: 员工列表
        """
        return self.read_all(where={"org_id": org_id})
    
    def get_by_role(self, role: str) -> List[AIWorker]:
        """
        按角色查询员工
        
        :param role: 角色名称
        :return: 员工列表
        """
        all_workers = self.read_all()
        return [w for w in all_workers if role in w.roles]
    
    def assign_task(self, employee_id: str, task_id: str) -> bool:
        """
        为员工分配任务
        
        :param employee_id: 员工ID
        :param task_id: 任务ID
        :return: 成功返回True
        """
        try:
            self.db.insert("worker_tasks", {
                "employee_id": employee_id,
                "task_id": task_id,
                "assigned_at": datetime.now().isoformat(),
                "status": "pending"
            })
            return True
        except Exception as e:
            self.logger.error(f"分配任务失败: {e}")
            return False
    
    def get_worker_tasks(self, employee_id: str) -> List[Dict[str, Any]]:
        """
        获取员工的任务列表
        
        :param employee_id: 员工ID
        :return: 任务ID列表
        """
        results = self.db.select("worker_tasks", where={"employee_id": employee_id})
        return results


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试员工服务
    service = WorkerService()
    
    # 创建测试员工
    worker = AIWorker(
        employee_id="EMP001",
        name="张三",
        department="研发部",
        roles=["DEV", "TEST"],
        daily_work_hours=8.0
    )
    
    # 保存
    service.create(worker)
    print(f"创建员工: {worker.employee_id}")
    
    # 读取
    loaded = service.read("EMP001")
    print(f"读取员工: {loaded}")
    
    # 删除
    service.delete("EMP001")
    print("删除员工成功")
    
    service.disconnect()
