"""Tests for the Database adapter methods."""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from prunejuice.core.database.manager import Database


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    db = Database(db_path)
    db.initialize()

    yield db

    # Cleanup
    db_path.unlink(missing_ok=True)


def test_database_initialization(temp_db):
    """Test that database initializes with correct schema."""
    with temp_db.connection() as conn:
        # Check tables exist
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = {row[0] for row in cursor.fetchall()}

        assert tables == {"event_log", "projects", "workspaces"}


def test_insert_project(temp_db):
    """Test inserting a project."""
    project_id = temp_db.insert_project(
        name="Test Project",
        slug="test-project",
        path="/path/to/project",
        worktree_path="/path/to/worktree",
        git_init_head_ref="refs/heads/main",
        git_init_branch="main",
    )

    assert project_id == 1

    # Verify the data was inserted
    with temp_db.connection() as conn:
        cursor = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()

        assert row is not None
        assert row[1] == "Test Project"  # name
        assert row[2] == "test-project"  # slug
        assert row[3] == "/path/to/project"  # path
        assert row[4] == "/path/to/worktree"  # worktree_path
        assert row[5] == "refs/heads/main"  # git_init_head_ref
        assert row[6] == "main"  # git_init_branch


def test_insert_project_minimal(temp_db):
    """Test inserting a project with minimal fields."""
    project_id = temp_db.insert_project(
        name="Minimal Project", slug="minimal", path="/minimal", worktree_path="/minimal/worktree"
    )

    assert project_id == 1

    # Verify optional fields are NULL
    with temp_db.connection() as conn:
        cursor = conn.execute("SELECT git_init_head_ref, git_init_branch FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()

        assert row[0] is None  # git_init_head_ref
        assert row[1] is None  # git_init_branch


def test_insert_workspace(temp_db):
    """Test inserting a workspace."""
    # First insert a project
    project_id = temp_db.insert_project(
        name="Test Project", slug="test-project", path="/project", worktree_path="/project/worktree"
    )

    # Then insert a workspace
    workspace_id = temp_db.insert_workspace(
        name="Feature Branch",
        slug="feature-branch",
        project_id=project_id,
        path="/project/worktree/feature",
        git_branch="feature/new-feature",
        git_origin_branch="origin/feature/new-feature",
        artifacts_path="/project/artifacts/feature",
    )

    assert workspace_id == 1

    # Verify the data was inserted
    with temp_db.connection() as conn:
        cursor = conn.execute("SELECT * FROM workspaces WHERE id = ?", (workspace_id,))
        row = cursor.fetchone()

        assert row is not None
        assert row[1] == "Feature Branch"  # name
        assert row[2] == "feature-branch"  # slug
        assert row[3] == project_id  # project_id
        assert row[4] == "/project/worktree/feature"  # path
        assert row[5] == "feature/new-feature"  # git_branch
        assert row[6] == "origin/feature/new-feature"  # git_origin_branch
        assert row[7] == "/project/artifacts/feature"  # artifacts_path


def test_insert_workspace_minimal(temp_db):
    """Test inserting a workspace with minimal fields."""
    # First insert a project
    project_id = temp_db.insert_project(
        name="Test Project", slug="test-project", path="/project", worktree_path="/project/worktree"
    )

    # Insert workspace without artifacts_path
    workspace_id = temp_db.insert_workspace(
        name="Main Branch",
        slug="main",
        project_id=project_id,
        path="/project/worktree/main",
        git_branch="main",
        git_origin_branch="origin/main",
    )

    assert workspace_id == 1

    # Verify artifacts_path is NULL
    with temp_db.connection() as conn:
        cursor = conn.execute("SELECT artifacts_path FROM workspaces WHERE id = ?", (workspace_id,))
        row = cursor.fetchone()

        assert row[0] is None  # artifacts_path


def test_insert_event_with_workspace(temp_db):
    """Test inserting an event with workspace."""
    # Create project and workspace
    project_id = temp_db.insert_project(
        name="Test Project", slug="test-project", path="/project", worktree_path="/project/worktree"
    )

    workspace_id = temp_db.insert_workspace(
        name="Feature Branch",
        slug="feature",
        project_id=project_id,
        path="/project/worktree/feature",
        git_branch="feature/new",
        git_origin_branch="origin/feature/new",
    )

    # Insert event
    event_id = temp_db.insert_event(action="build", project_id=project_id, workspace_id=workspace_id, status="success")

    assert event_id == 1

    # Verify the data
    with temp_db.connection() as conn:
        cursor = conn.execute("SELECT * FROM event_log WHERE id = ?", (event_id,))
        row = cursor.fetchone()

        assert row is not None
        assert row[1] == "build"  # action
        assert row[2] == project_id  # project_id
        assert row[3] == workspace_id  # workspace_id
        assert row[5] == "success"  # status


def test_insert_event_without_workspace(temp_db):
    """Test inserting an event without workspace."""
    # Create project
    project_id = temp_db.insert_project(
        name="Test Project", slug="test-project", path="/project", worktree_path="/project/worktree"
    )

    # Insert event without workspace
    event_id = temp_db.insert_event(action="init", project_id=project_id, status="completed")

    assert event_id == 1

    # Verify the data
    with temp_db.connection() as conn:
        cursor = conn.execute("SELECT * FROM event_log WHERE id = ?", (event_id,))
        row = cursor.fetchone()

        assert row is not None
        assert row[1] == "init"  # action
        assert row[2] == project_id  # project_id
        assert row[3] is None  # workspace_id
        assert row[5] == "completed"  # status


def test_foreign_key_constraints(temp_db):
    """Test that foreign key constraints are enforced."""
    # Try to insert event with non-existent project_id
    with pytest.raises(sqlite3.IntegrityError):
        temp_db.insert_event(
            action="test",
            project_id=999,  # Non-existent
            status="failed",
        )

    # Try to insert workspace with non-existent project_id
    with pytest.raises(sqlite3.IntegrityError):
        temp_db.insert_workspace(
            name="Test",
            slug="test",
            project_id=999,  # Non-existent
            path="/test",
            git_branch="test",
            git_origin_branch="origin/test",
        )
