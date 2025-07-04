import contextlib
from logging import getLogger
from pathlib import Path
from typing import Optional

from git import GitCommandError, InvalidGitRepositoryError, NoSuchPathError, Repo

logger = getLogger(__name__)


class GitManager:
    "Provides project operations requiring interaction with the Git repository"

    def __init__(self, project_path: Path):
        """Initialize with project path."""
        self.project_path = project_path
        self._repo: Optional[Repo] = None
        with contextlib.suppress(RuntimeError):
            self._repo = self._get_repo()

    def _get_repo(self) -> Repo:
        try:
            repo = Repo(self.project_path, search_parent_directories=True)
        except (InvalidGitRepositoryError, NoSuchPathError) as err:
            msg = f"Not a git repository: {self.project_path}"
            raise RuntimeError(msg) from err
        return repo

    @property
    def repo(self) -> Repo:
        """Get Git repository."""
        if self._repo is None:
            self._repo = self._get_repo()
        return self._repo

    def is_git_repository(self) -> bool:
        """Check if the project path is a Git repository."""
        try:
            self._get_repo()
        except RuntimeError:
            return False
        return True

    def get_repository_root(self) -> Path:
        """Get the root directory of the Git repository."""
        if self._repo is None:
            self._repo = self._get_repo()
        return Path(self._repo.working_dir)

    def get_current_branch(self) -> Optional[str]:
        """Get the current branch name."""
        if self._repo is None:
            return None
        try:
            return self._repo.active_branch.name
        except Exception:
            return None

    def get_head_commit_sha(self) -> Optional[str]:
        """Get the commit SHA for the repository HEAD.

        Returns:
            The SHA of the HEAD commit as a string, or None if there are no commits
            or if the repository is not initialized.
        """
        if self._repo is None:
            return None
        try:
            return self._repo.head.commit.hexsha
        except Exception:
            return None

    def close(self) -> None:
        """Close the repository and free resources."""
        if self._repo is not None:
            self._repo.close()
            self._repo = None

    def create_worktree(
        self, worktree_dir: Path, branch_name: str, base_branch: str = "main", prefix: str = ""
    ) -> dict[str, str]:
        """Create a new Git worktree.

        Args:
            worktree_dir: Directory for worktree (default: .worktrees)
            branch_name: Name for the new branch
            base_branch: Base branch to create from

        Returns:
            A dict with keys:
            status - Indicates success / failure
            output - worktree path on success, error message on failure
        """
        worktree_path = worktree_dir / f"{prefix}-{branch_name}" if prefix else worktree_dir / branch_name
        worktree_path.mkdir(parents=True, exist_ok=True)

        try:
            # Check if base branch exists
            if self._repo is None:
                return {"status": "failed", "output": "Repository not initialized"}

            if base_branch not in [ref.name for ref in self._repo.refs]:
                return {"status": "failed", "output": f"Base branch '{base_branch}' does not exist"}

            logger.info(f"Creating worktree at {worktree_path} with branch {branch_name}")

            self._repo.git.worktree("add", "-b", branch_name, str(worktree_path), base_branch)

            logger.info(f"Successfully created worktree: {worktree_path}")
            return {"status": "success", "output": str(worktree_path)}

        except GitCommandError as e:
            return {"status": "failed", "output": f"Failed to create worktree: {e}"}
