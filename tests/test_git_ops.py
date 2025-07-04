"""Tests for GitManager class."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, PropertyMock, patch

import pytest
from git import InvalidGitRepositoryError, Repo

from prunejuice.core.git_ops import GitManager


@pytest.fixture
def temp_git_repo():
    """Create a temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir)
        # Initialize a real git repo
        repo = Repo.init(repo_path)
        yield repo_path, repo
        # Clean up repo
        repo.close()


@pytest.fixture
def temp_non_git_dir():
    """Create a temporary directory that is not a git repository."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


class TestGitManager:
    """Test cases for GitManager class."""

    def test_init(self, temp_git_repo):
        """Test GitManager initialization."""
        repo_path, _ = temp_git_repo
        git_manager = GitManager(repo_path)

        try:
            assert git_manager.project_path == repo_path
            assert git_manager._repo is not None
        finally:
            # Clean up
            git_manager.close()

    def test_get_repo_success(self, temp_git_repo):
        """Test _get_repo method with valid git repository."""
        repo_path, _ = temp_git_repo
        git_manager = GitManager(repo_path)

        repo = git_manager._get_repo()
        assert isinstance(repo, Repo)
        assert repo.working_dir == str(repo_path)

    def test_get_repo_invalid_repository(self, temp_non_git_dir):
        """Test _get_repo method with invalid git repository."""
        git_manager = GitManager(temp_non_git_dir)

        with pytest.raises(RuntimeError, match="Not a git repository"):
            git_manager._get_repo()

    def test_get_repo_nonexistent_path(self):
        """Test _get_repo method with nonexistent path."""
        nonexistent_path = Path("/nonexistent/path")
        git_manager = GitManager(nonexistent_path)

        # GitPython raises NoSuchPathError for nonexistent paths, which gets converted to RuntimeError
        with pytest.raises(RuntimeError, match="Not a git repository"):
            git_manager._get_repo()

    def test_repo_property_lazy_loading(self, temp_git_repo):
        """Test repo property lazy loading."""
        repo_path, _ = temp_git_repo
        git_manager = GitManager(repo_path)

        # Initially _repo should be ready
        assert git_manager._repo is not None

        # First access should initialize _repo
        repo = git_manager.repo
        assert isinstance(repo, Repo)
        assert git_manager._repo is repo

        # Second access should return the same instance
        repo2 = git_manager.repo
        assert repo2 is repo

    def test_is_git_repository_true(self, temp_git_repo):
        """Test is_git_repository method with valid git repository."""
        repo_path, _ = temp_git_repo
        git_manager = GitManager(repo_path)

        assert git_manager.is_git_repository() is True

    def test_is_git_repository_false(self, temp_non_git_dir):
        """Test is_git_repository method with invalid git repository."""
        git_manager = GitManager(temp_non_git_dir)

        assert git_manager.is_git_repository() is False

    def test_is_git_repository_nonexistent_path(self):
        """Test is_git_repository method with nonexistent path."""
        nonexistent_path = Path("/nonexistent/path")
        git_manager = GitManager(nonexistent_path)

        assert git_manager.is_git_repository() is False

    def test_get_current_branch_success(self, temp_git_repo):
        """Test get_current_branch method with valid repository."""
        repo_path, repo = temp_git_repo
        git_manager = GitManager(repo_path)

        # Create initial commit to establish branch
        (repo_path / "test.txt").write_text("test")
        repo.index.add(["test.txt"])
        repo.index.commit("Initial commit")

        # Access repo property to initialize _repo
        _ = git_manager.repo

        branch_name = git_manager.get_current_branch()
        assert branch_name == "main" or branch_name == "master"

    def test_get_current_branch_no_repo_initialized(self, temp_non_git_dir):
        """Test get_current_branch method when _repo is None."""
        repo_path = temp_non_git_dir
        git_manager = GitManager(repo_path)

        # _repo is None, so method should return None
        assert git_manager.get_current_branch() is None

    def test_get_current_branch_detached_head(self, temp_git_repo):
        """Test get_current_branch method with detached HEAD."""
        repo_path, repo = temp_git_repo
        git_manager = GitManager(repo_path)

        # Create initial commit
        (repo_path / "test.txt").write_text("test")
        repo.index.add(["test.txt"])
        commit = repo.index.commit("Initial commit")

        # Checkout specific commit (detached HEAD)
        repo.head.reference = commit
        repo.head.reset(index=True, working_tree=True)

        # Access repo property to initialize _repo
        _ = git_manager.repo

        # Should return None for detached HEAD
        assert git_manager.get_current_branch() is None

    def test_get_current_branch_exception_handling(self, temp_git_repo):
        """Test get_current_branch method exception handling."""
        repo_path, _ = temp_git_repo
        git_manager = GitManager(repo_path)

        # Mock _repo to raise exception when accessing active_branch.name
        mock_repo = Mock(spec=Repo)
        mock_active_branch = Mock()
        type(mock_active_branch).name = PropertyMock(side_effect=Exception("Test exception"))
        mock_repo.active_branch = mock_active_branch
        git_manager._repo = mock_repo

        # Should return None when exception occurs
        assert git_manager.get_current_branch() is None

    def test_get_current_branch_no_commits(self, temp_git_repo):
        """Test get_current_branch method with repository that has no commits."""
        repo_path, _ = temp_git_repo
        git_manager = GitManager(repo_path)

        # Access repo property to initialize _repo
        _ = git_manager.repo

        # Repository with no commits still has default branch (main/master)
        branch_name = git_manager.get_current_branch()
        assert branch_name in ["main", "master"]

    @patch("prunejuice.core.git_ops.Repo")
    def test_get_repo_with_parent_search(self, mock_repo_class, temp_non_git_dir):
        """Test _get_repo method calls Repo with search_parent_directories=True."""
        mock_repo = Mock(spec=Repo)
        mock_repo_class.return_value = mock_repo
        git_manager = GitManager(temp_non_git_dir)
        mock_repo_class.assert_called_once_with(temp_non_git_dir, search_parent_directories=True)
        result = git_manager.repo
        assert result is mock_repo

    @patch("prunejuice.core.git_ops.Repo")
    def test_get_repo_invalid_git_repository_error(self, mock_repo_class, temp_non_git_dir):
        """Test _get_repo method handles InvalidGitRepositoryError."""
        mock_repo_class.side_effect = InvalidGitRepositoryError("Not a git repo")

        git_manager = GitManager(temp_non_git_dir)

        with pytest.raises(RuntimeError, match=f"Not a git repository: {temp_non_git_dir}"):
            git_manager._get_repo()

    def test_integration_workflow(self, temp_git_repo):
        """Test typical workflow integration."""
        repo_path, repo = temp_git_repo
        git_manager = GitManager(repo_path)

        # Check if it's a git repository
        assert git_manager.is_git_repository() is True

        # Access repo property to initialize _repo
        repo_obj = git_manager.repo
        assert isinstance(repo_obj, Repo)
        assert repo_obj.working_dir == str(repo_path)

        # Create a commit to establish branch
        (repo_path / "test.txt").write_text("test content")
        repo.index.add(["test.txt"])
        repo.index.commit("Initial commit")

        # Get current branch
        branch_name = git_manager.get_current_branch()
        assert branch_name in ["main", "master"]

    def test_get_head_commit_sha_success(self, temp_git_repo):
        """Test get_head_commit_sha method with valid repository and commits."""
        repo_path, repo = temp_git_repo
        git_manager = GitManager(repo_path)

        # Create initial commit
        (repo_path / "test.txt").write_text("test content")
        repo.index.add(["test.txt"])
        commit = repo.index.commit("Initial commit")

        # Access repo property to initialize _repo
        _ = git_manager.repo

        # Get HEAD commit SHA
        sha = git_manager.get_head_commit_sha()
        assert sha is not None
        assert len(sha) == 40  # Git SHA is 40 characters
        assert sha == commit.hexsha

    def test_get_head_commit_sha_no_repo_initialized(self, temp_git_repo):
        """Test get_head_commit_sha method when _repo is None."""
        repo_path, _ = temp_git_repo
        git_manager = GitManager(repo_path)

        # _repo is None, so method should return None
        assert git_manager.get_head_commit_sha() is None

    def test_get_head_commit_sha_no_commits(self, temp_git_repo):
        """Test get_head_commit_sha method with repository that has no commits."""
        repo_path, _ = temp_git_repo
        git_manager = GitManager(repo_path)

        # Access repo property to initialize _repo
        _ = git_manager.repo

        # Repository with no commits should return None
        assert git_manager.get_head_commit_sha() is None

    def test_get_head_commit_sha_multiple_commits(self, temp_git_repo):
        """Test get_head_commit_sha returns the latest commit."""
        repo_path, repo = temp_git_repo
        git_manager = GitManager(repo_path)

        # Create first commit
        (repo_path / "test1.txt").write_text("test content 1")
        repo.index.add(["test1.txt"])
        repo.index.commit("First commit")

        # Create second commit
        (repo_path / "test2.txt").write_text("test content 2")
        repo.index.add(["test2.txt"])
        latest_commit = repo.index.commit("Second commit")

        # Access repo property to initialize _repo
        _ = git_manager.repo

        # Should return the latest commit SHA
        sha = git_manager.get_head_commit_sha()
        assert sha == latest_commit.hexsha

    def test_get_head_commit_sha_exception_handling(self, temp_git_repo):
        """Test get_head_commit_sha method exception handling."""
        repo_path, _ = temp_git_repo
        git_manager = GitManager(repo_path)

        # Mock _repo to raise exception when accessing head.commit.hexsha
        mock_repo = Mock(spec=Repo)
        mock_commit = Mock()
        type(mock_commit).hexsha = PropertyMock(side_effect=Exception("Test exception"))
        mock_repo.head.commit = mock_commit
        git_manager._repo = mock_repo

        # Should return None when exception occurs
        assert git_manager.get_head_commit_sha() is None

    def test_get_repository_root_success(self, temp_git_repo):
        """Test get_repository_root method with valid repository."""
        repo_path, _ = temp_git_repo
        git_manager = GitManager(repo_path)

        # Get repository root
        root_path = git_manager.get_repository_root()
        assert isinstance(root_path, Path)
        assert root_path == repo_path

    def test_get_repository_root_with_subdirectory(self, temp_git_repo):
        """Test get_repository_root method when GitManager is initialized from subdirectory."""
        repo_path, repo = temp_git_repo

        # Create a subdirectory
        subdir = repo_path / "subdir"
        subdir.mkdir()

        # Initialize GitManager from subdirectory
        git_manager = GitManager(subdir)

        # Should still return the repository root, not the subdirectory
        root_path = git_manager.get_repository_root()
        assert isinstance(root_path, Path)
        assert root_path == repo_path
        assert root_path != subdir

    def test_get_repository_root_lazy_initialization(self, temp_git_repo):
        """Test get_repository_root method initializes _repo if None."""
        repo_path, _ = temp_git_repo
        git_manager = GitManager(repo_path)

        # Clear _repo to simulate lazy initialization
        git_manager._repo = None

        # get_repository_root should initialize _repo
        root_path = git_manager.get_repository_root()
        assert git_manager._repo is not None
        assert isinstance(root_path, Path)
        assert root_path == repo_path

    def test_get_repository_root_invalid_repository(self, temp_non_git_dir):
        """Test get_repository_root method with invalid git repository."""
        git_manager = GitManager(temp_non_git_dir)

        # Should raise RuntimeError for invalid repository
        with pytest.raises(RuntimeError, match="Not a git repository"):
            git_manager.get_repository_root()

    def test_create_worktree_success(self, temp_git_repo):
        """Test create_worktree method with valid parameters."""
        repo_path, repo = temp_git_repo
        git_manager = GitManager(repo_path)

        # Create initial commit to establish main branch
        (repo_path / "test.txt").write_text("test content")
        repo.index.add(["test.txt"])
        repo.index.commit("Initial commit")

        # Create worktree directory
        worktree_dir = repo_path / "worktrees"
        worktree_dir.mkdir()

        # Create worktree
        result = git_manager.create_worktree(
            worktree_dir=worktree_dir, branch_name="feature-branch", base_branch="main"
        )

        # Verify result
        expected_path = worktree_dir / "feature-branch"
        assert result["status"] == "success"
        assert result["output"] == str(expected_path)
        assert expected_path.exists()
        assert expected_path.is_dir()

        # Verify worktree was created in git
        worktrees = repo.git.worktree("list").split("\n")
        assert any(str(expected_path) in worktree for worktree in worktrees)

    def test_create_worktree_with_prefix(self, temp_git_repo):
        """Test create_worktree method with prefix parameter."""
        repo_path, repo = temp_git_repo
        git_manager = GitManager(repo_path)

        # Create initial commit to establish main branch
        (repo_path / "test.txt").write_text("test content")
        repo.index.add(["test.txt"])
        repo.index.commit("Initial commit")

        # Create worktree directory
        worktree_dir = repo_path / "worktrees"
        worktree_dir.mkdir()

        # Create worktree with prefix
        result = git_manager.create_worktree(
            worktree_dir=worktree_dir, branch_name="feature-branch", base_branch="main", prefix="dev"
        )

        # Verify result
        expected_path = worktree_dir / "dev-feature-branch"
        assert result["status"] == "success"
        assert result["output"] == str(expected_path)
        assert expected_path.exists()
        assert expected_path.is_dir()

    def test_create_worktree_nonexistent_base_branch(self, temp_git_repo):
        """Test create_worktree method with nonexistent base branch."""
        repo_path, repo = temp_git_repo
        git_manager = GitManager(repo_path)

        # Create initial commit to establish main branch
        (repo_path / "test.txt").write_text("test content")
        repo.index.add(["test.txt"])
        repo.index.commit("Initial commit")

        # Create worktree directory
        worktree_dir = repo_path / "worktrees"
        worktree_dir.mkdir()

        # Try to create worktree with nonexistent base branch
        result = git_manager.create_worktree(
            worktree_dir=worktree_dir, branch_name="feature-branch", base_branch="nonexistent"
        )

        # Should return failed status
        assert result["status"] == "failed"
        assert "Base branch 'nonexistent' does not exist" in result["output"]

    def test_create_worktree_creates_directory(self, temp_git_repo):
        """Test create_worktree method creates worktree directory if it doesn't exist."""
        repo_path, repo = temp_git_repo
        git_manager = GitManager(repo_path)

        # Create initial commit to establish main branch
        (repo_path / "test.txt").write_text("test content")
        repo.index.add(["test.txt"])
        repo.index.commit("Initial commit")

        # Create parent worktree directory but not the final path
        worktree_dir = repo_path / "worktrees"
        worktree_dir.mkdir()

        # Create worktree
        result = git_manager.create_worktree(
            worktree_dir=worktree_dir, branch_name="feature-branch", base_branch="main"
        )

        # Verify directory was created
        expected_path = worktree_dir / "feature-branch"
        assert result["status"] == "success"
        assert result["output"] == str(expected_path)
        assert expected_path.exists()
        assert expected_path.is_dir()

    def test_create_worktree_creates_parent_directories(self, temp_git_repo):
        """Test create_worktree method creates parent directories if they don't exist."""
        repo_path, repo = temp_git_repo
        git_manager = GitManager(repo_path)

        # Create initial commit to establish main branch
        (repo_path / "test.txt").write_text("test content")
        repo.index.add(["test.txt"])
        repo.index.commit("Initial commit")

        # Use nested directory path that doesn't exist
        worktree_dir = repo_path / "nested" / "worktrees"
        assert not worktree_dir.exists()
        assert not worktree_dir.parent.exists()

        # Create worktree - should create nested directories
        result = git_manager.create_worktree(
            worktree_dir=worktree_dir, branch_name="feature-branch", base_branch="main"
        )

        # Verify nested directories were created
        expected_path = worktree_dir / "feature-branch"
        assert result["status"] == "success"
        assert result["output"] == str(expected_path)
        assert expected_path.exists()
        assert expected_path.is_dir()
        assert worktree_dir.exists()
        assert worktree_dir.parent.exists()

    def test_create_worktree_existing_branch_name(self, temp_git_repo):
        """Test create_worktree method with existing branch name."""
        repo_path, repo = temp_git_repo
        git_manager = GitManager(repo_path)

        # Create initial commit to establish main branch
        (repo_path / "test.txt").write_text("test content")
        repo.index.add(["test.txt"])
        repo.index.commit("Initial commit")

        # Create a branch with the same name
        repo.create_head("feature-branch")

        # Create worktree directory
        worktree_dir = repo_path / "worktrees"
        worktree_dir.mkdir()

        # Try to create worktree with existing branch name
        result = git_manager.create_worktree(
            worktree_dir=worktree_dir, branch_name="feature-branch", base_branch="main"
        )

        # Should return failed status
        assert result["status"] == "failed"
        assert "Failed to create worktree" in result["output"]

    def test_create_worktree_master_as_base_branch(self, temp_git_repo):
        """Test create_worktree method with master as base branch."""
        repo_path, repo = temp_git_repo
        git_manager = GitManager(repo_path)

        # Create initial commit and rename main to master
        (repo_path / "test.txt").write_text("test content")
        repo.index.add(["test.txt"])
        repo.index.commit("Initial commit")

        # Rename main to master
        repo.heads.main.rename("master")

        # Create worktree directory
        worktree_dir = repo_path / "worktrees"
        worktree_dir.mkdir()

        # Create worktree using master as base
        result = git_manager.create_worktree(
            worktree_dir=worktree_dir, branch_name="feature-branch", base_branch="master"
        )

        # Verify result
        expected_path = worktree_dir / "feature-branch"
        assert result["status"] == "success"
        assert result["output"] == str(expected_path)
        assert expected_path.exists()
        assert expected_path.is_dir()

    @patch("prunejuice.core.git_ops.logger")
    def test_create_worktree_logging(self, mock_logger, temp_git_repo):
        """Test create_worktree method logs appropriate messages."""
        repo_path, repo = temp_git_repo
        git_manager = GitManager(repo_path)

        # Create initial commit to establish main branch
        (repo_path / "test.txt").write_text("test content")
        repo.index.add(["test.txt"])
        repo.index.commit("Initial commit")

        # Create worktree directory
        worktree_dir = repo_path / "worktrees"
        worktree_dir.mkdir()

        # Create worktree
        git_manager.create_worktree(worktree_dir=worktree_dir, branch_name="feature-branch", base_branch="main")

        # Verify logging calls
        expected_path = worktree_dir / "feature-branch"
        mock_logger.info.assert_any_call(f"Creating worktree at {expected_path} with branch feature-branch")
        mock_logger.info.assert_any_call(f"Successfully created worktree: {expected_path}")

    def test_create_worktree_empty_prefix(self, temp_git_repo):
        """Test create_worktree method with empty prefix parameter."""
        repo_path, repo = temp_git_repo
        git_manager = GitManager(repo_path)

        # Create initial commit to establish main branch
        (repo_path / "test.txt").write_text("test content")
        repo.index.add(["test.txt"])
        repo.index.commit("Initial commit")

        # Create worktree directory
        worktree_dir = repo_path / "worktrees"
        worktree_dir.mkdir()

        # Create worktree with empty prefix
        result = git_manager.create_worktree(
            worktree_dir=worktree_dir, branch_name="feature-branch", base_branch="main", prefix=""
        )

        # Verify result (should be same as no prefix)
        expected_path = worktree_dir / "feature-branch"
        assert result["status"] == "success"
        assert result["output"] == str(expected_path)
        assert expected_path.exists()
        assert expected_path.is_dir()

    def test_create_worktree_no_repo_initialized(self, temp_non_git_dir):
        """Test create_worktree method when _repo is None."""
        git_manager = GitManager(temp_non_git_dir)

        # Create worktree directory
        worktree_dir = temp_non_git_dir / "worktrees"
        worktree_dir.mkdir()

        # Should fail because _repo is None
        create_result = git_manager.create_worktree(
            worktree_dir=worktree_dir, branch_name="feature-branch", base_branch="main"
        )
        assert create_result["status"] == "failed"
        assert create_result["output"] == "Repository not initialized"
