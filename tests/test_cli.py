"""Tests for CLI commands."""

import tempfile
import warnings
from pathlib import Path

import pytest
from typer.testing import CliRunner

from prunejuice.cli import app


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture(autouse=True)
def suppress_resource_warnings():
    """Suppress ResourceWarnings for CLI tests due to SQLite finalizer timing."""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ResourceWarning)
        yield


def test_init_command_creates_project_structure(runner, temp_dir):
    """Test that init command creates the expected project structure."""
    # Change to temp directory
    import os

    original_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)

        # Run init command
        result = runner.invoke(app, ["init"])

        # Check command succeeded
        assert result.exit_code == 0
        assert "🧃 Initializing PruneJuice project:" in result.stdout
        assert "✅ Project initialized successfully!" in result.stdout

        # Check project structure was created
        prj_dir = temp_dir / ".prj"
        assert prj_dir.exists()
        assert prj_dir.is_dir()

        # Check subdirectories
        assert (prj_dir / "actions").exists()
        assert (prj_dir / "actions").is_dir()
        assert (prj_dir / "artifacts").exists()
        assert (prj_dir / "artifacts").is_dir()

        # Check database file
        assert (prj_dir / "prunejuice.db").exists()
        assert (prj_dir / "prunejuice.db").is_file()

    finally:
        os.chdir(original_cwd)


def test_init_command_database_initialization(runner, temp_dir):
    """Test that init command properly initializes the database."""
    import os
    import sqlite3

    original_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)

        # Run init command
        result = runner.invoke(app, ["init"])

        assert result.exit_code == 0
        assert "Database initialized" in result.stdout

        # Check database has correct tables
        db_path = temp_dir / ".prj" / "prunejuice.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = {row[0] for row in cursor.fetchall()}

            assert tables == {"event_log", "projects", "workspaces"}

    finally:
        os.chdir(original_cwd)


def test_init_command_creates_directories_if_exist(runner, temp_dir):
    """Test that init command works even if directories already exist."""
    import os

    original_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)

        # Pre-create the .prj directory
        prj_dir = temp_dir / ".prj"
        prj_dir.mkdir()
        (prj_dir / "actions").mkdir()

        # Run init command
        result = runner.invoke(app, ["init"])

        # Should still succeed
        assert result.exit_code == 0
        assert "✅ Project initialized successfully!" in result.stdout

        # All directories should still exist
        assert (prj_dir / "actions").exists()
        assert (prj_dir / "artifacts").exists()
        assert (prj_dir / "prunejuice.db").exists()

    finally:
        os.chdir(original_cwd)


def test_status_command_no_project(runner, temp_dir):
    """Test status command when no project exists."""
    import os

    original_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)

        # Run status command in empty directory
        result = runner.invoke(app, ["status"])

        assert result.exit_code == 1
        assert "❌ No PruneJuice project found in current directory" in result.stdout
        assert "Run 'prunejuice init' to initialize a project" in result.stdout

    finally:
        os.chdir(original_cwd)


def test_status_command_with_project(runner, temp_dir):
    """Test status command when project exists."""
    import os

    original_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)

        # First initialize a project
        init_result = runner.invoke(app, ["init", "Test Project"])
        assert init_result.exit_code == 0

        # Then check status
        result = runner.invoke(app, ["status"])

        assert result.exit_code == 0
        assert "✅ PruneJuice project found" in result.stdout
        assert "Project: Test Project (ID: 1)" in result.stdout
        assert f"Path: {temp_dir.resolve()}" in result.stdout
        assert "Slug: test-project" in result.stdout
        assert "No workspaces found" in result.stdout

    finally:
        os.chdir(original_cwd)


def test_status_command_with_git_project(runner, temp_dir):
    """Test status command with a Git project that includes workspaces."""
    import os

    from git import Repo

    original_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)

        # Initialize a git repository
        repo = Repo.init(temp_dir)
        test_file = temp_dir / "README.md"
        test_file.write_text("# Test Project")
        repo.index.add(["README.md"])
        repo.index.commit("Initial commit")

        # First initialize a project
        init_result = runner.invoke(app, ["init", "Git Test Project"])
        assert init_result.exit_code == 0

        # Then check status
        result = runner.invoke(app, ["status"])

        assert result.exit_code == 0
        assert "✅ PruneJuice project found" in result.stdout
        assert "Project: Git Test Project (ID: 1)" in result.stdout
        assert f"Path: {temp_dir.resolve()}" in result.stdout
        assert "Slug: git-test-project" in result.stdout
        assert "Git branch:" in result.stdout
        assert "Created:" in result.stdout
        assert "Workspaces (1):" in result.stdout
        assert "• main (ID: 1)" in result.stdout

    finally:
        os.chdir(original_cwd)


