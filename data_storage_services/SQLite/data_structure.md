# 数据结构清单

本文档描述仿真平台数据库中所有业务表的结构及其关联关系。

## 数据库概述

- **数据库类型**: SQLite
- **存储位置**: `DB/SQLite/simulation.db`
- **字符编码**: UTF-8

---

## 一、业务表结构

### 1. 方案表 (solutions)

存储方案对象的完整信息。

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|----------|------|------|
| solution_id | TEXT | PRIMARY KEY | 方案唯一标识 |
| name | TEXT | NOT NULL | 方案名称 |
| version | TEXT | NOT NULL DEFAULT '1.0' | 版本号 |
| status | TEXT | NOT NULL DEFAULT 'draft' | 方案状态（draft/review/approved/active/suspended/completed/archived） |
| priority | TEXT | NOT NULL DEFAULT 'medium' | 优先级（low/medium/high/critical） |
| purpose | TEXT | - | 方案目的 |
| objectives | TEXT | - | 方案目标列表（JSON格式） |
| initiatives | TEXT | - | 方案举措列表（JSON格式） |
| working_mechanism | TEXT | - | 工作机制描述 |
| organization | TEXT | - | 涉及组织列表（JSON格式） |
| personnel | TEXT | - | 涉及人员列表（JSON格式） |
| roles | TEXT | - | 涉及角色列表（JSON格式） |
| work_content | TEXT | - | 工作内容描述 |
| constraints | TEXT | - | 限制条件列表（JSON格式） |
| risks | TEXT | - | 风险列表（JSON格式） |
| issues | TEXT | - | 问题列表（JSON格式） |
| other_notes | TEXT | - | 其他说明 |
| main_document_id | TEXT | - | 主文档ID（外键关联solution_documents） |
| auxiliary_document_ids | TEXT | - | 辅助文档ID列表（JSON格式） |
| description | TEXT | - | 方案描述 |
| owner | TEXT | - | 方案负责人 |
| created_by | TEXT | - | 创建人 |
| created_at | TEXT | NOT NULL | 创建时间（ISO格式） |
| updated_at | TEXT | NOT NULL | 更新时间（ISO格式） |
| effective_date | TEXT | - | 生效日期（ISO格式） |
| expiry_date | TEXT | - | 到期日期（ISO格式） |
| tags | TEXT | - | 标签列表（JSON格式） |
| metadata | TEXT | - | 元数据（JSON格式） |

**索引**:
- `idx_solutions_status`: status
- `idx_solutions_owner`: owner
- `idx_solutions_created_at`: created_at

---

### 2. 方案文档表 (solution_documents)

存储方案关联的文档信息。

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|----------|------|------|
| document_id | TEXT | PRIMARY KEY | 文档唯一标识 |
| file_name | TEXT | NOT NULL | 文件名 |
| version | TEXT | NOT NULL | 版本号 |
| document_type | TEXT | NOT NULL DEFAULT 'attachment' | 文档类型（main/attachment/reference） |
| file_content | BLOB | - | 文件二进制内容 |
| text_content | TEXT | - | 纯文本内容 |
| description | TEXT | - | 文档描述 |
| format | TEXT | - | 文件格式 |
| size | INTEGER | - | 文件大小（字节） |
| created_by | TEXT | - | 创建人 |
| created_at | TEXT | NOT NULL | 创建时间 |
| updated_at | TEXT | NOT NULL | 更新时间 |
| related_solution_ids | TEXT | - | 关联方案ID列表（JSON格式） |
| metadata | TEXT | - | 元数据（JSON格式） |

**关联关系**:
- `main_document_id` → `solution_documents.document_id` (方案主文档)
- `auxiliary_document_ids` → `solution_documents.document_id` (方案辅助文档)

---

### 3. 任务表 (tasks)

存储任务对象信息，支持普通任务、开始任务、结束任务和中断任务。

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|----------|------|------|
| task_id | TEXT | PRIMARY KEY | 任务唯一标识 |
| task_name | TEXT | NOT NULL | 任务名称 |
| task_type | TEXT | NOT NULL DEFAULT 'normal' | 任务类型（normal/start/end/halt） |
| expected_start_time | TEXT | NOT NULL | 期望开始时间 |
| expected_end_time | TEXT | NOT NULL | 期望结束时间 |
| scheduled_start_time | TEXT | - | 排期开始时间 |
| scheduled_end_time | TEXT | - | 排期结束时间 |
| actual_start_time | TEXT | - | 实际开始时间 |
| actual_end_time | TEXT | - | 实际结束时间 |
| content | TEXT | NOT NULL | 工作内容 |
| execute_role | TEXT | NOT NULL | 执行角色 |
| resource_consumption | REAL | NOT NULL | 资源消耗（工时） |
| priority | TEXT | NOT NULL DEFAULT 'medium' | 优先级（low/medium/high） |
| output_target_role | TEXT | - | 输出目标角色 |
| next_task_info | TEXT | - | 下一步任务信息（JSON格式） |
| is_completed | INTEGER | NOT NULL DEFAULT 0 | 是否完成（0/1） |
| task_source | TEXT | - | 任务来源（上一任务ID） |
| task_destinations | TEXT | - | 任务去向列表（JSON格式） |
| flow_group_id | TEXT | - | 所属任务流组ID（外键） |
| graph_id | TEXT | - | 所属任务图谱ID（外键） |
| manifest_id | TEXT | - | 所属任务清单ID（外键） |

**索引**:
- `idx_tasks_flow_group_id`: flow_group_id
- `idx_tasks_graph_id`: graph_id
- `idx_tasks_manifest_id`: manifest_id
- `idx_tasks_execute_role`: execute_role
- `idx_tasks_is_completed`: is_completed

---

### 4. 智能员工表 (ai_workers)

存储智能员工信息。

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|----------|------|------|
| employee_id | TEXT | PRIMARY KEY | 员工工号 |
| name | TEXT | NOT NULL | 员工姓名 |
| department | TEXT | NOT NULL | 所属部门 |
| roles | TEXT | NOT NULL | 角色列表（JSON格式） |
| daily_work_hours | REAL | NOT NULL DEFAULT 8.0 | 每日工作时长 |
| org_id | TEXT | - | 所属组织ID（外键） |
| created_at | TEXT | NOT NULL | 创建时间 |
| updated_at | TEXT | NOT NULL | 更新时间 |

**关联关系**:
- `org_id` → `organizations.org_id` (所属组织)

---

### 5. 组织表 (organizations)

存储组织架构信息。

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|----------|------|------|
| org_id | TEXT | PRIMARY KEY | 组织唯一标识 |
| name | TEXT | NOT NULL | 组织名称 |
| parent_id | TEXT | - | 父组织ID（外键，自关联） |
| created_at | TEXT | NOT NULL | 创建时间 |
| updated_at | TEXT | NOT NULL | 更新时间 |

**关联关系**:
- `parent_id` → `organizations.org_id` (父组织，支持树形结构)

---

### 6. 角色表 (roles)

存储角色定义信息。

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|----------|------|------|
| name | TEXT | PRIMARY KEY | 角色名称 |
| description | TEXT | NOT NULL | 角色描述 |
| created_at | TEXT | NOT NULL | 创建时间 |
| updated_at | TEXT | NOT NULL | 更新时间 |

