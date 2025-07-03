-- SQLite schema generated from database.dbml

-- Projects table
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name VARCHAR NOT NULL,
    slug VARCHAR NOT NULL,
    path VARCHAR NOT NULL,
    worktree_path VARCHAR NOT NULL,
    git_init_head_ref VARCHAR,
    git_init_branch VARCHAR,
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Workspaces table
CREATE TABLE workspaces (
    id INTEGER PRIMARY KEY,
    name VARCHAR NOT NULL,
    slug VARCHAR NOT NULL,
    project_id INTEGER NOT NULL,
    path VARCHAR NOT NULL,
    git_branch VARCHAR NOT NULL,
    git_origin_branch VARCHAR NOT NULL,
    artifacts_path VARCHAR,
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- Event log table
CREATE TABLE event_log (
    id INTEGER PRIMARY KEY,
    action VARCHAR NOT NULL,
    project_id INTEGER NOT NULL,
    workspace_id INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
);