def test_status_command_project_exists_but_not_in_database(runner, temp_dir):
    """Test status command when .prj directory exists but project is not in database."""
    import os

    original_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)

        # Create .prj directory structure manually without proper database entry
        prj_dir = temp_dir / ".prj"
        prj_dir.mkdir()
        (prj_dir / "actions").mkdir()
        (prj_dir / "artifacts").mkdir()

        # Create database file but don't initialize it properly
        from prunejuice.core.database.manager import Database

        db = Database(prj_dir / "prunejuice.db")
        db.initialize()
        # Note: We don't insert any project data

        # Run status command
        result = runner.invoke(app, ["status"])

        assert result.exit_code == 1
        assert "❌ Project not found in database" in result.stdout
        assert "The .prj directory exists but no project is registered" in result.stdout

    finally:
        os.chdir(original_cwd)


def test_status_command_returns_project_model(runner, temp_dir):
    """Test that status command returns a Project model instance."""
    import os

    from prunejuice.core.models import Project

    original_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)

        # Initialize a project
        init_result = runner.invoke(app, ["init", "Model Test Project"])
        assert init_result.exit_code == 0

        # Import the CLI function directly to test return value
        from prunejuice.cli import status

        # Capture the returned project
        project = status()

        # Verify it's a Project instance with correct data
        assert isinstance(project, Project)
        assert project.name == "Model Test Project"
        assert project.slug == "model-test-project"
        assert project.path == str(temp_dir.resolve())
        assert project.id == 1

    finally:
        os.chdir(original_cwd)


def test_status_command_multiple_workspaces(runner, temp_dir):
    """Test status command displays multiple workspaces correctly."""
    import os
    import sqlite3

    from git import Repo

    original_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)

        # Initialize a git repository
        repo = Repo.init(temp_dir)
        test_file = temp_dir / "README.md"
        test_file.write_text("# Test Project")
        repo.index.add(["README.md"])
        repo.index.commit("Initial commit")

        # Initialize project
        init_result = runner.invoke(app, ["init", "Multi Workspace Project"])
        assert init_result.exit_code == 0

        # Manually add additional workspace to database for testing
        db_path = temp_dir / ".prj" / "prunejuice.db"
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                INSERT INTO workspaces
                (name, slug, project_id, path, git_branch, git_origin_branch, artifacts_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "feature-branch",
                    "feature-branch",
                    1,
                    str(temp_dir / "feature"),
                    "feature/awesome",
                    "origin/feature/awesome",
                    str(temp_dir / "artifacts/feature"),
                ),
            )
            conn.commit()

        # Check status
        result = runner.invoke(app, ["status"])

        assert result.exit_code == 0
        assert "✅ PruneJuice project found" in result.stdout
        assert "Project: Multi Workspace Project (ID: 1)" in result.stdout
        assert "Workspaces (2):" in result.stdout
        assert "• main (ID: 1)" in result.stdout
        assert "• feature-branch (ID: 2) - feature/awesome" in result.stdout

    finally:
        os.chdir(original_cwd)


def test_status_command_in_git_subdirectory(runner, temp_dir):
    """Test status command works from Git repository subdirectory."""
    import os

    from git import Repo

    original_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)

        # Initialize a git repository
        repo = Repo.init(temp_dir)
        test_file = temp_dir / "README.md"
        test_file.write_text("# Test Project")
        repo.index.add(["README.md"])
        repo.index.commit("Initial commit")

        # Initialize project from git root
        init_result = runner.invoke(app, ["init", "Subdir Test Project"])
        assert init_result.exit_code == 0

        # Create subdirectory and run status from there
        subdir = temp_dir / "src"
        subdir.mkdir()
        os.chdir(subdir)

        # Run status command from subdirectory
        result = runner.invoke(app, ["status"])

        assert result.exit_code == 0
        assert "✅ PruneJuice project found" in result.stdout
        assert "Project: Subdir Test Project (ID: 1)" in result.stdout
        assert f"Path: {temp_dir.resolve()}" in result.stdout  # Should show git root, not subdir

    finally:
        os.chdir(original_cwd)