**预置角色**:
- PM: 项目负责人
- PF: 项目财务负责人
- PP: 项目采购负责人
- PR: 项目研究负责人
- PMA: 项目负责人助手
- DEV: 开发人员
- TEST: 测试人员
- QA: QA工程师

---

### 7. 任务流组表 (task_flow_groups)

存储任务流组信息。

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|----------|------|------|
| flow_id | TEXT | PRIMARY KEY | 任务流组唯一标识 |
| flow_name | TEXT | NOT NULL | 任务流组名称 |
| description | TEXT | - | 描述 |
| manifest_id | TEXT | - | 所属任务清单ID（外键） |
| created_at | TEXT | NOT NULL | 创建时间 |
| updated_at | TEXT | NOT NULL | 更新时间 |

**关联关系**:
- `manifest_id` → `task_manifests.manifest_id` (所属任务清单)

---

### 8. 任务图谱表 (tasks_graphs)

存储任务图谱信息。

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|----------|------|------|
| graph_id | TEXT | PRIMARY KEY | 图谱唯一标识 |
| graph_name | TEXT | NOT NULL | 图谱名称 |
| description | TEXT | - | 描述 |
| manifest_id | TEXT | - | 所属任务清单ID（外键） |
| created_at | TEXT | NOT NULL | 创建时间 |
| updated_at | TEXT | NOT NULL | 更新时间 |

**关联关系**:
- `manifest_id` → `task_manifests.manifest_id` (所属任务清单)

---

### 9. 任务清单表 (task_manifests)

存储任务清单信息。

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|----------|------|------|
| manifest_id | TEXT | PRIMARY KEY | 清单唯一标识 |
| manifest_name | TEXT | NOT NULL | 清单名称 |
| description | TEXT | - | 描述 |
| solution_id | TEXT | - | 所属方案ID（外键） |
| status | TEXT | NOT NULL DEFAULT 'draft' | 状态（draft/active/completed/archived） |
| created_at | TEXT | NOT NULL | 创建时间 |
| updated_at | TEXT | NOT NULL | 更新时间 |

**关联关系**:
- `solution_id` → `solutions.solution_id` (所属方案)

---

### 10. 评价指标表 (evaluation_indices)

存储评价指标信息。

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|----------|------|------|
| index_id | TEXT | PRIMARY KEY | 指标唯一标识 |
| name | TEXT | NOT NULL | 指标名称 |
| description | TEXT | NOT NULL | 指标说明 |
| evaluation_method | TEXT | NOT NULL | 评价方法 |
| agent_ids | TEXT | NOT NULL | 评价Agent ID列表（JSON格式） |
| index_type | TEXT | NOT NULL | 指标类型（completeness/rationality/feasibility/risk/efficiency/compliance/strategy/resource/benefit/other） |
| index_level | TEXT | NOT NULL | 指标层级（level_1/level_2/level_3/level_4） |
| parent_id | TEXT | - | 父指标ID（外键，自关联） |
| weight | REAL | NOT NULL DEFAULT 1.0 | 权重 |
| score_range | TEXT | NOT NULL DEFAULT '(0, 100)' | 评分范围 |
| created_at | TEXT | NOT NULL | 创建时间 |
| updated_at | TEXT | NOT NULL | 更新时间 |
| is_active | INTEGER | NOT NULL DEFAULT 1 | 是否启用（0/1） |

**关联关系**:
- `parent_id` → `evaluation_indices.index_id` (父指标，支持树形结构)

---

### 11. 知识表 (knowledge)

存储知识信息。

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|----------|------|------|
| knowledge_id | TEXT | PRIMARY KEY | 知识唯一标识 |
| title | TEXT | NOT NULL | 知识标题 |
| summary | TEXT | NOT NULL | 知识摘要 |
| content | TEXT | NOT NULL | 知识内容 |
| index_ids | TEXT | - | 关联指标ID列表（JSON格式） |
| tags | TEXT | - | 标签列表（JSON格式） |
| category | TEXT | NOT NULL DEFAULT 'evaluation' | 知识分类 |
| created_at | TEXT | NOT NULL | 创建时间 |
| updated_at | TEXT | NOT NULL | 更新时间 |
| is_active | INTEGER | NOT NULL DEFAULT 1 | 是否启用（0/1） |

---

### 12. 员工-任务关联表 (worker_tasks)

存储员工与任务的关联关系。

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|----------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 自增主键 |
| employee_id | TEXT | NOT NULL | 员工ID（外键） |
| task_id | TEXT | NOT NULL | 任务ID（外键） |
| assigned_at | TEXT | NOT NULL | 分配时间 |
| status | TEXT | NOT NULL DEFAULT 'pending' | 状态（pending/in_progress/completed） |

**关联关系**:
- `employee_id` → `ai_workers.employee_id` (员工)
- `task_id` → `tasks.task_id` (任务)

---

### 13. 组织-员工关联表 (org_workers)

存储组织与员工的关联关系。

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|----------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 自增主键 |
| org_id | TEXT | NOT NULL | 组织ID（外键） |
| employee_id | TEXT | NOT NULL | 员工ID（外键） |

**关联关系**:
- `org_id` → `organizations.org_id` (组织)
- `employee_id` → `ai_workers.employee_id` (员工)

---

## 二、表关系图

```
┌─────────────────┐       ┌─────────────────────┐
│   solutions     │       │ solution_documents  │
├─────────────────┤       ├─────────────────────┤
│ PK: solution_id │◄──────│ PK: document_id     │
│ FK: main_doc_id │       │                     │
└────────┬────────┘       └─────────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐       ┌─────────────────────┐
│ task_manifests  │       │   task_flow_groups  │
├─────────────────┤       ├─────────────────────┤
│ PK: manifest_id │◄──────│ PK: flow_id         │
│ FK: solution_id │       │ FK: manifest_id     │
└────────┬────────┘       └─────────┬───────────┘
         │                          │
         │                          │ 1:N
         │                          ▼
         │                 ┌─────────────────────┐
         │                 │       tasks         │
         │                 ├─────────────────────┤
         │                 │ PK: task_id         │
         └────────────────►│ FK: flow_group_id   │
                           │ FK: graph_id        │
                           │ FK: manifest_id     │
                           └─────────────────────┘

┌─────────────────┐       ┌─────────────────────┐
│ organizations   │       │     ai_workers      │
├─────────────────┤       ├─────────────────────┤
│ PK: org_id      │◄──────│ PK: employee_id     │
│ FK: parent_id   │       │ FK: org_id          │
└─────────────────┘       └─────────────────────┘

┌─────────────────┐       ┌─────────────────────┐
│evaluation_indices│      │     knowledge       │
├─────────────────┤       ├─────────────────────┤
│ PK: index_id    │       │ PK: knowledge_id    │
│ FK: parent_id   │       │                     │
└─────────────────┘       └─────────────────────┘
```

---

## 三、数据存储模块架构

### 模块结构

```
data_storage_services/
├── __init__.py                      # 模块入口
├── sql_db_services/                 # 关系数据库存储服务子模块
│   ├── __init__.py
│   ├── base_service.py              # 基础服务类
│   ├── solution_service.py          # 方案服务
│   ├── task_service.py              # 任务服务
│   ├── worker_service.py            # 员工服务
│   ├── organization_service.py      # 组织服务
│   ├── role_service.py              # 角色服务
│   ├── task_flow_group_service.py   # 任务流组服务
│   ├── tasks_graph_service.py       # 任务图谱服务
│   ├── task_manifest_service.py     # 任务清单服务
│   ├── evaluation_index_service.py  # 评价指标服务
│   └── knowledge_service.py         # 知识服务
└── SQLite/                          # SQLite操作子模块
    ├── __init__.py
    ├── sqlite_operator.py           # SQLite操作类
    └── data_structure.md            # 本文档
```

