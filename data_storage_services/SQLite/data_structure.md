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

| 版本 | 日期 | 修改内容 |
|------|------|----------|
| 1.0 | 2026-06-20 | 初始版本，创建所有业务表结构 |

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
