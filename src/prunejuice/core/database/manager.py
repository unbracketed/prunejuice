"""SQLite database layer with secure parameter binding."""

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class Database:
    """SQLite database manager with secure parameter binding."""

    def __init__(self, db_path: Path):
        """Initialize database manager."""
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()

    def initialize(self):
        """Initialize database with schema."""
        schema_path = Path(__file__).parent / "schema.sql"
        with self.connection() as conn:
            with open(schema_path) as f:
                conn.executescript(f.read())
            conn.commit()

    def insert_event(
        self,
        action: str,
        project_id: int,
        status: str,
        workspace_id: Optional[int] = None,
    ) -> int:
        """Create new event with proper parameter binding."""
        with self.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO event_log
                (action, project_id, workspace_id, status)
                VALUES (?, ?, ?, ?)
                """,
                (action, project_id, workspace_id, status),
            )
            conn.commit()
            return cursor.lastrowid

    def insert_project(
        self,
        name: str,
        slug: str,
        path: str,
        worktree_path: str,
        git_init_head_ref: Optional[str] = None,
        git_init_branch: Optional[str] = None,
    ) -> int:
        """Create new project with proper parameter binding."""
        with self.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO projects
                (name, slug, path, worktree_path, git_init_head_ref, git_init_branch)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (name, slug, path, worktree_path, git_init_head_ref, git_init_branch),
            )
            conn.commit()
            return cursor.lastrowid

    def insert_workspace(
        self,
        name: str,
        slug: str,
        project_id: int,
        path: str,
        git_branch: str,
        git_origin_branch: str,
        artifacts_path: Optional[str] = None,
    ) -> int:
        """Create new workspace with proper parameter binding."""
        with self.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO workspaces
                (name, slug, project_id, path, git_branch, git_origin_branch, artifacts_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (name, slug, project_id, path, git_branch, git_origin_branch, artifacts_path),
            )
            conn.commit()
            return cursor.lastrowid
