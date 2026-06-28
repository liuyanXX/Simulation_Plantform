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

CREATE TABLE IF NOT EXISTS evaluation_indices (
    index_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    evaluation_method TEXT NOT NULL,
    agent_ids TEXT NOT NULL,
    index_type TEXT NOT NULL,
    index_level TEXT NOT NULL,
    parent_id TEXT,
    weight REAL NOT NULL DEFAULT 1.0,
    score_range TEXT NOT NULL DEFAULT '(0, 100)',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
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
