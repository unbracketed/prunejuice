"""Tests for the Database adapter methods."""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from prunejuice.core.database.manager import Database
from prunejuice.core.models import Event


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


def test_get_project_by_path(temp_db):
    """Test retrieving a project by path."""
    # Insert a project
    project_id = temp_db.insert_project(
        name="Test Project",
        slug="test-project",
        path="/path/to/project",
        worktree_path="/path/to/worktree",
        git_init_head_ref="refs/heads/main",
        git_init_branch="main",
    )

    # Retrieve by path
    project = temp_db.get_project_by_path("/path/to/project")

    assert project is not None
    assert project["id"] == project_id
    assert project["name"] == "Test Project"
    assert project["slug"] == "test-project"
    assert project["path"] == "/path/to/project"
    assert project["worktree_path"] == "/path/to/worktree"
    assert project["git_init_head_ref"] == "refs/heads/main"
    assert project["git_init_branch"] == "main"
    assert project["date_created"] is not None


def test_get_project_by_path_not_found(temp_db):
    """Test retrieving a project by path when it doesn't exist."""
    project = temp_db.get_project_by_path("/nonexistent/path")
    assert project is None


def test_get_workspaces_by_project_id(temp_db):
    """Test retrieving workspaces by project ID."""
    # Insert a project
    project_id = temp_db.insert_project(
        name="Test Project",
        slug="test-project",
        path="/path/to/project",
        worktree_path="/path/to/worktree",
    )

    # Insert multiple workspaces
    workspace1_id = temp_db.insert_workspace(
        name="Main Branch",
        slug="main",
        project_id=project_id,
        path="/project/worktree/main",
        git_branch="main",
        git_origin_branch="origin/main",
    )

    workspace2_id = temp_db.insert_workspace(
        name="Feature Branch",
        slug="feature",
        project_id=project_id,
        path="/project/worktree/feature",
        git_branch="feature/new-feature",
        git_origin_branch="origin/feature/new-feature",
        artifacts_path="/project/artifacts/feature",
    )

    # Retrieve workspaces
    workspaces = temp_db.get_workspaces_by_project_id(project_id)

    assert len(workspaces) == 2

    # Check first workspace (should be ordered by date_created)
    workspace1 = workspaces[0]
    assert workspace1["id"] == workspace1_id
    assert workspace1["name"] == "Main Branch"
    assert workspace1["slug"] == "main"
    assert workspace1["project_id"] == project_id
    assert workspace1["path"] == "/project/worktree/main"
    assert workspace1["git_branch"] == "main"
    assert workspace1["git_origin_branch"] == "origin/main"
    assert workspace1["artifacts_path"] is None
    assert workspace1["date_created"] is not None

    # Check second workspace
    workspace2 = workspaces[1]
    assert workspace2["id"] == workspace2_id
    assert workspace2["name"] == "Feature Branch"
    assert workspace2["slug"] == "feature"
    assert workspace2["project_id"] == project_id
    assert workspace2["path"] == "/project/worktree/feature"
    assert workspace2["git_branch"] == "feature/new-feature"
    assert workspace2["git_origin_branch"] == "origin/feature/new-feature"
    assert workspace2["artifacts_path"] == "/project/artifacts/feature"
    assert workspace2["date_created"] is not None


def test_get_workspaces_by_project_id_empty(temp_db):
    """Test retrieving workspaces when none exist for a project."""
    # Insert a project
    project_id = temp_db.insert_project(
        name="Test Project",
        slug="test-project",
        path="/path/to/project",
        worktree_path="/path/to/worktree",
    )

    # Retrieve workspaces (should be empty)
    workspaces = temp_db.get_workspaces_by_project_id(project_id)
    assert workspaces == []


def test_get_workspaces_by_project_id_nonexistent(temp_db):
    """Test retrieving workspaces for a nonexistent project."""
    workspaces = temp_db.get_workspaces_by_project_id(999)
    assert workspaces == []


def test_get_events_by_project_id(temp_db):
    """Test retrieving events by project ID ordered by timestamp DESC."""
    # Insert a project
    project_id = temp_db.insert_project(
        name="Test Project",
        slug="test-project",
        path="/path/to/project",
        worktree_path="/path/to/worktree",
    )

    # Insert another project to test filtering
    other_project_id = temp_db.insert_project(
        name="Other Project",
        slug="other-project",
        path="/path/to/other",
        worktree_path="/path/to/other/worktree",
    )

    # Insert a workspace
    workspace_id = temp_db.insert_workspace(
        name="Feature Branch",
        slug="feature",
        project_id=project_id,
        path="/project/worktree/feature",
        git_branch="feature/new",
        git_origin_branch="origin/feature/new",
    )

    # Insert events for the test project with explicit timestamps
    event1_id = temp_db.insert_event(
        action="init", project_id=project_id, status="completed", timestamp="2024-01-01 10:00:00"
    )

    event2_id = temp_db.insert_event(
        action="build",
        project_id=project_id,
        workspace_id=workspace_id,
        status="success",
        timestamp="2024-01-01 10:00:30",
    )

    event3_id = temp_db.insert_event(
        action="test",
        project_id=project_id,
        workspace_id=workspace_id,
        status="failed",
        timestamp="2024-01-01 10:01:00",
    )

    # Insert an event for the other project (should not appear in results)
    temp_db.insert_event(action="deploy", project_id=other_project_id, status="success")

    # Retrieve events
    events = temp_db.get_events_by_project_id(project_id)

    assert len(events) == 3
    assert all(isinstance(event, Event) for event in events)

    # Check events are ordered by timestamp DESC (most recent first)
    # event3 should be first (most recent)
    assert events[0].id == event3_id
    assert events[0].action == "test"
    assert events[0].project_id == project_id
    assert events[0].workspace_id == workspace_id
    assert events[0].status == "failed"
    assert events[0].timestamp is not None

    # event2 should be second
    assert events[1].id == event2_id
    assert events[1].action == "build"
    assert events[1].project_id == project_id
    assert events[1].workspace_id == workspace_id
    assert events[1].status == "success"
    assert events[1].timestamp is not None

    # event1 should be last (oldest)
    assert events[2].id == event1_id
    assert events[2].action == "init"
    assert events[2].project_id == project_id
    assert events[2].workspace_id is None
    assert events[2].status == "completed"
    assert events[2].timestamp is not None

    # Verify timestamps are in descending order
    for i in range(len(events) - 1):
        assert events[i].timestamp >= events[i + 1].timestamp


def test_get_events_by_project_id_empty(temp_db):
    """Test retrieving events when none exist for a project."""
    # Insert a project
    project_id = temp_db.insert_project(
        name="Test Project",
        slug="test-project",
        path="/path/to/project",
        worktree_path="/path/to/worktree",
    )

    # Retrieve events (should be empty)
    events = temp_db.get_events_by_project_id(project_id)
    assert events == []


def test_get_events_by_project_id_nonexistent(temp_db):
    """Test retrieving events for a nonexistent project."""
    events = temp_db.get_events_by_project_id(999)
    assert events == []
