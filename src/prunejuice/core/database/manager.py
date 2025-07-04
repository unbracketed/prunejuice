"""SQLite database layer with secure parameter binding."""

import logging
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..models import Event

logger = logging.getLogger(__name__)


class Database:
    """SQLite database manager with secure parameter binding."""

    def __init__(self, db_path: Path):
        """Initialize database manager."""
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()

    def initialize(self) -> None:
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
        timestamp: Optional[str] = None,
    ) -> int:
        """Create new event with proper parameter binding."""
        # Use provided timestamp or current datetime
        if timestamp is None:
            timestamp = datetime.now().isoformat()

        with self.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO event_log
                (action, project_id, workspace_id, status, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (action, project_id, workspace_id, status, timestamp),
            )
            conn.commit()
            if cursor.lastrowid is None:
                raise ValueError("Failed to insert event - no ID returned")
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
            if cursor.lastrowid is None:
                raise ValueError("Failed to insert project - no ID returned")
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
            if cursor.lastrowid is None:
                raise ValueError("Failed to insert workspace - no ID returned")
            return cursor.lastrowid

    def get_project_by_path(self, path: str) -> Optional[dict]:
        """Lookup project by directory path."""
        with self.connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, name, slug, path, worktree_path, git_init_head_ref, git_init_branch, date_created
                FROM projects
                WHERE path = ?
                """,
                (path,),
            )
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "name": row[1],
                    "slug": row[2],
                    "path": row[3],
                    "worktree_path": row[4],
                    "git_init_head_ref": row[5],
                    "git_init_branch": row[6],
                    "date_created": row[7],
                }
            return None

    def get_workspaces_by_project_id(self, project_id: int) -> list[dict]:
        """Get all workspaces for a project."""
        with self.connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, name, slug, project_id, path, git_branch, git_origin_branch, artifacts_path, date_created
                FROM workspaces
                WHERE project_id = ?
                ORDER BY date_created
                """,
                (project_id,),
            )
            rows = cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "slug": row[2],
                    "project_id": row[3],
                    "path": row[4],
                    "git_branch": row[5],
                    "git_origin_branch": row[6],
                    "artifacts_path": row[7],
                    "date_created": row[8],
                }
                for row in rows
            ]

    def get_events_by_project_id(self, project_id: int) -> list[Event]:
        """Get all events for a project, ordered by timestamp DESC (most recent first)."""
        with self.connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, action, project_id, workspace_id, timestamp, status
                FROM event_log
                WHERE project_id = ?
                ORDER BY timestamp DESC
                """,
                (project_id,),
            )
            rows = cursor.fetchall()
            return [
                Event(
                    id=row[0],
                    action=row[1],
                    project_id=row[2],
                    workspace_id=row[3],
                    timestamp=row[4],
                    status=row[5],
                )
                for row in rows
            ]
