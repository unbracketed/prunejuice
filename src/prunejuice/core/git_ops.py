from pathlib import Path
from typing import Optional

from git import InvalidGitRepositoryError, NoSuchPathError, Repo


class GitManager:
    "Provides project operations requiring interaction with the Git repository"

    def __init__(self, project_path: Path):
        """Initialize with project path."""
        self.project_path = project_path
        self._repo: Optional[Repo] = None

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

    def get_current_branch(self) -> Optional[str]:
        """Get the current branch name."""
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
