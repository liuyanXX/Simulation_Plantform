CREATE TABLE IF NOT EXISTS solutions (
    solution_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT '1.0',
    status TEXT NOT NULL DEFAULT 'draft',
    priority TEXT NOT NULL DEFAULT 'medium',
    purpose TEXT,
    objectives TEXT,
    initiatives TEXT,
    working_mechanism TEXT,
    organization TEXT,
    personnel TEXT,
    roles TEXT,
    work_content TEXT,
    constraints TEXT,
    risks TEXT,
    issues TEXT,
    other_notes TEXT,
    main_document_id TEXT,
    auxiliary_document_ids TEXT,
    description TEXT,
    owner TEXT,
    created_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    effective_date TEXT,
    expiry_date TEXT,
    tags TEXT,
    metadata TEXT
);

CREATE TABLE IF NOT EXISTS solution_documents (
    document_id TEXT PRIMARY KEY,
    file_name TEXT NOT NULL,
    version TEXT NOT NULL,
    document_type TEXT NOT NULL DEFAULT 'attachment',
    file_content BLOB,
    text_content TEXT,
    description TEXT,
    format TEXT,
    size INTEGER,
    created_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    related_solution_ids TEXT,
    understanding_status TEXT NOT NULL DEFAULT 'pending',
    metadata TEXT
);

