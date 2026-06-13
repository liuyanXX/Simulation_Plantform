from pydantic import BaseModel, Field
from typing import List


class Role(BaseModel):
    name: str = Field(description="角色名称")
    description: str = Field(description="角色描述")

    PROJECT_MANAGER = "PM"
    PROJECT_FINANCIAL = "PF"
    PROJECT_PURCHASE = "PP"
    PROJECT_RESEARCH = "PR"
    PROJECT_MANAGER_ASSISTANT = "PMA"
    PROJECT_DEVELOPER = "DEV"
    PROJECT_TESTER = "TEST"
    PROJECT_QA_ENGINEER = "QA"


class RoleRegistry:
    def __init__(self):
        self.roles: List[Role] = []
        self._register_default_roles()

    def _register_default_roles(self):
        self.register(Role(
            name=Role.PROJECT_MANAGER,
            description="项目负责人，负责对项目的全面管理，包括项目计划、资源分配、风险管理和项目执行。"
        ))
        self.register(Role(
            name=Role.PROJECT_FINANCIAL,
            description="项目财务负责人，负责管理项目的财务，包括项目预算、项目成本、项目资金等。"
        ))
        self.register(Role(
            name=Role.PROJECT_PURCHASE,
            description="项目采购负责人，负责采购项目所需的资源和材料。"
        ))
        self.register(Role(
            name=Role.PROJECT_RESEARCH,
            description="项目研究负责人，负责研究项目需求，确定项目技术方向。"
        ))
        self.register(Role(
            name=Role.PROJECT_MANAGER_ASSISTANT,
            description="项目负责人助手，负责协助项目负责人管理项目。"
        ))
        self.register(Role(
            name=Role.PROJECT_DEVELOPER,
            description="开发人员，负责编写项目代码，实现项目功能。"
        ))
        self.register(Role(
            name=Role.PROJECT_TESTER,
            description="测试人员，负责测试项目功能，确保项目质量。"
        ))
        self.register(Role(
            name=Role.PROJECT_QA_ENGINEER,
            description="QA工程师，负责跟踪管理项目质量，对项目质量进行评估和改进。"
        ))

    def register(self, role: Role) -> None:
        self.roles.append(role)

    def get_role(self, name: str) -> Role:
        for role in self.roles:
            if role.name == name:
                return role
        return None

    def get_all_roles(self) -> List[Role]:
        return self.roles

    def get_all_names(self) -> List[str]:
        return [role.name for role in self.roles]

    def remove_role(self, name: str) -> None:
        for role in self.roles:
            if role.name == name:
                self.roles.remove(role)
                break
