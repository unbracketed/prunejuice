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

        assert result.exit_code == 0
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
        init_result = runner.invoke(app, ["init"])
        assert init_result.exit_code == 0

        # Then check status
        result = runner.invoke(app, ["status"])

        assert result.exit_code == 0
        assert "✅ PruneJuice project found" in result.stdout
        assert "Project directory:" in result.stdout
        assert ".prj" in result.stdout

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

        # Check database has project with directory name
        db_path = project_dir / ".prj" / "prunejuice.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT name, slug FROM projects")
            row = cursor.fetchone()

            assert row is not None
            assert row[0] == "test-project-dir"
            assert row[1] == "test-project-dir"  # Already a valid slug

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

        # Check database has git information
        db_path = temp_dir / ".prj" / "prunejuice.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT git_init_head_ref, git_init_branch FROM projects")
            row = cursor.fetchone()

            assert row is not None
            assert row[0] == commit.hexsha
            assert row[1] in ["main", "master"]

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
