"""Tests for the core operations module."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from prunejuice.core.models import Event, Project, Workspace
from prunejuice.core.operations import EventService, WorkspaceService


@pytest.fixture
def mock_database():
    """Mock Database instance."""
    db = Mock()
    db.insert_workspace.return_value = 123
    db.insert_event.return_value = None
    return db


@pytest.fixture
def mock_git_manager():
    """Mock GitManager instance."""
    git = Mock()
    git.create_worktree.return_value = {"status": "success", "output": "/tmp/test_worktree"}
    return git


@pytest.fixture
def mock_project():
    """Mock Project instance."""
    return Project(
        id=1,
        name="Test Project",
        slug="test-project",
        path="/tmp/test_project",
        worktree_path="/tmp/test_project_worktrees",
        git_init_head_ref="main",
        git_init_branch="main",
    )


@pytest.fixture
def workspace_service(mock_database, mock_git_manager, mock_project):
    """WorkspaceService instance with mocked dependencies."""
    return WorkspaceService(db=mock_database, git_interace=mock_git_manager, project=mock_project)


def test_create_workspace_basic(workspace_service, mock_database, mock_git_manager, mock_project):
    """Test basic workspace creation."""
    # Act
    result = workspace_service.create_workspace("Test Workspace", branch_name=None)

    # Assert
    assert isinstance(result, Workspace)
    assert result.id == 123
    assert result.name == "Test Workspace"
    assert result.slug == "test-workspace"
    assert result.project_id == 1
    assert result.path == "/tmp/test_worktree"
    assert result.git_branch == "test-workspace"
    assert result.git_origin_branch == ""

    # Verify database calls
    mock_database.insert_workspace.assert_called_once_with(
        "Test Workspace",
        "test-workspace",
        1,
        "/tmp/test_worktree",
        "test-workspace",
        "",
        str(Path(mock_project.path) / ".prj/artifacts" / "test-workspace"),
    )

    mock_database.insert_event.assert_called_once_with(
        action="workspace-created", project_id=1, workspace_id=123, status="success"
    )


def test_create_workspace_with_custom_branch(workspace_service, mock_database, mock_git_manager):
    """Test workspace creation with custom branch name."""
    # Act
    result = workspace_service.create_workspace("Feature Workspace", branch_name="feature/new-feature")

    # Assert
    assert result.git_branch == "feature/new-feature"

    # Verify git worktree creation
    mock_git_manager.create_worktree.assert_called_once_with(Path("/tmp/test_project_worktrees"), "feature/new-feature")


def test_create_workspace_with_base_branch(workspace_service, mock_database, mock_git_manager):
    """Test workspace creation with base branch."""
    # Act
    result = workspace_service.create_workspace(
        "Feature Workspace", branch_name="feature/new-feature", base_branch="develop"
    )

    # Assert
    assert result.git_origin_branch == "develop"

    # Verify git worktree creation with base branch
    mock_git_manager.create_worktree.assert_called_once_with(
        Path("/tmp/test_project_worktrees"), "feature/new-feature", base_branch="develop"
    )


def test_create_workspace_branch_defaults_to_slug(workspace_service, mock_database, mock_git_manager):
    """Test that branch name defaults to workspace slug when not provided."""
    # Act
    result = workspace_service.create_workspace("My Cool Feature", branch_name=None)

    # Assert
    assert result.git_branch == "my-cool-feature"

    # Verify git worktree creation uses slug as branch name
    mock_git_manager.create_worktree.assert_called_once_with(Path("/tmp/test_project_worktrees"), "my-cool-feature")


def test_list_workspaces_success(workspace_service, mock_database, mock_project):
    """Test successful listing of workspaces."""
    # Arrange - mock database returns dictionaries
    mock_workspaces_data = [
        {
            "id": 1,
            "name": "Workspace 1",
            "slug": "workspace-1",
            "project_id": 1,
            "path": "/tmp/workspace1",
            "git_branch": "workspace-1",
            "git_origin_branch": "main",
            "artifacts_path": "/tmp/artifacts/workspace-1",
        },
        {
            "id": 2,
            "name": "Workspace 2",
            "slug": "workspace-2",
            "project_id": 1,
            "path": "/tmp/workspace2",
            "git_branch": "feature/workspace-2",
            "git_origin_branch": "develop",
            "artifacts_path": "/tmp/artifacts/workspace-2",
        },
    ]
    mock_database.get_workspaces_by_project_id.return_value = mock_workspaces_data

    # Act
    result = workspace_service.list_workspaces()

    # Assert
    assert len(result) == 2
    assert all(isinstance(w, Workspace) for w in result)
    assert result[0].name == "Workspace 1"
    assert result[1].name == "Workspace 2"
    assert result[0].id == 1
    assert result[1].id == 2
    mock_database.get_workspaces_by_project_id.assert_called_once_with(mock_project.id)


def test_list_workspaces_empty_list(workspace_service, mock_database, mock_project):
    """Test listing workspaces when no workspaces exist."""
    # Arrange
    mock_database.get_workspaces_by_project_id.return_value = []

    # Act
    result = workspace_service.list_workspaces()

    # Assert
    assert result == []
    mock_database.get_workspaces_by_project_id.assert_called_once_with(mock_project.id)


def test_list_workspaces_returns_none(workspace_service, mock_database, mock_project):
    """Test listing workspaces when database returns None."""
    # Arrange
    mock_database.get_workspaces_by_project_id.return_value = None

    # Act
    result = workspace_service.list_workspaces()

    # Assert
    assert result is None
    mock_database.get_workspaces_by_project_id.assert_called_once_with(mock_project.id)


@pytest.fixture
def event_service(mock_database, mock_project):
    """EventService instance with mocked dependencies."""
    return EventService(db=mock_database, project=mock_project)


@pytest.fixture
def mock_workspace():
    """Mock Workspace instance."""
    return Workspace(
        id=42,
        name="Test Workspace",
        slug="test-workspace",
        project_id=1,
        path="/tmp/test_workspace",
        git_branch="test-branch",
        git_origin_branch="main",
        artifacts_path="/tmp/artifacts/test-workspace",
    )


def test_event_service_add_event_without_workspace(event_service, mock_database, mock_project):
    """Test adding an event without workspace association."""
    mock_database.insert_event.return_value = 999

    result = event_service.add_event(action="project-initialized", status="success")

    assert isinstance(result, Event)
    assert result.id == 999
    assert result.action == "project-initialized"
    assert result.status == "success"
    assert result.project_id == 1
    assert result.workspace_id is None

    mock_database.insert_event.assert_called_once_with(
        action="project-initialized", project_id=1, workspace_id=None, status="success"
    )


def test_event_service_add_event_with_workspace(event_service, mock_database, mock_project, mock_workspace):
    """Test adding an event with workspace association."""
    mock_database.insert_event.return_value = 1000

    result = event_service.add_event(action="build-started", status="pending", workspace=mock_workspace)

    assert isinstance(result, Event)
    assert result.id == 1000
    assert result.action == "build-started"
    assert result.status == "pending"
    assert result.project_id == 1
    assert result.workspace_id == 42

    mock_database.insert_event.assert_called_once_with(
        action="build-started", project_id=1, workspace_id=42, status="pending"
    )


def test_event_service_add_event_project_id_not_set(mock_database):
    """Test adding event when project ID is not set raises ValueError."""
    project_without_id = Project(name="Test", slug="test", path="/tmp/test", worktree_path="/tmp/test_worktrees")
    service = EventService(db=mock_database, project=project_without_id)

    with pytest.raises(ValueError, match="Project ID is not set"):
        service.add_event(action="test", status="success")


def test_event_service_list_events_all_project_events(event_service, mock_database, mock_project):
    """Test listing all events for a project."""
    mock_events = [
        Event(id=1, action="project-initialized", project_id=1, status="success"),
        Event(id=2, action="workspace-created", project_id=1, workspace_id=10, status="success"),
        Event(id=3, action="build-started", project_id=1, workspace_id=11, status="pending"),
    ]
    mock_database.get_events_by_project_id.return_value = mock_events

    result = event_service.list_events()

    assert result == mock_events
    assert len(result) == 3
    mock_database.get_events_by_project_id.assert_called_once_with(1)


def test_event_service_list_events_by_workspace(event_service, mock_database, mock_workspace):
    """Test listing events filtered by workspace."""
    mock_events = [
        Event(id=10, action="workspace-created", project_id=1, workspace_id=42, status="success"),
        Event(id=11, action="build-started", project_id=1, workspace_id=42, status="pending"),
        Event(id=12, action="build-completed", project_id=1, workspace_id=42, status="success"),
    ]
    mock_database.get_events_by_workspace_id.return_value = mock_events

    result = event_service.list_events(workspace=mock_workspace)

    assert result == mock_events
    assert len(result) == 3
    assert all(e.workspace_id == 42 for e in result)
    mock_database.get_events_by_workspace_id.assert_called_once_with(42)


def test_event_service_list_events_workspace_without_id(event_service, mock_database):
    """Test listing events with workspace that has no ID raises ValueError."""
    workspace_without_id = Workspace(
        name="Test", slug="test", project_id=1, path="/tmp/test", git_branch="test", git_origin_branch="main"
    )

    with pytest.raises(ValueError, match="Workspace ID is not set"):
        event_service.list_events(workspace=workspace_without_id)


def test_event_service_list_events_project_id_not_set(mock_database):
    """Test listing events when project ID is not set raises ValueError."""
    project_without_id = Project(name="Test", slug="test", path="/tmp/test", worktree_path="/tmp/test_worktrees")
    service = EventService(db=mock_database, project=project_without_id)

    with pytest.raises(ValueError, match="Project ID is not set"):
        service.list_events()


def test_event_service_list_events_empty_list(event_service, mock_database):
    """Test listing events when no events exist returns empty list."""
    mock_database.get_events_by_project_id.return_value = []

    result = event_service.list_events()

    assert result == []
    mock_database.get_events_by_project_id.assert_called_once()


def test_event_service_add_event_different_statuses(event_service, mock_database):
    """Test adding events with different status values."""
    statuses = ["success", "failure", "pending", "warning", "error"]
    mock_database.insert_event.side_effect = range(100, 105)

    for i, status in enumerate(statuses):
        result = event_service.add_event(action=f"test-{status}", status=status)
        assert result.status == status
        assert result.id == 100 + i


def test_event_service_add_event_various_actions(event_service, mock_database, mock_workspace):
    """Test adding events with various action types."""
    actions = [
        "workspace-created",
        "workspace-deleted",
        "build-started",
        "build-completed",
        "test-started",
        "test-completed",
        "deploy-initiated",
        "deploy-completed",
    ]
    mock_database.insert_event.side_effect = range(200, 208)

    for i, action in enumerate(actions):
        result = event_service.add_event(
            action=action, status="success", workspace=mock_workspace if "workspace" in action or i % 2 == 0 else None
        )
        assert result.action == action
        assert result.id == 200 + i
