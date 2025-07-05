from logging import getLogger
from pathlib import Path
from typing import Optional, Protocol

from slugify import slugify

from prunejuice.core.database.manager import Database
from prunejuice.core.git_ops import GitManager
from prunejuice.core.models import Event, Project, Workspace

logger = getLogger(__name__)


class WorkspaceProtocol(Protocol):
    def create_workspace(
        self, name: str, branch_name: Optional[str] = None, base_branch: Optional[str] = None
    ) -> Workspace: ...
    def list_workspaces(self) -> Optional[list[Workspace]]: ...


class WorkspaceService:
    def __init__(self, db: Database, git_interace: GitManager, project: Project) -> None:
        self.db = db
        self.git = git_interace
        self.project = project

    def create_workspace(
        self, name: str, branch_name: Optional[str] = None, base_branch: Optional[str] = None
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

    def list_workspaces(self) -> Optional[list[Workspace]]:
        if self.project.id is None:
            return None
        workspaces_data = self.db.get_workspaces_by_project_id(self.project.id)
        if workspaces_data is None:
            return None
        return [Workspace(**workspace_data) for workspace_data in workspaces_data]


class EventProtocol(Protocol):
    def add_event(self, action: str, status: str, workspace: Optional[Workspace] = None) -> Event: ...
    def list_events(self, workspace: Optional[Workspace] = None) -> list[Event]: ...


class EventService:
    def __init__(self, db: Database, project: Project):
        self.db = db
        self.project = project

    def add_event(self, action: str, status: str, workspace: Optional[Workspace] = None) -> Event:
        """Add a new event to the event log.

        Args:
            action: The action that occurred (e.g., 'workspace-created', 'build-started')
            status: The status of the action (e.g., 'success', 'failure', 'pending')
            workspace: Optional workspace associated with the event

        Returns:
            The created Event object
        """
        if self.project.id is None:
            raise ValueError("Project ID is not set")

        workspace_id = workspace.id if workspace else None

        event_id = self.db.insert_event(
            action=action, project_id=self.project.id, workspace_id=workspace_id, status=status
        )

        return Event(id=event_id, action=action, project_id=self.project.id, workspace_id=workspace_id, status=status)

    def list_events(self, workspace: Optional[Workspace] = None) -> list[Event]:
        """List events for the project, optionally filtered by workspace.

        Args:
            workspace: Optional workspace to filter events by

        Returns:
            List of Event objects, ordered by timestamp DESC (most recent first)
        """
        if self.project.id is None:
            raise ValueError("Project ID is not set")

        if workspace:
            if workspace.id is None:
                raise ValueError("Workspace ID is not set")
            # Get events for specific workspace
            return self.db.get_events_by_workspace_id(workspace.id)
        else:
            # Get all events for the project
            return self.db.get_events_by_project_id(self.project.id)