### 设计原则

1. **面向对象设计**: 使用Pydantic模型定义业务对象，确保类型安全
2. **微服务设计**: 每个服务类独立负责一个业务对象的CRUD操作
3. **松耦合设计**: 通过抽象基类屏蔽底层数据库实现细节
4. **可扩展性**: 支持扩展其他关系数据库（MySQL、PostgreSQL等）

---

## 四、使用示例

### 初始化数据库

```python
from data_storage_services.SQLite.sqlite_operator import init_database

# 初始化数据库，创建所有表
operator = init_database(db_path="DB/SQLite", db_name="simulation.db")
```

### 使用服务类

```python
from data_storage_services import SolutionService
from bo.solution import Solution, SolutionStatus, SolutionPriority

# 创建服务实例
service = SolutionService()

# 创建方案
solution = Solution(
    solution_id="SOL001",
    name="数字化转型方案",
    version="1.0",
    status=SolutionStatus.DRAFT,
    priority=SolutionPriority.HIGH
)
service.create(solution)

# 查询方案
loaded = service.read("SOL001")

# 更新方案
solution.status = SolutionStatus.ACTIVE
service.update(solution)

# 删除方案
service.delete("SOL001")

# 断开连接
service.disconnect()
```

---

## 五、版本历史

| 10.0 | 2026-06-28 | 新增系统空间组织对象表 ssys_organization，完整 CRUD + 树查询 |

---

## 七、系统空间 · 组织对象 (ssys_organization)

> 业务对象：`bo.ssys.organization.Organization`
> 持久化服务：`data_storage_services.sql_db_services.ssys.organization_service.SsysOrganizationService`
> 数据库表：`ssys_organization`

### 7.1 Pydantic 对象结构

| 属性 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | int? | unique, autoincrement | 组织主键ID(数字唯一) |
| org_code | str | NOT NULL, unique, 1~64 | 组织编码(业务唯一, 如 "RD_CENTER") |
| org_name | str | NOT NULL, 1~128 | 组织名称 |
| org_type | str | DEFAULT "ORG", ≤32 | 类型: COMPANY / DEPARTMENT / TEAM / GROUP / ORG |
| description | str? | - | 说明 |
| parent_id | int? | FK 自关联 | 父组织ID(顶级为 NULL) |
| parent_name | str? | 冗余显示 | 父组织名称 |
| sort_order | int | DEFAULT 0 | 同级排序序号 |
| status | str | DEFAULT "active" | active / disabled / archived |
| extra_info | dict? | JSON | 扩展字段 |
| created_at | str? | ISO | 创建时间 |
| updated_at | str? | ISO | 更新时间 |

### 7.2 数据表 (ssys_organization)

```sql
CREATE TABLE IF NOT EXISTS ssys_organization (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    org_code     TEXT NOT NULL UNIQUE,
    org_name     TEXT NOT NULL,
    org_type     TEXT NOT NULL DEFAULT 'ORG',
    description  TEXT,
    parent_id    INTEGER,
    parent_name  TEXT,
    sort_order   INTEGER NOT NULL DEFAULT 0,
    status       TEXT NOT NULL DEFAULT 'active',
    extra_info   TEXT,                    -- JSON 序列化存储
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES ssys_organization(id) ON DELETE SET NULL
);
```

索引：
- `idx_ssys_organization_code`  UNIQUE  (org_code)
- `idx_ssys_organization_parent`          (parent_id)
- `idx_ssys_organization_type`            (org_type)

### 7.3 服务方法一览 (SsysOrganizationService)

| 方法 | 说明 |
|------|------|
| add(Organization) | 增加组织，自动填 parent_name / 时间戳 |
| delete(org_id, cascade=False) | 删除组织；cascade=True 递归删除下级 |
| update(org_id, **fields) | 变更属性(org_code/org_name/org_type/description/parent_id/sort_order/status/extra_info) |
| move(org_id, new_parent_id) | 调整父子关系 |
| get_by_id(org_id) | 按ID查本身 |
| get_by_code(org_code) | 按组织编码查本身 |
| search_by_name(keyword) | 按名称/编码模糊 |
| list_all(parent_id, org_type, status, ...) | 条件查全量 |
| list_roots() | 顶级(parent_id IS NULL) |
| list_children(parent_id) | 直接下级 |
| get_parent(org_id) | 直接上级 |
| list_ancestors(org_id) | 祖先链(不含自身) |
| count(...) | 统计 |
| exists(org_id) / exists_by_code(org_code) | 存在性 |

### 7.4 使用示例

```python
from bo.ssys.organization import Organization
from data_storage_services.sql_db_services.ssys.organization_service import SsysOrganizationService

with SsysOrganizationService() as svc:
    root = svc.add(Organization(org_code="ROOT", org_name="仿真平台总公司", org_type="COMPANY"))
    rd = svc.add(Organization(org_code="RD", org_name="仿真研发部", org_type="DEPARTMENT", parent_id=root.id))
    svc.add(Organization(org_code="RD_FE", org_name="前端组", org_type="TEAM", parent_id=rd.id))

    print(svc.list_roots())
    print(svc.list_children(rd.id))
    print(svc.search_by_name("研发"))
    print(svc.get_parent(rd.id))
    print(svc.list_ancestors(rd.id))

    svc.update(rd.id, description="负责仿真引擎和前端")
    svc.delete(rd.id, cascade=False)   # 下级存在会拒绝
    svc.delete(rd.id, cascade=True)   # 连带下级一起删
```


---

## 六、附录

### JSON字段说明

以下字段以JSON格式存储复杂数据：

| 表名 | 字段名 | JSON结构说明 |
|------|--------|--------------|
| solutions | objectives | `["目标1", "目标2", ...]` |
| solutions | initiatives | `["举措1", "举措2", ...]` |
| solutions | organization | `["组织1", "组织2", ...]` |
| solutions | personnel | `["人员1", "人员2", ...]` |
| solutions | roles | `["角色1", "角色2", ...]` |
| solutions | constraints | `["约束1", "约束2", ...]` |
| solutions | risks | `["风险1", "风险2", ...]` |
| solutions | issues | `["问题1", "问题2", ...]` |
| solutions | auxiliary_document_ids | `["DOC001", "DOC002", ...]` |
| solutions | tags | `["标签1", "标签2", ...]` |
| tasks | task_destinations | `["TASK001", "TASK002", ...]` |
| tasks | next_task_info | `{task对象属性}` |
| ai_workers | roles | `["DEV", "TEST", ...]` |
| evaluation_indices | agent_ids | `["AGENT001", "AGENT002", ...]` |
| knowledge | index_ids | `["IDX001", "IDX002", ...]` |
| knowledge | tags | `["标签1", "标签2", ...]` |
## 方案元空间 · Organization

方案元空间组织对象 = 系统空间组织对象的完整结构复制 +
扩展 solution_id / solution_version 两个属性,
用于唯一标识当前组织对象所属的方案对象。

