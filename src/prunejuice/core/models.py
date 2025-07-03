from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Project(BaseModel):
    id: Optional[int] = None
    name: str
    slug: str
    path: str
    worktree_path: str
    git_init_head_ref: Optional[str] = None
    git_init_branch: Optional[str] = None
    date_created: Optional[datetime] = None

    class Config:
        from_attributes = True


class Workspace(BaseModel):
    id: Optional[int] = None
    name: str
    slug: str
    project_id: int
    path: str
    git_branch: str
    git_origin_branch: str
    artifacts_path: Optional[str] = None
    date_created: Optional[datetime] = None

    class Config:
        from_attributes = True


class Event(BaseModel):
    id: Optional[int] = None
    action: str
    project_id: int
    workspace_id: Optional[int] = None
    timestamp: Optional[datetime] = None
    status: str

    class Config:
        from_attributes = True