def test_help_command(runner):
    """Test that help command works and shows available commands."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "init" in result.stdout
    assert "status" in result.stdout
    assert "Initialize a new PruneJuice project" in result.stdout
    assert "Show the current status of the PruneJuice project" in result.stdout


def test_init_command_help(runner):
    """Test help for init command."""
    result = runner.invoke(app, ["init", "--help"])

    assert result.exit_code == 0
    assert "Initialize a new PruneJuice project in the current directory" in result.stdout
    assert "NAME" in result.stdout
    assert "Name for the project" in result.stdout


def test_status_command_help(runner):
    """Test help for status command."""
    result = runner.invoke(app, ["status", "--help"])

    assert result.exit_code == 0
    assert "Show the current status of the PruneJuice project" in result.stdout


def test_database_error_handling(runner, temp_dir, monkeypatch):
    """Test that database errors are handled gracefully."""
    import os

    from prunejuice.core.database.manager import Database

    class MockDatabaseError(Exception):
        """Mock database error for testing."""

        def __init__(self):
            super().__init__("Mock database error")

    original_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)

        # Mock Database.initialize to raise an exception
        def mock_initialize(self):
            raise MockDatabaseError()

        monkeypatch.setattr(Database, "initialize", mock_initialize)

        # Run init command
        result = runner.invoke(app, ["init"])

        # Should exit with error
        assert result.exit_code == 1
        assert "Warning: Database initialization failed: Mock database error" in result.stdout

        # Directory structure should still be created
        prj_dir = temp_dir / ".prj"
        assert prj_dir.exists()
        assert (prj_dir / "actions").exists()
        assert (prj_dir / "artifacts").exists()

    finally:
        os.chdir(original_cwd)


def test_init_command_with_custom_name(runner, temp_dir):
    """Test init command with a custom project name."""
    import os
    import sqlite3

    original_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)

        # Run init command with custom name
        result = runner.invoke(app, ["init", "My Awesome Project"])

        # Check command succeeded
        assert result.exit_code == 0
        assert "🧃 Initializing PruneJuice project: My Awesome Project" in result.stdout
        assert "Project 'My Awesome Project' registered" in result.stdout
        assert "✅ Project initialized successfully!" in result.stdout

        # Check database has project with correct name and slug
        db_path = temp_dir / ".prj" / "prunejuice.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT name, slug FROM projects")
            row = cursor.fetchone()

            assert row is not None
            assert row[0] == "My Awesome Project"
            assert row[1] == "my-awesome-project"  # Slugified

    finally:
        os.chdir(original_cwd)


def test_init_command_default_name_from_directory(runner, temp_dir):
    """Test init command uses directory name when no name is provided."""
    import os
    import sqlite3

    # Create a subdirectory with a specific name
    project_dir = temp_dir / "test-project-dir"
    project_dir.mkdir()

    original_cwd = os.getcwd()
    try:
        os.chdir(project_dir)

        # Run init command without name
        result = runner.invoke(app, ["init"])

        # Check command succeeded
        assert result.exit_code == 0
        assert "🧃 Initializing PruneJuice project: test-project-dir" in result.stdout

        # Check database has project with directory name and correct worktree path
        db_path = project_dir / ".prj" / "prunejuice.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT name, slug, path, worktree_path FROM projects")
            row = cursor.fetchone()

            assert row is not None
            assert row[0] == "test-project-dir"
            assert row[1] == "test-project-dir"  # Already a valid slug
            assert Path(row[2]).resolve() == project_dir.resolve()  # Path should be the current directory
            assert (
                Path(row[3]).resolve() == (project_dir / ".worktrees").resolve()
            )  # Worktree path should be project_dir/.worktrees

    finally:
        os.chdir(original_cwd)


def test_init_command_in_git_repository(runner, temp_dir):
    """Test init command in a Git repository."""
    import os
    import sqlite3

    from git import Repo

    original_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)

        # Initialize a git repository
        repo = Repo.init(temp_dir)

        # Create a file and commit
        test_file = temp_dir / "README.md"
        test_file.write_text("# Test Project")
        repo.index.add(["README.md"])
        commit = repo.index.commit("Initial commit")

        # Run init command
        result = runner.invoke(app, ["init", "Git Project"])

        # Check command succeeded
        assert result.exit_code == 0
        assert "Git repository detected" in result.stdout
        assert "Using Git repository root:" in result.stdout

        # Check database has git information and correct paths
        db_path = temp_dir / ".prj" / "prunejuice.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT git_init_head_ref, git_init_branch, path, worktree_path FROM projects")
            row = cursor.fetchone()

            assert row is not None
            assert row[0] == commit.hexsha
            assert row[1] in ["main", "master"]
            assert Path(row[2]).resolve() == temp_dir.resolve()  # Project path should be the git root
            assert (
                Path(row[3]).resolve() == (temp_dir / ".worktrees").resolve()
            )  # Worktree path should be project_dir/.worktrees

    finally:
        os.chdir(original_cwd)


def test_init_command_in_git_subdirectory(runner, temp_dir):
    """Test init command in a subdirectory of a Git repository."""
    import os
    import sqlite3

    from git import Repo

    original_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)

        # Initialize a git repository
        repo = Repo.init(temp_dir)

        # Create a file and commit
        test_file = temp_dir / "README.md"
        test_file.write_text("# Test Project")
        repo.index.add(["README.md"])
        commit = repo.index.commit("Initial commit")

        # Create a subdirectory and run init from there
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        os.chdir(subdir)

        # Run init command from subdirectory
        result = runner.invoke(app, ["init", "Git Subdir Project"])

        # Check command succeeded
        assert result.exit_code == 0
        assert "Git repository detected" in result.stdout
        assert "Using Git repository root:" in result.stdout

        # Check that .prj directory was created in the Git root, not the subdirectory
        prj_dir = temp_dir / ".prj"  # Should be in Git root
        assert prj_dir.exists()
        assert (subdir / ".prj").exists() is False  # Should NOT be in subdirectory

        # Check database has git information and correct paths
        db_path = prj_dir / "prunejuice.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT git_init_head_ref, git_init_branch, path, worktree_path FROM projects")
            row = cursor.fetchone()

            assert row is not None
            assert row[0] == commit.hexsha
            assert row[1] in ["main", "master"]
            assert Path(row[2]).resolve() == temp_dir.resolve()  # Project path should be the git root, not subdir
            assert (
                Path(row[3]).resolve() == (temp_dir / ".worktrees").resolve()
            )  # Worktree path should be git_root/.worktrees

    finally:
        os.chdir(original_cwd)


def test_init_command_creates_workspace_event(runner, temp_dir):
    """Test that init command creates workspace-created event when initializing with Git."""
    import os
    import sqlite3

    from git import Repo

    original_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)

        # Initialize a git repository
        repo = Repo.init(temp_dir)
        test_file = temp_dir / "README.md"
        test_file.write_text("# Test Project")
        repo.index.add(["README.md"])
        repo.index.commit("Initial commit")

        # Run init command
        result = runner.invoke(app, ["init", "Event Test Project"])

        # Check command succeeded
        assert result.exit_code == 0

        # Check that workspace-created event was inserted
        db_path = temp_dir / ".prj" / "prunejuice.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(
                """
                SELECT action, project_id, workspace_id, status
                FROM event_log
                WHERE action = 'workspace-created'
                """
            )
            row = cursor.fetchone()

            assert row is not None
            assert row[0] == "workspace-created"  # action
            assert row[1] == 1  # project_id
            assert row[2] == 1  # workspace_id
            assert row[3] == "success"  # status

    finally:
        os.chdir(original_cwd)


def test_init_command_no_workspace_event_without_git(runner, temp_dir):
    """Test that init command does NOT create workspace-created event when no Git repository."""
    import os
    import sqlite3

    original_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)

        # Run init command without git repository
        result = runner.invoke(app, ["init", "No Git Project"])

        # Check command succeeded
        assert result.exit_code == 0

        # Check that NO workspace-created event was inserted
        db_path = temp_dir / ".prj" / "prunejuice.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(
                """
                SELECT COUNT(*)
                FROM event_log
                WHERE action = 'workspace-created'
                """
            )
            count = cursor.fetchone()[0]
            assert count == 0  # No workspace-created events should exist

    finally:
        os.chdir(original_cwd)


def test_init_command_special_characters_in_name(runner, temp_dir):
    """Test init command with special characters in project name."""
    import os
    import sqlite3

    original_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)

        # Run init command with special characters
        result = runner.invoke(app, ["init", "Test Project #123 (Beta)!"])

        # Check command succeeded
        assert result.exit_code == 0
        assert "Test Project #123 (Beta)!" in result.stdout

        # Check database has properly slugified name
        db_path = temp_dir / ".prj" / "prunejuice.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT name, slug FROM projects")
            row = cursor.fetchone()

            assert row is not None
            assert row[0] == "Test Project #123 (Beta)!"
            assert row[1] == "test-project-123-beta"  # Special chars removed and slugified

    finally:
        os.chdir(original_cwd)