数据库表: smeta_organization

业务对象: o/smeta/organization.py (Pydantic)
- Organization          — 持久化对象, 字段包括 id, solution_id, solution_version, org_code, org_name, org_type, description, parent_id, parent_name, sort_order, status, extra_info(TEXT), created_at, updated_at
- OrganizationTreeNode  — 运行时树节点, children 递归自引用

服务类: data_storage_services/sql_db_services/smeta/organization_service.py
类名:   SmetaOrganizationService
模块:
  from data_storage_services.sql_db_services.smeta.organization_service import SmetaOrganizationService
  from data_storage_services.sql_db_services import SmetaOrganizationService
  from data_storage_services import SmetaOrganizationService

表结构:

`sql
CREATE TABLE smeta_organization (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    solution_id TEXT NOT NULL,
    solution_version TEXT NOT NULL,
    org_code TEXT NOT NULL,
    org_name TEXT NOT NULL,
    org_type TEXT NOT NULL DEFAULT 'ORG',
    description TEXT,
    parent_id INTEGER,
    parent_name TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    extra_info TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES smeta_organization(id) ON DELETE SET NULL
);

CREATE INDEX idx_smeta_organization_parent ON smeta_organization(parent_id);
CREATE INDEX idx_smeta_organization_type ON smeta_organization(org_type);
CREATE INDEX idx_smeta_organization_sol ON smeta_organization(solution_id, solution_version);
CREATE UNIQUE INDEX idx_smeta_organization_code_sol ON smeta_organization(solution_id, solution_version, org_code);
`

服务方法:

| 方法 | 说明 |
| --- | --- |
| add / get_by_id / get_by_code / update / delete | 方案内单条 CRUD |
| list_roots / list_children / list_all | 列表查询(自动限定 (solution_id, solution_version)) |
| list_ancestors / get_parent / search_by_name | 辅助查询 |
| count(...) | 条件计数(默认统计根节点) |
| build_organization_tree(root_id) | 以给定节点为根, 递归 fetch DESC, 返回 OrganizationTreeNode |
| build_full_tree(solution_id, solution_version) | 当前方案内全部根节点组成的列表 |
| build_tree_as_dict / build_tree_as_json | 树序列化 |
| batch_add / import_from_json / export_to_json | 批量/JSON |
| **load_from_ssys(root_id, solution_id, solution_version, overwrite)** | **新增**: 从系统空间整棵子树递归复制, 所有节点统一设置方案属性 |

默认 db_path = DB/SQLite, 与 SQLiteOperator 共用根目录。

### (smeta_organization 与 ssys_organization 字段对照表)

| 字段 | ssys | smeta |
| --- | --- | --- |
| solution_id | — | ✓ NOT NULL |
| solution_version | — | ✓ NOT NULL |
| org_code / org_name / org_type / description / parent_id / parent_name / sort_order / status / extra_info / created_at / updated_at | ✓ | ✓ |
| UNIQUE 键 | org_code | (solution_id, solution_version, org_code) |
## 仿真虚空间 · Organization

仿真虚空间组织对象 = 系统空间组织对象的完整结构复制 +
扩展 task_id(仿真任务ID) / batch_no(仿真任务批次号) 两个属性,
用于唯一标识当前组织对象所属的仿真任务。

数据库表: senv_organization

业务对象: o/senv/organization.py (Pydantic)
- Organization          — 持久化对象, 字段: id, task_id, batch_no, org_code, org_name, org_type, description, parent_id, parent_name, sort_order, status, extra_info(TEXT), created_at, updated_at
- OrganizationTreeNode  — 运行时树节点, children 递归自引用, extra_info 自动解析为 Dict

服务类: data_storage_services/sql_db_services/senv/organization_service.py
类名:   SenvOrganizationService
模块:
  from data_storage_services.sql_db_services.senv.organization_service import SenvOrganizationService
  from data_storage_services.sql_db_services import SenvOrganizationService
  from data_storage_services import SenvOrganizationService

表结构:

`sql
CREATE TABLE senv_organization (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    batch_no TEXT NOT NULL,
    org_code TEXT NOT NULL,
    org_name TEXT NOT NULL,
    org_type TEXT NOT NULL DEFAULT 'ORG',
    description TEXT,
    parent_id INTEGER,
    parent_name TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    extra_info TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES senv_organization(id) ON DELETE SET NULL
);

CREATE INDEX idx_senv_organization_parent ON senv_organization(parent_id);
CREATE INDEX idx_senv_organization_type ON senv_organization(org_type);
CREATE INDEX idx_senv_organization_task ON senv_organization(task_id, batch_no);
CREATE UNIQUE INDEX idx_senv_organization_code_task ON senv_organization(task_id, batch_no, org_code);
`

服务方法:

| 方法 | 说明 |
| --- | --- |
| add(org, skip_unique_check=False) | 方案内单条插入; 默认唯一键冲突返回已存在记录 |
| get_by_id / get_by_code(task_id, batch_no, org_code) | 查询 |
| update / delete | 更新、级联删除 |
| list_roots / list_children / list_all | 列表查询(自动限定 (task_id, batch_no)) |
| list_ancestors / get_parent / search_by_name | 辅助查询 |
| count(...) | 条件计数(默认统计根节点) |
| build_organization_tree(root_id) | 以给定节点为根, 递归 fetch DESC, 返回 OrganizationTreeNode |
| build_full_tree(task_id, batch_no) | 当前仿真任务内全部根节点组成的列表 |
| build_tree_as_dict / build_tree_as_json | 树序列化 |
| batch_add / import_from_json / export_to_json | 批量 / JSON |
| **load_from_ssys(root_id, task_id, batch_no, overwrite)** | **新增**: 从系统空间子树整棵复制进仿真虚空间 |
| **load_from_smeta(root_id, task_id, batch_no, overwrite)** | **新增**: 从方案元空间子树整棵复制进仿真虚空间 |

默认 db_path = DB/SQLite, 与 SQLiteOperator 共用根目录。

### (senv_organization 与 smeta_organization 字段对照表)

| 字段 | smeta | senv |
| --- | --- | --- |
| task_id | — | ✓ NOT NULL |
| batch_no | — | ✓ NOT NULL |
| solution_id | ✓ NOT NULL | — |
| solution_version | ✓ NOT NULL | — |
| org_code / org_name / org_type / description / parent_id / parent_name / sort_order / status / extra_info / created_at / updated_at | ✓ | ✓ |
| UNIQUE 键 | (solution_id, solution_version, org_code) | (task_id, batch_no, org_code) |

### 三空间命名空间矩阵

| 空间 | 表 | BO | Service | 唯一键 |
| --- | --- | --- | --- | --- |
| 系统空间 (ssys) | ssys_organization | bo.ssys.Organization | SsysOrganizationService | org_code 全局唯一 |
| 方案元空间 (smeta) | smeta_organization | bo.smeta.Organization | SmetaOrganizationService | (solution_id, solution_version, org_code) |
| 仿真虚空间 (senv) | senv_organization | bo.senv.Organization | SenvOrganizationService | (task_id, batch_no, org_code) |

---
## 系统空间 · Employee（人员对象）

> 表名: `ssys_employee`  |  服务类: `SsysEmployeeService`  |  BO: `bo.ssys.employee.Employee`

### 字段定义