CREATE TABLE IF NOT EXISTS solution_files (
    file_id TEXT PRIMARY KEY,
    document_id TEXT,
    file_name TEXT NOT NULL,
    version TEXT NOT NULL,
    file_type TEXT NOT NULL DEFAULT 'attachment',
    file_content BLOB,
    text_content TEXT,
    description TEXT,
    format TEXT,
    size INTEGER,
    created_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    related_solution_ids TEXT,
    understanding_status TEXT NOT NULL DEFAULT 'pending',
    metadata TEXT,
    FOREIGN KEY (document_id) REFERENCES solution_documents(document_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    task_name TEXT NOT NULL,
    task_type TEXT NOT NULL DEFAULT 'normal',
    expected_start_time TEXT NOT NULL,
    expected_end_time TEXT NOT NULL,
    scheduled_start_time TEXT,
    scheduled_end_time TEXT,
    actual_start_time TEXT,
    actual_end_time TEXT,
    content TEXT NOT NULL,
    execute_role TEXT NOT NULL,
    resource_consumption REAL NOT NULL,
    priority TEXT NOT NULL DEFAULT 'medium',
    output_target_role TEXT,
    next_task_info TEXT,
    is_completed INTEGER NOT NULL DEFAULT 0,
    task_source TEXT,
    task_destinations TEXT,
    flow_group_id TEXT,
    graph_id TEXT,
    manifest_id TEXT
);

CREATE TABLE IF NOT EXISTS ai_workers (
    employee_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    roles TEXT NOT NULL,
    daily_work_hours REAL NOT NULL DEFAULT 8.0,
    org_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS organizations (
    org_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    parent_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS roles (
    name TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS task_flow_groups (
    flow_id TEXT PRIMARY KEY,
    flow_name TEXT NOT NULL,
    description TEXT,
    manifest_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks_graphs (
    graph_id TEXT PRIMARY KEY,
    graph_name TEXT NOT NULL,
    description TEXT,
    manifest_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS task_manifests (
    manifest_id TEXT PRIMARY KEY,
    manifest_name TEXT NOT NULL,
    description TEXT,
    solution_id TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS knowledge (
    knowledge_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    content TEXT NOT NULL,
    index_ids TEXT,
    tags TEXT,
    category TEXT NOT NULL DEFAULT 'evaluation',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS org_workers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT NOT NULL,
    org_id TEXT NOT NULL,
    assigned_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS ssys_organization (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_code TEXT NOT NULL UNIQUE,
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
    FOREIGN KEY (parent_id) REFERENCES ssys_organization(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_ssys_organization_parent ON ssys_organization(parent_id);
CREATE INDEX IF NOT EXISTS idx_ssys_organization_type ON ssys_organization(org_type);
CREATE UNIQUE INDEX IF NOT EXISTS idx_ssys_organization_code ON ssys_organization(org_code);

CREATE TABLE IF NOT EXISTS decomposition_behaviors (
    behavior_id TEXT PRIMARY KEY,
    solution_id TEXT NOT NULL,
    solution_name TEXT,
    strategy TEXT NOT NULL DEFAULT 'auto',
    status TEXT NOT NULL DEFAULT 'completed',
    organizations TEXT,
    personnel TEXT,
    roles TEXT,
    task_manifest_id TEXT,
    tasks_graph_id TEXT,
    flow_groups TEXT,
    tasks TEXT,
    process_log TEXT,
    result_summary TEXT,
    created_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (solution_id) REFERENCES solutions(solution_id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS smeta_organization (
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

CREATE INDEX IF NOT EXISTS idx_smeta_organization_parent ON smeta_organization(parent_id);
CREATE INDEX IF NOT EXISTS idx_smeta_organization_type ON smeta_organization(org_type);
CREATE INDEX IF NOT EXISTS idx_smeta_organization_sol ON smeta_organization(solution_id, solution_version);
CREATE UNIQUE INDEX IF NOT EXISTS idx_smeta_organization_code_sol ON smeta_organization(solution_id, solution_version, org_code);

CREATE TABLE IF NOT EXISTS senv_organization (
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

CREATE INDEX IF NOT EXISTS idx_senv_organization_parent ON senv_organization(parent_id);
CREATE INDEX IF NOT EXISTS idx_senv_organization_type ON senv_organization(org_type);
CREATE INDEX IF NOT EXISTS idx_senv_organization_task ON senv_organization(task_id, batch_no);
CREATE UNIQUE INDEX IF NOT EXISTS idx_senv_organization_code_task ON senv_organization(task_id, batch_no, org_code);

CREATE TABLE IF NOT EXISTS ssys_employee (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    emp_code TEXT NOT NULL,
    emp_name TEXT NOT NULL,
    position TEXT,
    org_id INTEGER,
    org_name TEXT,
    email TEXT,
    phone TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    extra_info TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (org_id) REFERENCES ssys_organization(id) ON DELETE SET NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_ssys_employee_code ON ssys_employee(emp_code);
CREATE INDEX IF NOT EXISTS idx_ssys_employee_name ON ssys_employee(emp_name);
CREATE INDEX IF NOT EXISTS idx_ssys_employee_org ON ssys_employee(org_id);
CREATE INDEX IF NOT EXISTS idx_ssys_employee_status ON ssys_employee(status);

CREATE TABLE IF NOT EXISTS smeta_employee (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    solution_id TEXT NOT NULL,
    solution_version TEXT NOT NULL,
    emp_code TEXT NOT NULL,
    emp_name TEXT NOT NULL,
    position TEXT,
    org_id INTEGER,
    org_name TEXT,
    email TEXT,
    phone TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    extra_info TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (org_id) REFERENCES smeta_organization(id) ON DELETE SET NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_smeta_employee_code_solution
    ON smeta_employee(solution_id, solution_version, emp_code);
CREATE INDEX IF NOT EXISTS idx_smeta_employee_name ON smeta_employee(emp_name);
CREATE INDEX IF NOT EXISTS idx_smeta_employee_org ON smeta_employee(org_id);
CREATE INDEX IF NOT EXISTS idx_smeta_employee_status ON smeta_employee(status);

CREATE TABLE IF NOT EXISTS senv_employee (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    batch_no TEXT NOT NULL,
    emp_code TEXT NOT NULL,
    emp_name TEXT NOT NULL,
    position TEXT,
    org_id INTEGER,
    org_name TEXT,
    email TEXT,
    phone TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    extra_info TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (org_id) REFERENCES senv_organization(id) ON DELETE SET NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_senv_employee_code_task
    ON senv_employee(task_id, batch_no, emp_code);
CREATE INDEX IF NOT EXISTS idx_senv_employee_name ON senv_employee(emp_name);
CREATE INDEX IF NOT EXISTS idx_senv_employee_org ON senv_employee(org_id);
CREATE INDEX IF NOT EXISTS idx_senv_employee_status ON senv_employee(status);

CREATE TABLE IF NOT EXISTS ssys_role (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_code TEXT NOT NULL,
    role_name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    extra_info TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_ssys_role_code ON ssys_role(role_code);
CREATE INDEX IF NOT EXISTS idx_ssys_role_name ON ssys_role(role_name);
CREATE INDEX IF NOT EXISTS idx_ssys_role_status ON ssys_role(status);

CREATE TABLE IF NOT EXISTS smeta_role (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    solution_id TEXT NOT NULL,
    solution_version TEXT NOT NULL,
    role_code TEXT NOT NULL,
    role_name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    extra_info TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_smeta_role_code_solution
    ON smeta_role(solution_id, solution_version, role_code);
CREATE INDEX IF NOT EXISTS idx_smeta_role_name ON smeta_role(role_name);
CREATE INDEX IF NOT EXISTS idx_smeta_role_status ON smeta_role(status);

CREATE TABLE IF NOT EXISTS smeta_role (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    solution_id TEXT NOT NULL,
    solution_version TEXT NOT NULL,
    role_code TEXT NOT NULL,
    role_name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    extra_info TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_smeta_role_code_solution
    ON smeta_role(solution_id, solution_version, role_code);
CREATE INDEX IF NOT EXISTS idx_smeta_role_name ON smeta_role(role_name);
CREATE INDEX IF NOT EXISTS idx_smeta_role_status ON smeta_role(status);

CREATE TABLE IF NOT EXISTS senv_role (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    batch_no TEXT NOT NULL,
    role_code TEXT NOT NULL,
    role_name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    extra_info TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_senv_role_code_task
    ON senv_role(task_id, batch_no, role_code);
CREATE INDEX IF NOT EXISTS idx_senv_role_name ON senv_role(role_name);
CREATE INDEX IF NOT EXISTS idx_senv_role_status ON senv_role(status);

CREATE TABLE IF NOT EXISTS senv_role (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    batch_no TEXT NOT NULL,
    role_code TEXT NOT NULL,
    role_name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    extra_info TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_senv_role_code_task
    ON senv_role(task_id, batch_no, role_code);
CREATE INDEX IF NOT EXISTS idx_senv_role_name ON senv_role(role_name);
CREATE INDEX IF NOT EXISTS idx_senv_role_status ON senv_role(status);

-- ===== 系统空间 · 员工-角色关联 =====
CREATE TABLE IF NOT EXISTS ssys_employee_role (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    emp_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    assigned_at TEXT NOT NULL,
    FOREIGN KEY (emp_id) REFERENCES ssys_employee(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES ssys_role(id) ON DELETE CASCADE,
    UNIQUE(emp_id, role_id)
);
CREATE INDEX IF NOT EXISTS idx_ssys_emp_role_emp ON ssys_employee_role(emp_id);
CREATE INDEX IF NOT EXISTS idx_ssys_emp_role_role ON ssys_employee_role(role_id);

-- ===== 方案元空间 · 员工-角色关联 =====
CREATE TABLE IF NOT EXISTS smeta_employee_role (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    solution_id TEXT NOT NULL,
    solution_version TEXT NOT NULL,
    emp_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    assigned_at TEXT NOT NULL,
    FOREIGN KEY (emp_id) REFERENCES smeta_employee(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES smeta_role(id) ON DELETE CASCADE,
    UNIQUE(solution_id, solution_version, emp_id, role_id)
);
CREATE INDEX IF NOT EXISTS idx_smeta_emp_role_emp ON smeta_employee_role(solution_id, solution_version, emp_id);
CREATE INDEX IF NOT EXISTS idx_smeta_emp_role_role ON smeta_employee_role(solution_id, solution_version, role_id);

-- ===== 仿真虚空间 · 员工-角色关联 =====
CREATE TABLE IF NOT EXISTS senv_employee_role (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    batch_no TEXT NOT NULL,
    emp_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    assigned_at TEXT NOT NULL,
    FOREIGN KEY (emp_id) REFERENCES senv_employee(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES senv_role(id) ON DELETE CASCADE,
    UNIQUE(task_id, batch_no, emp_id, role_id)
);
CREATE INDEX IF NOT EXISTS idx_senv_emp_role_emp ON senv_employee_role(task_id, batch_no, emp_id);
CREATE INDEX IF NOT EXISTS idx_senv_emp_role_role ON senv_employee_role(task_id, batch_no, role_id);

CREATE TABLE IF NOT EXISTS smeta_file (
    id TEXT PRIMARY KEY,
    file_name TEXT NOT NULL,
    version_no TEXT NOT NULL DEFAULT '1.0',
    file_category TEXT NOT NULL,
    solution_id TEXT NOT NULL,
    solution_name TEXT,
    physical_path TEXT,
    content_text TEXT,
    file_size INTEGER,
    mime_type TEXT,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_smeta_file_id ON smeta_file(id);
CREATE INDEX IF NOT EXISTS idx_smeta_file_solution ON smeta_file(solution_id);
CREATE INDEX IF NOT EXISTS idx_smeta_file_name ON smeta_file(file_name);
CREATE INDEX IF NOT EXISTS idx_smeta_file_category ON smeta_file(file_category);

CREATE TABLE IF NOT EXISTS smeta_solutions (
    id TEXT PRIMARY KEY,
    solution_name TEXT NOT NULL UNIQUE,
    major_version INTEGER NOT NULL DEFAULT 1,
    minor_version INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT '草稿',
    category TEXT,
    summary TEXT,
    key_purpose TEXT,
    key_objectives TEXT,
    key_measures TEXT,
    key_organizations TEXT,
    key_personnel TEXT,
    key_work_mechanism TEXT,
    key_work_content TEXT,
    key_constraints TEXT,
    key_risk_list TEXT,
    key_issue_list TEXT,
    key_notes TEXT,
    doc_main_docs TEXT,
    doc_attachments TEXT,
    doc_references TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_smeta_solutions_name ON smeta_solutions(solution_name);
CREATE INDEX IF NOT EXISTS idx_smeta_solutions_status ON smeta_solutions(status);
CREATE INDEX IF NOT EXISTS idx_smeta_solutions_category ON smeta_solutions(category);

CREATE TABLE IF NOT EXISTS smeta_solution_revision (
    solution_id TEXT NOT NULL,
    revision_no INTEGER NOT NULL,
    modifier TEXT NOT NULL,
    modified_at TEXT NOT NULL,
    change_summary TEXT NOT NULL,
    PRIMARY KEY (solution_id, revision_no)
);

CREATE INDEX IF NOT EXISTS idx_smeta_solution_revision_sid ON smeta_solution_revision(solution_id);

CREATE TABLE IF NOT EXISTS senv_solutions (
    id TEXT NOT NULL,
    solution_name TEXT NOT NULL,
    major_version INTEGER NOT NULL DEFAULT 1,
    minor_version INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT '草稿',
    category TEXT,
    summary TEXT,
    key_purpose TEXT,
    key_objectives TEXT,
    key_measures TEXT,
    key_organizations TEXT,
    key_personnel TEXT,
    key_work_mechanism TEXT,
    key_work_content TEXT,
    key_constraints TEXT,
    key_risk_list TEXT,
    key_issue_list TEXT,
    key_notes TEXT,
    doc_main_docs TEXT,
    doc_attachments TEXT,
    doc_references TEXT,
    simulation_task_id TEXT NOT NULL,
    simulation_task_batch TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (id, simulation_task_id, simulation_task_batch)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_senv_solutions_name_task ON senv_solutions(solution_name, simulation_task_id, simulation_task_batch);
CREATE INDEX IF NOT EXISTS idx_senv_solutions_status ON senv_solutions(status);
CREATE INDEX IF NOT EXISTS idx_senv_solutions_task ON senv_solutions(simulation_task_id, simulation_task_batch);

CREATE TABLE IF NOT EXISTS senv_solution_revision (
    solution_id TEXT NOT NULL,
    simulation_task_id TEXT NOT NULL,
    simulation_task_batch TEXT NOT NULL,
    revision_no INTEGER NOT NULL,
    modifier TEXT NOT NULL,
    modified_at TEXT NOT NULL,
    change_summary TEXT NOT NULL,
    PRIMARY KEY (solution_id, simulation_task_id, simulation_task_batch, revision_no)
);

CREATE INDEX IF NOT EXISTS idx_senv_solution_revision_sid ON senv_solution_revision(solution_id, simulation_task_id, simulation_task_batch);

-- ============================================================================
-- 知识空间 · 指标管理库 (前缀 km_)
-- ============================================================================

-- 指标分类分级目录表: 树形存储指标目录, 所有指标挂载至该分类树下
CREATE TABLE IF NOT EXISTS km_indicator_category (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id INTEGER NOT NULL DEFAULT 0,
    category_name TEXT NOT NULL,
    category_code TEXT NOT NULL UNIQUE,
    level INTEGER NOT NULL DEFAULT 1,
    sort INTEGER NOT NULL DEFAULT 0,
    scene_tag TEXT,
    remark TEXT,
    status INTEGER NOT NULL DEFAULT 1,
    create_time TEXT NOT NULL,
    update_time TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_km_category_parent ON km_indicator_category(parent_id);
CREATE INDEX IF NOT EXISTS idx_km_category_level ON km_indicator_category(level);
CREATE INDEX IF NOT EXISTS idx_km_category_scene ON km_indicator_category(scene_tag);
CREATE INDEX IF NOT EXISTS idx_km_category_status ON km_indicator_category(status);

-- 通用指标主表: 全局唯一基础指标, 跨模板复用, 含评估口径/阈值/标准
CREATE TABLE IF NOT EXISTS km_indicator_info (
    indicator_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    indicator_name TEXT NOT NULL,
    indicator_code TEXT NOT NULL UNIQUE,
    indicator_desc TEXT,
    data_type INTEGER NOT NULL DEFAULT 1,
    unit TEXT,
    standard_value TEXT,
    min_threshold REAL,
    max_threshold REAL,
    positive_flag INTEGER NOT NULL DEFAULT 1,
    default_score_rule_id INTEGER,
    tag_list TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    status INTEGER NOT NULL DEFAULT 1,
    create_user INTEGER,
    create_time TEXT NOT NULL,
    update_time TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_km_indicator_category ON km_indicator_info(category_id);
CREATE INDEX IF NOT EXISTS idx_km_indicator_data_type ON km_indicator_info(data_type);
CREATE INDEX IF NOT EXISTS idx_km_indicator_tag ON km_indicator_info(tag_list);
CREATE INDEX IF NOT EXISTS idx_km_indicator_status ON km_indicator_info(status);

-- 指标配套附件标准表: 存储指标打分细则/行业规范/示例文档
CREATE TABLE IF NOT EXISTS km_indicator_attach (
    attach_id INTEGER PRIMARY KEY AUTOINCREMENT,
    indicator_id INTEGER NOT NULL,
    file_name TEXT NOT NULL,
    file_url TEXT NOT NULL,
    attach_type INTEGER NOT NULL DEFAULT 1,
    create_time TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_km_attach_indicator ON km_indicator_attach(indicator_id);

-- ============================================================================
-- 结果空间 · 指标评估管理 (前缀 srlt_)
-- ============================================================================

-- 评估对象类型字典
CREATE TABLE IF NOT EXISTS srlt_object_type_dict (
    type_id INTEGER PRIMARY KEY,
    type_code TEXT NOT NULL UNIQUE,
    type_name TEXT NOT NULL,
    remark TEXT
);

-- 评估对象主表
CREATE TABLE IF NOT EXISTS srlt_evaluate_object (
    object_id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_type INTEGER NOT NULL,
    object_name TEXT NOT NULL,
    object_code TEXT NOT NULL,
    org_id INTEGER,
    ext_json TEXT,
    status INTEGER NOT NULL DEFAULT 1,
    create_time TEXT NOT NULL,
    UNIQUE (object_type, object_code)
);

CREATE INDEX IF NOT EXISTS idx_srlt_object_type ON srlt_evaluate_object(object_type);
CREATE INDEX IF NOT EXISTS idx_srlt_object_org ON srlt_evaluate_object(org_id);
CREATE INDEX IF NOT EXISTS idx_srlt_object_status ON srlt_evaluate_object(status);

-- 评估模板主表
CREATE TABLE IF NOT EXISTS srlt_evaluate_template (
    template_id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_name TEXT NOT NULL,
    template_code TEXT NOT NULL UNIQUE,
    scene_type INTEGER NOT NULL DEFAULT 1,
    template_desc TEXT,
    total_score INTEGER NOT NULL DEFAULT 100,
    is_preset INTEGER NOT NULL DEFAULT 0,
    version INTEGER NOT NULL DEFAULT 1,
    status INTEGER NOT NULL DEFAULT 1,
    create_user INTEGER,
    create_time TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_srlt_template_scene ON srlt_evaluate_template(scene_type);
CREATE INDEX IF NOT EXISTS idx_srlt_template_preset ON srlt_evaluate_template(is_preset);
CREATE INDEX IF NOT EXISTS idx_srlt_template_status ON srlt_evaluate_template(status);

-- 模板指标关联权重表
CREATE TABLE IF NOT EXISTS srlt_template_indicator_rel (
    rel_id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    indicator_id INTEGER NOT NULL,
    weight REAL NOT NULL DEFAULT 0,
    template_score_rule_id INTEGER,
    sort INTEGER NOT NULL DEFAULT 0,
    must_fill INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_srlt_tir_template ON srlt_template_indicator_rel(template_id, indicator_id);
CREATE INDEX IF NOT EXISTS idx_srlt_tir_indicator ON srlt_template_indicator_rel(indicator_id);

-- 指标计分规则表
CREATE TABLE IF NOT EXISTS srlt_score_rule (
    rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_name TEXT NOT NULL,
    calc_type INTEGER NOT NULL DEFAULT 1,
    rule_config_json TEXT,
    expression TEXT,
    remark TEXT
);

CREATE INDEX IF NOT EXISTS idx_srlt_rule_calc_type ON srlt_score_rule(calc_type);

-- 评估任务主表
CREATE TABLE IF NOT EXISTS srlt_evaluate_task (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    object_id INTEGER NOT NULL,
    task_name TEXT NOT NULL,
    evaluate_cycle TEXT,
    start_time TEXT,
    end_time TEXT,
    task_status INTEGER NOT NULL DEFAULT 0,
    total_score REAL,
    evaluate_conclusion TEXT,
    fill_user INTEGER,
    audit_user INTEGER,
    org_id INTEGER,
    create_time TEXT NOT NULL,
    finish_time TEXT
);

CREATE INDEX IF NOT EXISTS idx_srlt_task_template ON srlt_evaluate_task(template_id, object_id);
CREATE INDEX IF NOT EXISTS idx_srlt_task_cycle ON srlt_evaluate_task(evaluate_cycle);
CREATE INDEX IF NOT EXISTS idx_srlt_task_status ON srlt_evaluate_task(task_status);
CREATE INDEX IF NOT EXISTS idx_srlt_task_fill_user ON srlt_evaluate_task(fill_user);
CREATE INDEX IF NOT EXISTS idx_srlt_task_org ON srlt_evaluate_task(org_id);

-- 评估指标填报明细表
CREATE TABLE IF NOT EXISTS srlt_task_indicator_record (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    indicator_id INTEGER NOT NULL,
    raw_value TEXT,
    real_score REAL,
    score_rule_id INTEGER,
    fill_remark TEXT,
    attach_ids TEXT,
    create_time TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_srlt_record_task ON srlt_task_indicator_record(task_id, indicator_id);
CREATE INDEX IF NOT EXISTS idx_srlt_record_score ON srlt_task_indicator_record(real_score);

-- 评估结果快照宽表
CREATE TABLE IF NOT EXISTS srlt_evaluate_snapshot (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL UNIQUE,
    object_id INTEGER NOT NULL,
    template_id INTEGER NOT NULL,
    object_type INTEGER NOT NULL,
    total_score REAL,
    level_1_category_score TEXT,
    evaluate_rank TEXT,
    snapshot_time TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_srlt_snapshot_object ON srlt_evaluate_snapshot(object_id, template_id);
CREATE INDEX IF NOT EXISTS idx_srlt_snapshot_type ON srlt_evaluate_snapshot(object_type);
CREATE INDEX IF NOT EXISTS idx_srlt_snapshot_score ON srlt_evaluate_snapshot(total_score);
CREATE INDEX IF NOT EXISTS idx_srlt_snapshot_rank ON srlt_evaluate_snapshot(evaluate_rank);
CREATE INDEX IF NOT EXISTS idx_srlt_snapshot_time ON srlt_evaluate_snapshot(snapshot_time);

-- 评估对象类型字典预置数据
INSERT OR IGNORE INTO srlt_object_type_dict (type_id, type_code, type_name, remark) VALUES
    (1, 'org', '组织/企业', '组织或企业级评估主体'),
    (2, 'system', '软件系统', '软件系统评估主体'),
    (3, 'requirement', '软件需求', '软件需求评估主体'),
    (4, 'process', '业务流程', '业务流程评估主体'),
    (5, 'project', '项目', '项目评估主体'),
    (6, 'staff', '人员', '人员评估主体');
