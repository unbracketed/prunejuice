from logging import getLogger
from pathlib import Path
from typing import Optional, Protocol

from slugify import slugify

from prunejuice.core.database.manager import Database
from prunejuice.core.git_ops import GitManager
from prunejuice.core.models import Project, Workspace

logger = getLogger(__name__)


class WorkspaceProtocol(Protocol):
    def create_workspace(
        self, name: str, branch_name: Optional[str], base_branch: Optional[str] = None
    ) -> Workspace: ...
    def list_workspaces(self) -> None: ...


class WorkspaceService:
    def __init__(self, db: Database, git_interace: GitManager, project: Project) -> None:
        self.db = db
        self.git = git_interace
        self.project = project

    def create_workspace(
        self, name: str, branch_name: Optional[str], base_branch: Optional[str] = None
    ) -> Optional[Workspace]:
        workspace_slug = slugify(name)

        # Create a Git worktree for the Workspace
        actual_branch_name = branch_name or workspace_slug
        kwargs = {}
        if base_branch:
            kwargs["base_branch"] = base_branch
        worktree_result = self.git.create_worktree(Path(self.project.worktree_path), actual_branch_name, **kwargs)

        if worktree_result["status"] != "success":
            logger.error(worktree_result["message"])
            return None

        new_worktree_path = worktree_result["output"]

        if self.project.id is None:
            raise ValueError("Project ID is not set")

        new_workspace_id = self.db.insert_workspace(
            name,
            workspace_slug,
            self.project.id,
            new_worktree_path,
            actual_branch_name,
            base_branch or "",
            str(Path(self.project.path) / ".prj/artifacts" / workspace_slug),
        )

        new_workspace = Workspace(
            id=new_workspace_id,
            name=name,
            slug=workspace_slug,
            project_id=self.project.id,
            path=str(new_worktree_path),
            git_branch=actual_branch_name,
            git_origin_branch=base_branch or "",
            artifacts_path=str(Path(self.project.path) / ".prj/artifacts" / workspace_slug),
        )
        self.db.insert_event(
            action="workspace-created",
            project_id=self.project.id,
            workspace_id=new_workspace_id,
            status="success",
        )
        return new_workspace

    def list_workspaces(self) -> None:
        pass