| 字段 | 类型 | 非空 | 说明 |
| --- | --- | --- | --- |
| id | INTEGER PK | ✔ | 自增主键 |
| emp_code | TEXT UNIQUE | ✔ | 人员编码（业务唯一） |
| emp_name | TEXT | ✔ | 姓名 |
| position | TEXT |   | 职位/岗位 |
| org_id | INTEGER FK |   | 归属组织ID（ssys_organization.id） |
| org_name | TEXT |   | 归属组织名称（冗余字段，便于直接展示） |
| email | TEXT |   | 邮箱 |
| phone | TEXT |   | 联系电话 |
| status | TEXT | ✔ | active/disabled/archived/resigned，默认 active |
| extra_info | TEXT |   | 扩展信息（JSON） |
| created_at | TEXT | ✔ | ISO 创建时间 |
| updated_at | TEXT | ✔ | ISO 更新时间 |

### 索引

| 名称 | 字段 | 类型 |
| --- | --- | --- |
| idx_ssys_employee_code | emp_code | UNIQUE |
| idx_ssys_employee_name | emp_name | |
| idx_ssys_employee_org | org_id | |
| idx_ssys_employee_status | status | |

### SsysEmployeeService 方法

```python
add(Employee)                    # 新增（INSERT → 返回带 id 的完整记录）
get_by_id(emp_id)                # 按 ID 查本身
get_by_code(emp_code)            # 按人员编码查本身（UNIQUE）
update(Employee)                 # 更新（根据 id）
delete(emp_id)                   # 删除
list_all(status, org_id, keyword, page, page_size)   # 查全量（支持过滤 + 分页）
search_by_name(keyword)          # 按姓名/编码/职位模糊查
list_by_org(org_id, include_subtree=False)  # 按归属组织查；include_subtree=True 时递归子组织
count(status, org_id, keyword)   # 统计
```

### 使用示例

```python
from data_storage_services import SsysOrganizationService, SsysEmployeeService
from bo.ssys import Organization, Employee

with SsysOrganizationService() as osvc:
    RD = osvc.get_by_code("RD")
with SsysEmployeeService() as svc:
    emp = svc.add(Employee(emp_code="EMP-001", emp_name="张三", position="架构师", org_id=RD.id))
    emp.position = "首席架构师"
    svc.update(emp)
    # 查研发部及其子组织所有员工
    for e in svc.list_by_org(RD.id, include_subtree=True):
        print(e.emp_name, e.position, e.org_name)
```

### 与系统空间组织对象的关系

- `Employee.org_id` → `Organization.id`（外键，ON DELETE SET NULL）
- 批量 `list_by_org(..., include_subtree=True)` 会借用 `SsysOrganizationService.build_organization_tree` 找到所有子组织 ID，一次性查回

### 验证

- Pydantic validator：`status` 必须属于 {active, disabled, archived, resigned}；`emp_code`/`emp_name` 自动 strip
- UNIQUE(emp_code)：服务层不加 try，重复 emp_code 由调用方捕获 IntegrityError 或先调 get_by_code 判断

---
## 方案元空间 · Employee（人员对象）

> 表名: `smeta_employee`  |  服务类: `SmetaEmployeeService`  |  BO: `bo.smeta.employee.Employee`

### 与系统空间的差异

在系统空间 Employee 完整结构之上扩展两个业务唯一键字段：
- `solution_id` TEXT NOT NULL — 方案ID
- `solution_version` TEXT NOT NULL — 方案版本号

业务唯一键（UNIQUE）为 **(solution_id, solution_version, emp_code)**：
同一人员编码 `emp_code` 可在不同方案/版本下独立存在；同一方案/版本下编码唯一。

### 字段定义

| 字段 | 类型 | 非空 | 说明 |
| --- | --- | --- | --- |
| id | INTEGER PK | ✔ | 自增主键 |
| solution_id | TEXT | ✔ | 方案ID |
| solution_version | TEXT | ✔ | 方案版本号 |
| emp_code | TEXT | ✔ | 人员编码（方案内唯一） |
| emp_name | TEXT | ✔ | 姓名 |
| position | TEXT |   | 职位 |
| org_id | INTEGER FK |   | 归属组织ID → smeta_organization.id |
| org_name | TEXT |   | 归属组织名称（冗余展示） |
| email / phone | TEXT |   | 联系信息 |
| status | TEXT | ✔ | active/disabled/archived/resigned，默认 active |
| extra_info | TEXT |   | 扩展信息（JSON） |
| created_at / updated_at | TEXT | ✔ | ISO 时间 |

### 索引

| 名称 | 字段 | 类型 |
| --- | --- | --- |
| idx_smeta_employee_code_solution | (solution_id, solution_version, emp_code) | **UNIQUE** |
| idx_smeta_employee_name | emp_name | |
| idx_smeta_employee_org | org_id | |
| idx_smeta_employee_status | status | |

### SmetaEmployeeService 方法

所有查询方法均要求显式传入 `(solution_id, solution_version)`，强制限定方案命名空间：

```python
add(Employee)
get_by_id(emp_id)
get_by_code(solution_id, solution_version, emp_code)
update(Employee)
delete(emp_id)
list_all(solution_id, solution_version, status, org_id, keyword, page, page_size)
search_by_name(solution_id, solution_version, keyword)
list_by_org(solution_id, solution_version, org_id)
count(solution_id, solution_version, status, org_id, keyword)
list_solutions()                                # 列出当前表内所有方案ID/版本对
load_from_ssys(solution_id, solution_version,
               ssys_org_id=None, ssys_emp_ids=None,
               overwrite=False)                 # 系统空间 → 方案元空间 批量复制
```

### load_from_ssys 批量复制说明

- 内部借用 `SsysEmployeeService` 读取系统空间数据
- 可按组织（含子组织递归 `list_by_org(..., include_subtree=True)`）或按员工ID列表复制
- 自动去重（同 emp_code 只取第一条）+ 跳过已存在于目标方案的员工
- `overwrite=True` 时先清空 `(solution_id, solution_version)` 下的全部员工再复制

### 使用示例

```python
from data_storage_services import SmetaEmployeeService

with SmetaEmployeeService() as svc:
    svc.load_from_ssys(
        solution_id="SOL-001", solution_version="v1.0",
        ssys_org_id=1, overwrite=True,
    )
    for e in svc.list_all("SOL-001", "v1.0"):
        print(e.emp_code, e.emp_name, e.position, e.org_name)
```

---
## 仿真虚空间 · Employee（人员对象）

> 表名: `senv_employee`  |  服务类: `SenvEmployeeService`  |  BO: `bo.senv.employee.Employee`

### 与系统空间的差异

在系统空间 Employee 完整结构之上扩展两个业务唯一键字段：
- `task_id` TEXT NOT NULL — 仿真任务ID
- `batch_no` TEXT NOT NULL — 仿真任务批次号

业务唯一键（UNIQUE）为 **(task_id, batch_no, emp_code)**：
同一人员编码 `emp_code` 可在不同任务/批次下独立存在；同一任务/批次下编码唯一。

### 字段定义

