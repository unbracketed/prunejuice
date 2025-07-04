"""Tests for the core operations module."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from prunejuice.core.models import Project, Workspace
from prunejuice.core.operations import WorkspaceService


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
