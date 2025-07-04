from typing import Optional, Protocol

from slugify import slugify

from prunejuice.core.database.manager import Database
from prunejuice.core.git_ops import GitManager
from prunejuice.core.models import Project, Workspace

"""
Use typing.Protocol for service interfaces - more Pythonic than ABCs.

  Key patterns:
  1. Protocols define contracts without inheritance
  2. Dependency injection via __init__ parameters
  3. Feature-based organization (users/service.py vs services/user_service.py)
  4. Framework DI systems (FastAPI Depends) inject services into endpoints

  Example structure:
  # Protocol definition
  class UserServiceProtocol(Protocol):
      def create_user(self, user_create: UserCreate) -> User: ...

  # Implementation (no inheritance needed)
  class DatabaseUserService:
      def __init__(self, db_session: Session):
          self.db = db_session

      def create_user(self, user_create: UserCreate) -> User:
          # business logic here

  Testing benefit: Easy to mock services by overriding dependencies.
"""


class WorkspaceProtocol(Protocol):
    def create_workspace(self, name: str) -> Workspace: ...
    def list_workspaces(self): ...


class WorkspaceService:
    def __init__(self, db: Database, git_interace: GitManager, project: Project):
        self.db = db
        self.git = git_interace
        self.project = project

    def create_workspace(self, name, branch_name: Optional[str], base_branch: Optional[str] = None):
        workspace_slug = slugify(name)

        # Create a Git worktree for the Workspace
        kwargs = {"branch_name": branch_name or workspace_slug}
        if base_branch:
            kwargs.update(base_branch=base_branch)
        new_worktree_path = self.git.create_worktree(self.project.worktree_path, branch_name, **kwargs)

        # run hooks (future) ...

        # new_workspace = Workspace({"name": name, "slug": workspace_slug, "project_id": self.project.id})

        new_workspace_id = self.db.insert_workspace(
            name,
            workspace_slug,
            self.project.id,
            new_worktree_path,
            branch_name,
            base_branch or "",
            self.project.path / ".prj/artifacts" / workspace_slug,
        )
        self.db.insert_event(
            action="workspace-created",
            project_id=self.project.id,
            workspace_id=new_workspace_id,
            status="success",
        )

    def list_workspaces(self):
        pass