| 字段 | 类型 | 非空 | 说明 |
| --- | --- | --- | --- |
| id | INTEGER PK | ✔ | 自增主键 |
| task_id | TEXT | ✔ | 仿真任务ID |
| batch_no | TEXT | ✔ | 仿真任务批次号 |
| emp_code | TEXT | ✔ | 人员编码（任务批次内唯一） |
| emp_name | TEXT | ✔ | 姓名 |
| position | TEXT |   | 职位 |
| org_id | INTEGER FK |   | 归属组织ID → senv_organization.id |
| org_name | TEXT |   | 归属组织名称（冗余展示） |
| email / phone | TEXT |   | 联系信息 |
| status | TEXT | ✔ | active/disabled/archived/resigned，默认 active |
| extra_info | TEXT |   | 扩展信息（JSON） |
| created_at / updated_at | TEXT | ✔ | ISO 时间 |

### 索引

| 名称 | 字段 | 类型 |
| --- | --- | --- |
| idx_senv_employee_code_task | (task_id, batch_no, emp_code) | **UNIQUE** |
| idx_senv_employee_name | emp_name | |
| idx_senv_employee_org | org_id | |
| idx_senv_employee_status | status | |

### SenvEmployeeService 方法

所有查询方法均要求显式传入 `(task_id, batch_no)`，强制限定仿真任务命名空间：

```python
add(Employee)
get_by_id(emp_id)
get_by_code(task_id, batch_no, emp_code)
update(Employee)
delete(emp_id)
list_all(task_id, batch_no, status, org_id, keyword, page, page_size)
search_by_name(task_id, batch_no, keyword)
list_by_org(task_id, batch_no, org_id)
count(task_id, batch_no, status, org_id, keyword)
list_tasks()

load_from_ssys(task_id, batch_no,
               ssys_org_id=None, ssys_emp_ids=None,
               overwrite=False)

load_from_smeta(task_id, batch_no,
                solution_id, solution_version,
                smeta_org_id=None, smeta_emp_ids=None,
                overwrite=False)
```

### 批量复制说明

- `load_from_ssys`：从系统空间复制员工（支持按组织含子组织递归、或按员工ID列表）
- `load_from_smeta`：从方案元空间复制员工（支持按方案+版本，或再加按组织/ID过滤）
- 内部去重（同 emp_code 只取第一条）+ 跳过已存在于目标任务/批次的员工
- `overwrite=True` 时先清空目标 `(task_id, batch_no)` 再复制

### 三空间人员对象对照

| 空间 | 表 | 扩展字段 | 唯一键 |
| --- | --- | --- | --- |
| 系统空间 | ssys_employee | — | emp_code |
| 方案元空间 | smeta_employee | solution_id, solution_version | (solution_id, solution_version, emp_code) |
| 仿真虚空间 | senv_employee | task_id, batch_no | (task_id, batch_no, emp_code) |

---
## 系统空间 · Role（角色对象）

> 表名: `ssys_role`  |  服务类: `SsysRoleService`  |  BO: `bo.ssys.role.Role`

### 字段定义

| 字段 | 类型 | 非空 | 说明 |
| --- | --- | --- | --- |
| id | INTEGER PK | ✔ | 自增主键 |
| role_code | TEXT UNIQUE | ✔ | 角色编码（业务唯一） |
| role_name | TEXT | ✔ | 角色名称 |
| description | TEXT |   | 角色描述 |
| status | TEXT | ✔ | active/disabled/archived，默认 active |
| extra_info | TEXT |   | 扩展信息（JSON） |
| created_at / updated_at | TEXT | ✔ | ISO 时间 |

### 索引

| 名称 | 字段 | 类型 |
| --- | --- | --- |
| idx_ssys_role_code | role_code | **UNIQUE** |
| idx_ssys_role_name | role_name | |
| idx_ssys_role_status | status | |

### SsysRoleService 方法

```python
add(Role)                         # 新增
get_by_id(role_id)                # 按 ID 查本身
get_by_code(role_code)            # 按角色编码查本身（UNIQUE）
update(Role)                      # 按 id 更新
delete(role_id)                   # 按 id 删除
list_all(status, keyword, page, page_size)  # 查全量 + 过滤 + 分页
search_by_name(keyword)           # 按名称/编码/描述模糊查
count(status, keyword)            # 统计
```

### 与项目旧 RoleService 的关系

- 旧版 `bo.role.Role` + `RoleService`（sql_db_services 下，操作 `roles` 表）保留不动
- 新版系统空间 `bo.ssys.Role` + `SsysRoleService` 操作 `ssys_role` 表，遵循三空间命名空间架构
- 两者并存，供新旧模块按需选用

### 验证

- Pydantic validator：`status ∈ {active, disabled, archived}`；`role_code`/`role_name` 自动 strip
- UNIQUE(role_code)：重复编码触发 `IntegrityError`（由调用方决定如何处理）

---
## 方案元空间 · Role（角色对象）

> 表名: `smeta_role`  |  服务类: `SmetaRoleService`  |  BO: `bo.smeta.role.Role`

### 与系统空间的差异

在系统空间 Role 完整结构之上扩展两个业务唯一键字段：
- `solution_id` TEXT NOT NULL — 方案ID
- `solution_version` TEXT NOT NULL — 方案版本号

业务唯一键（UNIQUE）为 **(solution_id, solution_version, role_code)**：
同一角色编码 `role_code` 可在不同方案/版本下独立存在；同一方案/版本下编码唯一。
（用户原文描述 "role_id + solution_id + solution_version" 共同唯一，但 role_id 是数据库自增主键本身就唯一；
实际业务维度是方案+版本+编码三字段联合，故 UNIQUE 落在 `(solution_id, solution_version, role_code)` 上。）

### 字段定义

| 字段 | 类型 | 非空 | 说明 |
| --- | --- | --- | --- |
| id | INTEGER PK | ✔ | 自增主键 |
| solution_id | TEXT | ✔ | 方案ID |
| solution_version | TEXT | ✔ | 方案版本号 |
| role_code | TEXT | ✔ | 角色编码（方案内唯一） |
| role_name | TEXT | ✔ | 角色名称 |
| description | TEXT |   | 角色描述 |
| status | TEXT | ✔ | active/disabled/archived，默认 active |
| extra_info | TEXT |   | 扩展信息（JSON） |
| created_at / updated_at | TEXT | ✔ | ISO 时间 |

### 索引

| 名称 | 字段 | 类型 |
| --- | --- | --- |
| idx_smeta_role_code_solution | (solution_id, solution_version, role_code) | **UNIQUE** |
| idx_smeta_role_name | role_name | |
| idx_smeta_role_status | status | |

### SmetaRoleService 方法

所有查询方法均要求显式传入 `(solution_id, solution_version)`，强制限定方案命名空间：

```python
add(Role)
get_by_id(role_id)
get_by_code(solution_id, solution_version, role_code)
update(Role)
delete(role_id)
list_all(solution_id, solution_version, status, keyword, page, page_size)
search_by_name(solution_id, solution_version, keyword)
count(solution_id, solution_version, status, keyword)
list_solutions()

load_from_ssys(solution_id, solution_version,
               ssys_role_ids=None, overwrite=False)   # 系统空间 → 方案元空间 批量复制
```

### load_from_ssys 批量复制说明

- 内部借用 `SsysRoleService` 读取系统空间角色
- 不传 ssys_role_ids 时复制系统空间所有角色；传了则按 ID 列表精确复制
- 自动去重（同 role_code 只取第一条）+ 跳过已存在于目标方案的角色
- `overwrite=True` 时先 DELETE 整个方案/版本的角色再复制

