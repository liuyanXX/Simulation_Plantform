from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from .ai_worker import AIWorker
from .task import Task


class Organization(BaseModel):
    org_id: str = Field(description="组织唯一标识")
    name: str = Field(description="组织名称")
    parent: Optional['Organization'] = Field(default=None, description="父组织")
    children: List['Organization'] = Field(default_factory=list, description="子组织列表")
    workers: List[AIWorker] = Field(default_factory=list, description="组织内的员工列表")

    def add_child(self, child: 'Organization') -> None:
        """添加子组织"""
        if child not in self.children:
            child.parent = self
            self.children.append(child)

    def remove_child(self, child: 'Organization') -> None:
        """移除子组织"""
        if child in self.children:
            child.parent = None
            self.children.remove(child)

    def add_worker(self, worker: AIWorker) -> None:
        """添加员工到组织"""
        if worker not in self.workers:
            self.workers.append(worker)

    def remove_worker(self, worker: AIWorker) -> None:
        """从组织中移除员工"""
        if worker in self.workers:
            self.workers.remove(worker)

    def get_all_workers(self) -> List[AIWorker]:
        """获取组织及其所有子组织的所有员工"""
        all_workers = []
        stack = [self]
        
        while stack:
            current = stack.pop()
            all_workers.extend(current.workers)
            stack.extend(reversed(current.children))
        
        return all_workers

    def get_worker_by_id(self, employee_id: str) -> Optional[AIWorker]:
        """根据员工工号查找员工"""
        stack = [self]
        
        while stack:
            current = stack.pop()
            for worker in current.workers:
                if worker.employee_id == employee_id:
                    return worker
            stack.extend(reversed(current.children))
        
        return None

    def get_organization_by_id(self, org_id: str) -> Optional['Organization']:
        """根据组织ID查找组织"""
        stack = [self]
        
        while stack:
            current = stack.pop()
            if current.org_id == org_id:
                return current
            stack.extend(reversed(current.children))
        
        return None

    def get_depth(self) -> int:
        """获取组织树的深度"""
        if not self.children:
            return 1
        return 1 + max(child.get_depth() for child in self.children)

    def get_total_org_count(self) -> int:
        """获取组织总数（包括自身和所有子组织）"""
        count = 1
        for child in self.children:
            count += child.get_total_org_count()
        return count

    def get_total_worker_count(self) -> int:
        """获取员工总数（包括自身和所有子组织）"""
        return len(self.get_all_workers())

    def assign_task_to_worker(self, employee_id: str, task: Task) -> bool:
        """给指定员工分配任务"""
        worker = self.get_worker_by_id(employee_id)
        if worker:
            worker.add_task(task)
            return True
        return False

    def find_workers_by_role(self, role: str) -> List[AIWorker]:
        """查找具备指定角色的所有员工"""
        all_workers = self.get_all_workers()
        return [worker for worker in all_workers if role in worker.roles]

    def to_dict(self, include_workers: bool = True) -> Dict[str, Any]:
        """将组织树转换为字典结构"""
        result = {
            "org_id": self.org_id,
            "name": self.name,
            "children": [child.to_dict(include_workers) for child in self.children]
        }
        
        if include_workers:
            result["workers"] = [
                {
                    "employee_id": w.employee_id,
                    "name": w.name,
                    "department": w.department,
                    "roles": w.roles,
                    "task_count": len(w.task_list)
                } for w in self.workers
            ]
        
        return result

    def __str__(self, indent: int = 0) -> str:
        """以树形结构打印组织"""
        prefix = "  " * indent
        result = f"{prefix}{self.org_id}: {self.name} ({len(self.workers)} workers)"
        
        for child in self.children:
            result += "\n" + child.__str__(indent + 1)
        
        return result


