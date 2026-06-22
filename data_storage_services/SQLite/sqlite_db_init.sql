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
    metadata TEXT
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

CREATE TABLE IF NOT EXISTS worker_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    assigned_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS org_workers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id TEXT NOT NULL,
    employee_id TEXT NOT NULL
);