### 三空间角色对象对照

| 空间 | 表 | 扩展字段 | 唯一键 |
| --- | --- | --- | --- |
| 系统空间 | ssys_role | — | role_code |
| 方案元空间 | smeta_role | solution_id, solution_version | (solution_id, solution_version, role_code) |
| 仿真虚空间 | senv_role（待创建） | task_id, batch_no | (task_id, batch_no, role_code) |

---
## 仿真虚空间 · Role（角色对象）

> 表名: `senv_role`  |  服务类: `SenvRoleService`  |  BO: `bo.senv.role.Role`

### 与系统空间的差异

在系统空间 Role 完整结构之上扩展两个业务唯一键字段：
- `task_id` TEXT NOT NULL — 仿真任务ID
- `batch_no` TEXT NOT NULL — 仿真任务批次号

业务唯一键（UNIQUE）为 **(task_id, batch_no, role_code)**：
同一角色编码 `role_code` 可在不同任务/批次下独立存在；同一任务/批次内编码唯一。
（用户原文描述 "role_id + task_id + batch_no" 共同唯一，但 role_id 是数据库自增主键本身就天然唯一；
实际业务维度是任务+批次+编码三字段联合，故 UNIQUE 落在 `(task_id, batch_no, role_code)` 上。）

### 字段定义

| 字段 | 类型 | 非空 | 说明 |
| --- | --- | --- | --- |
| id | INTEGER PK | ✔ | 自增主键 |
| task_id | TEXT | ✔ | 仿真任务ID |
| batch_no | TEXT | ✔ | 仿真任务批次号 |
| role_code | TEXT | ✔ | 角色编码（任务批次内唯一） |
| role_name | TEXT | ✔ | 角色名称 |
| description | TEXT |   | 角色描述 |
| status | TEXT | ✔ | active/disabled/archived，默认 active |
| extra_info | TEXT |   | 扩展信息（JSON） |
| created_at / updated_at | TEXT | ✔ | ISO 时间 |

### 索引

| 名称 | 字段 | 类型 |
| --- | --- | --- |
| idx_senv_role_code_task | (task_id, batch_no, role_code) | **UNIQUE** |
| idx_senv_role_name | role_name | |
| idx_senv_role_status | status | |

### SenvRoleService 方法

所有查询方法均要求显式传入 `(task_id, batch_no)`，强制限定仿真任务命名空间：

```python
add(Role)
get_by_id(role_id)
get_by_code(task_id, batch_no, role_code)
update(Role)
delete(role_id)
list_all(task_id, batch_no, status, keyword, page, page_size)
search_by_name(task_id, batch_no, keyword)
count(task_id, batch_no, status, keyword)
list_tasks()

load_from_ssys(task_id, batch_no,
               ssys_role_ids=None, overwrite=False)

load_from_smeta(task_id, batch_no,
                solution_id, solution_version,
                smeta_role_ids=None, overwrite=False)
```

### 批量复制说明

- `load_from_ssys`：从系统空间复制角色（支持按 ID 列表精确复制，不传则复制全部）
- `load_from_smeta`：从方案元空间复制角色（支持按方案+版本，再加按 ID 过滤）
- 内部去重 + 跳过已存在于目标任务/批次的角色
- `overwrite=True` 时先 DELETE 再复制

### 三空间角色对象完整对照表

| 空间 | 表 | 扩展字段 | 唯一键 | 批量复制入口 |
| --- | --- | --- | --- | --- |
| 系统空间 | ssys_role | — | role_code | — |
| 方案元空间 | smeta_role | solution_id, solution_version | (solution_id, solution_version, role_code) | load_from_ssys |
| 仿真虚空间 | senv_role | task_id, batch_no | (task_id, batch_no, role_code) | load_from_ssys / load_from_smeta |

> 至此，Organization / Employee / Role 三对象 × 三空间（ssys / smeta / senv）共 9 组已完整落地。

---
## 系统空间 · Employee 角色关联 (M:N)

### 关联关系

一个员工对象可以对应多个角色对象，一个角色对象也可以分配给多个员工（M:N 多对多）。
系统空间使用独立中间表 `ssys_employee_role` 存储关联；方案元空间和仿真虚空间也各自有对应中间表（smeta_employee_role / senv_employee_role）。

### 表: ssys_employee_role

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | INTEGER PK | ✔ | 自增 |
| emp_id | INTEGER FK | ✔ | → ssys_employee.id ON DELETE CASCADE |
| role_id | INTEGER FK | ✔ | → ssys_role.id ON DELETE CASCADE |
| assigned_at | TEXT | ✔ | 分配时间 |

**UNIQUE(emp_id, role_id)** — 同一员工-角色对只保存一条。

### SsysEmployeeService 新增方法

```python
assign_role(emp_id, role_id)          # 分配角色（幂等，重复分配不报错）
revoke_role(emp_id, role_id)          # 收回角色
list_roles(emp_id)                    # 返回 Role 对象列表
list_role_ids(emp_id)                 # 返回 role_id 整数列表
has_role(emp_id, role_id)             # 是否持有某角色
assign_roles(emp_id, [r1,r2,...])     # 批量分配
revoke_all_roles(emp_id)              # 收回该员工所有角色
employees_with_role(role_id)          # 反查：持有某角色的员工列表
```

### 方案元空间 / 仿真虚空间 对称扩展

| 空间 | 中间表 | 唯一键 | Service 方法（与系统空间同名） |
| --- | --- | --- | --- |
| 系统空间 | ssys_employee_role | (emp_id, role_id) | assign_role / revoke_role / list_roles / list_role_ids / has_role / assign_roles / revoke_all_roles / employees_with_role |
| 方案元空间 | smeta_employee_role | (solution_id, solution_version, emp_id, role_id) | 同上 |
| 仿真虚空间 | senv_employee_role | (task_id, batch_no, emp_id, role_id) | 同上 |

> 使用 `assign_role / list_roles ...` 前先调用 `load_from_ssys` / `load_from_smeta` 或手动设定 `_solution_id/_solution_version`（smeta）或 `_task_id/_batch_no`（senv）。

## 2026-06-28 20:43:32 追加

# SQLite 数据表结构

数据库文件: DB/SQLite/simulation.db
初始化脚本: data_storage_services/SQLite/init_db.py + sqlite_db_init.sql

## 方案元空间 (smeta)

### 表 smeta_file
方案文件对象 (实体文件元数据)。实体文件位于 Files/Solutions/<solution_id>/<主文档|附件文档|参考文档>/<file_id>__<file_name>。

| 列 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | TEXT | PK UNIQUE | 文件ID (UUID4 hex32, 业务唯一) |
| file_name | TEXT | NOT NULL | 文件名称 (含扩展名) |
| version_no | TEXT | NOT NULL DEFAULT '1.0' | 版本号 |
| file_category | TEXT | NOT NULL | 文件类别: 主文档 / 附件文档 / 参考文档 |
| solution_id | TEXT | NOT NULL | 所属方案 ID |
| solution_name | TEXT | | 所属方案名称 |
| physical_path | TEXT | | 实体文件相对路径 |
| content_text | TEXT | | 可选, 纯文本正文 |
| file_size | INTEGER | | 字节大小 |
| mime_type | TEXT | | MIME 类型 |
| description | TEXT | | 文件说明 |
| created_at | TEXT | NOT NULL | ISO 创建时间 |
| updated_at | TEXT | NOT NULL | ISO 更新时间 |