class OrganizationFactory:
    """组织工厂类，用于创建和初始化组织架构"""
    
    @staticmethod
    def create_organization_from_config(config: Dict[str, Any]) -> Organization:
        """
        根据配置创建组织架构
        
        配置格式示例:
        {
            "org_id": "root",
            "name": "总公司",
            "children": [
                {
                    "org_id": "dept1",
                    "name": "研发部",
                    "workers": [
                        {
                            "employee_id": "EMP001",
                            "name": "张三",
                            "department": "研发部",
                            "roles": ["DEV", "TEST"],
                            "daily_work_hours": 8.0
                        }
                    ],
                    "children": []
                }
            ],
            "workers": []
        }
        """
        org_id = config["org_id"]
        name = config["name"]
        
        org = Organization(org_id=org_id, name=name)
        
        for worker_config in config.get("workers", []):
            worker = AIWorker(**worker_config)
            org.add_worker(worker)
        
        for child_config in config.get("children", []):
            child_org = OrganizationFactory.create_organization_from_config(child_config)
            org.add_child(child_org)
        
        return org

    @staticmethod
    def create_hierarchical_org(
        levels: int,
        branches_per_level: int,
        workers_per_org: int,
        base_org_name: str = "组织",
        base_worker_name: str = "员工"
    ) -> Organization:
        """
        创建层级化的组织架构
        
        :param levels: 组织层级数
        :param branches_per_level: 每层的分支数
        :param workers_per_org: 每个组织的员工数
        :param base_org_name: 组织基础名称
        :param base_worker_name: 员工基础名称
        """
        org_counter = 1
        worker_counter = 1
        
        def create_level(org_id_prefix: str, level: int, parent_name: str) -> Organization:
            nonlocal org_counter, worker_counter
            
            org_id = f"{org_id_prefix}-{level}-{org_counter}"
            org_name = f"{parent_name}/{base_org_name}{org_counter}"
            org_counter += 1
            
            org = Organization(org_id=org_id, name=org_name)
            
            for i in range(workers_per_org):
                worker = AIWorker(
                    employee_id=f"EMP{str(worker_counter).zfill(4)}",
                    name=f"{base_worker_name}{worker_counter}",
                    department=org_name,
                    roles=["DEV", "TEST"] if level == levels else ["MANAGER", "COORDINATOR"],
                    daily_work_hours=8.0
                )
                org.add_worker(worker)
                worker_counter += 1
            
            if level < levels:
                for _ in range(branches_per_level):
                    child_org = create_level(org_id_prefix, level + 1, org_name)
                    org.add_child(child_org)
            
            return org
        
        root = Organization(org_id="ROOT", name="根组织")
        for _ in range(branches_per_level):
            child_org = create_level("ORG", 1, "根组织")
            root.add_child(child_org)
        
        return root


if __name__ == "__main__":
    print("=== 创建简单组织架构 ===")
    config = {
        "org_id": "ROOT",
        "name": "总公司",
        "workers": [],
        "children": [
            {
                "org_id": "RD",
                "name": "研发部",
                "workers": [
                    {
                        "employee_id": "EMP001",
                        "name": "张三",
                        "department": "研发部",
                        "roles": ["DEV", "TEST"],
                        "daily_work_hours": 8.0
                    },
                    {
                        "employee_id": "EMP002",
                        "name": "李四",
                        "department": "研发部",
                        "roles": ["DEV"],
                        "daily_work_hours": 8.0
                    }
                ],
                "children": [
                    {
                        "org_id": "RD-FE",
                        "name": "前端开发组",
                        "workers": [
                            {
                                "employee_id": "EMP003",
                                "name": "王五",
                                "department": "前端开发组",
                                "roles": ["DEV"],
                                "daily_work_hours": 8.0
                            }
                        ],
                        "children": []
                    }
                ]
            },
            {
                "org_id": "QA",
                "name": "测试部",
                "workers": [
                    {
                        "employee_id": "EMP004",
                        "name": "赵六",
                        "department": "测试部",
                        "roles": ["TEST", "QA"],
                        "daily_work_hours": 8.0
                    }
                ],
                "children": []
            }
        ]
    }
    
    org = OrganizationFactory.create_organization_from_config(config)
    print("组织架构:")
    print(org)
    
    print(f"\n组织总数: {org.get_total_org_count()}")
    print(f"员工总数: {org.get_total_worker_count()}")
    print(f"组织深度: {org.get_depth()}")
    
    print("\n=== 查找员工 ===")
    worker = org.get_worker_by_id("EMP001")
    if worker:
        print(f"找到员工: {worker.name}")
    
    print("\n=== 查找具备DEV角色的员工 ===")
    dev_workers = org.find_workers_by_role("DEV")
    for w in dev_workers:
        print(f"- {w.name} ({w.employee_id})")
    
    print("\n=== 组织字典结构 ===")
    import json
    print(json.dumps(org.to_dict(), ensure_ascii=False, indent=2))
    
    print("\n=== 创建层级化组织架构 ===")
    hierarchical_org = OrganizationFactory.create_hierarchical_org(
        levels=3,
        branches_per_level=2,
        workers_per_org=2
    )
    print(hierarchical_org)
    print(f"\n层级化组织 - 组织总数: {hierarchical_org.get_total_org_count()}")
    print(f"层级化组织 - 员工总数: {hierarchical_org.get_total_worker_count()}")
    print(f"层级化组织 - 组织深度: {hierarchical_org.get_depth()}")