索引: idx_smeta_file_id, idx_smeta_file_solution, idx_smeta_file_name, idx_smeta_file_category

### 表 smeta_solutions
方案对象 (当前状态快照)。与 smeta_solution_revision 配合提供完整修订轨迹。

| 列 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | TEXT | PK | 方案ID (UUID4 hex32) |
| solution_name | TEXT | UNIQUE NOT NULL | 方案名称 (业务唯一) |
| major_version | INTEGER | NOT NULL DEFAULT 1 | 主版本号 |
| minor_version | INTEGER | NOT NULL DEFAULT 0 | 次版本号 |
| status | TEXT | NOT NULL DEFAULT '草稿' | 方案状态 (草稿/评审中/已批准/已驳回/已归档) |
| category | TEXT | | 方案类别, 可选 |
| summary | TEXT | | 摘要, 可选 |
| key_purpose | TEXT (JSON) | | 目的列表 ["",""] |
| key_objectives | TEXT (JSON) | | 目标列表 |
| key_measures | TEXT (JSON) | | 举措列表 |
| key_organizations | TEXT (JSON) | | 组织列表 |
| key_personnel | TEXT (JSON) | | 人员列表 |
| key_work_mechanism | TEXT | | 工作机制描述 |
| key_work_content | TEXT | | 工作内容描述 |
| key_constraints | TEXT (JSON) | | 限制条件列表 |
| key_risk_list | TEXT (JSON) | | 风险清单 |
| key_issue_list | TEXT (JSON) | | 问题清单 |
| key_notes | TEXT | | 其它说明 |
| doc_main_docs | TEXT (JSON) | | 主文档 File.id 列表 |
| doc_attachments | TEXT (JSON) | | 附件文档 File.id 列表 |
| doc_references | TEXT (JSON) | | 参考文档 File.id 列表 |
| created_at | TEXT | NOT NULL | ISO 创建时间 |
| updated_at | TEXT | NOT NULL | ISO 更新时间 |

索引: idx_smeta_solutions_name, idx_smeta_solutions_status, idx_smeta_solutions_category

### 表 smeta_solution_revision
方案修订历史 (追加式, 一条修订一行)。

| 列 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| solution_id | TEXT | PK+FK | 所属方案 ID |
| revision_no | INTEGER | PK | 修订序号 (从 1 递增) |
| modifier | TEXT | NOT NULL | 修改人 |
| modified_at | TEXT | NOT NULL | ISO 修改时间 |
| change_summary | TEXT | NOT NULL | 修改内容描述 |

索引: idx_smeta_solution_revision_sid


### 仿真虚空间方案对象扩展

仿真虚空间 (senv) 的“方案对象”完整复制方案元空间方案对象结构, 新增仿真任务ID / 仿真任务批次号两个业务属性。
方案对象ID + 仿真任务ID + 仿真任务批次号 三者联合唯一定位仿真虚空间内的一个方案对象实例。

数据库表: senv_solutions / senv_solution_revision
BO: bo/senv/solution.py (Pydantic Solution)
Service: data_storage_services/sql_db_services/senv/solution_service.py · SenvSolutionService

### 表 senv_solutions

| 列 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | TEXT | PK | 方案ID (UUID4 hex32, 业务唯一) |
| solution_name | TEXT | NOT NULL | 方案名称 (同一仿真任务+批次内唯一) |
| major_version | INTEGER | NOT NULL DEFAULT 1 | 主版本号 |
| minor_version | INTEGER | NOT NULL DEFAULT 0 | 次版本号 |
| status | TEXT | NOT NULL DEFAULT '草稿' | 方案状态 |
| category | TEXT | | 方案类别 |
| summary | TEXT | | 摘要 |
| key_purpose | TEXT (JSON) | | 目的列表 |
| key_objectives | TEXT (JSON) | | 目标列表 |
| key_measures | TEXT (JSON) | | 举措列表 |
| key_organizations | TEXT (JSON) | | 组织列表 |
| key_personnel | TEXT (JSON) | | 人员列表 |
| key_work_mechanism | TEXT | | 工作机制 |
| key_work_content | TEXT | | 工作内容 |
| key_constraints | TEXT (JSON) | | 限制条件 |
| key_risk_list | TEXT (JSON) | | 风险清单 |
| key_issue_list | TEXT (JSON) | | 问题清单 |
| key_notes | TEXT | | 其它说明 |
| doc_main_docs | TEXT (JSON) | | 主文档 File.id 列表 |
| doc_attachments | TEXT (JSON) | | 附件文档 File.id 列表 |
| doc_references | TEXT (JSON) | | 参考文档 File.id 列表 |
| simulation_task_id | TEXT | PK NOT NULL | 仿真任务ID |
| simulation_task_batch | TEXT | PK NOT NULL | 仿真任务批次号 |
| created_at | TEXT | NOT NULL | ISO 创建时间 |
| updated_at | TEXT | NOT NULL | ISO 更新时间 |

索引: idx_senv_solutions_name_task (UNIQUE) on (solution_name, simulation_task_id, simulation_task_batch); idx_senv_solutions_status (status); idx_senv_solutions_task (simulation_task_id, simulation_task_batch)

### 表 senv_solution_revision

| 列 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| solution_id | TEXT | PK | 所属方案 ID |
| simulation_task_id | TEXT | PK NOT NULL | 仿真任务ID |
| simulation_task_batch | TEXT | PK NOT NULL | 仿真任务批次号 |
| revision_no | INTEGER | PK | 修订序号 (从 1 递增) |
| modifier | TEXT | NOT NULL | 修改人 |
| modified_at | TEXT | NOT NULL | ISO 修改时间 |
| change_summary | TEXT | NOT NULL | 修改内容描述 |

索引: idx_senv_solution_revision_sid

### SenvSolutionService 关键方法

| 方法 | 说明 |
| --- | --- |
| 
ew_solution(solution_name, simulation_task_id, simulation_task_batch, modifier, category, summary) | 构造仿真虚空间新方案 |
| dd(solution) | 新增 (检查联合唯一名称) |
| update(solution, modifier, change_summary) | 更新并追加修订 |
| ump_version(solution_id, simulation_task_id, simulation_task_batch, mode, modifier, change_summary) | 主/次版本递增 |
| get_by_unique(solution_id, simulation_task_id, simulation_task_batch) | 方案ID+任务+批次 精确获取 |
| get_by_name(solution_name, simulation_task_id, simulation_task_batch) | 联合名称唯一获取 |
| list_all(simulation_task_id, simulation_task_batch, status, category) | 按任务/批次/状态/类别列表 |
| search_by_content(kw, simulation_task_id, simulation_task_batch) | 摘要/说明/工作内容关键字搜索 |
| count(simulation_task_id, simulation_task_batch) | 计数 |
| export(solution_id, simulation_task_id, simulation_task_batch) | 纯文本导出 |
| delete(solution_id, simulation_task_id, simulation_task_batch) | 删除 (连同修订表) |
| delete_by_task(simulation_task_id, simulation_task_batch) | 按任务/批次批量删除 |
| rom_smeta(smeta_solution_id, simulation_task_id, simulation_task_batch, modifier) | 从方案元空间复制方案 (含修订轨迹, 重新分配ID) |
