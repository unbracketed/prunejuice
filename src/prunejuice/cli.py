from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from slugify import slugify

from prunejuice.core.database.manager import Database
from prunejuice.core.git_ops import GitManager
from prunejuice.core.models import Project, Workspace
from prunejuice.core.operations import WorkspaceService

app = typer.Typer()

console = Console()


@app.command("init")
def init(name: str = typer.Argument(None, help="Name for the project")) -> None:
    """Initialize a new PruneJuice project in the current directory."""
    current_path = Path.cwd()

    # Check Git repository status and determine project directory
    git_manager = GitManager(current_path)
    git_init_head_ref = None
    git_init_branch = None

    if git_manager.is_git_repository():
        # Use Git repository root as project directory
        path = git_manager.get_repository_root()
        git_init_branch = git_manager.get_current_branch()
        git_init_head_ref = git_manager.get_head_commit_sha()
        console.print(f"Git repository detected (branch: {git_init_branch})", style="dim")
        console.print(f"Using Git repository root: {path}", style="dim")
    else:
        # Use current directory if no Git repository
        path = current_path
        console.print("No Git repository found", style="dim yellow")

    # Determine project name
    if name is None:
        # Use the project directory name as default
        name = path.name

    project_slug = slugify(name)

    console.print(f"🧃 Initializing PruneJuice project: [bold]{name}[/bold]", style="bold green")

    # Create project structure
    prj_dir = path / ".prj"
    prj_dir.mkdir(exist_ok=True)
    (prj_dir / "actions").mkdir(exist_ok=True)
    (prj_dir / "artifacts").mkdir(exist_ok=True)

    # Initialize database
    try:
        db = Database(prj_dir / "prunejuice.db")
        db.initialize()
        console.print("Database initialized", style="dim")
    except Exception as e:
        console.print(f"Warning: Database initialization failed: {e}", style="yellow")
        raise typer.Exit(1) from e

    # Insert project into database
    try:
        worktree_path = path / ".worktrees"
        project_id = db.insert_project(
            name=name,
            slug=project_slug,
            path=str(path),
            worktree_path=str(worktree_path),
            git_init_head_ref=git_init_head_ref,
            git_init_branch=git_init_branch,
        )
        console.print(f"Project '{name}' registered (ID: {project_id})", style="dim")

        # Insert event for project initialization
        db.insert_event(
            action="project-initialized",
            project_id=project_id,
            status="success",
        )

        # Insert initial workspace (only if git repository exists)
        if git_init_branch:
            workspace_id = db.insert_workspace(
                name="main",
                slug="main",
                project_id=project_id,
                path=str(path),
                git_branch=git_init_branch,
                git_origin_branch=f"origin/{git_init_branch}",
            )
            console.print(f"Main workspace created (ID: {workspace_id})", style="dim")

            # Insert event for workspace creation
            db.insert_event(
                action="workspace-created",
                project_id=project_id,
                workspace_id=workspace_id,
                status="success",
            )

    except Exception as e:
        console.print(f"Error: Failed to register project: {e}", style="red")
        raise typer.Exit(1) from e

    console.print("✅ Project initialized successfully!", style="bold green")


def _get_project_path() -> Path:
    """Get the project path, using Git root if in a repository."""
    path = Path.cwd()
    git_manager = GitManager(path)
    return git_manager.get_repository_root() if git_manager.is_git_repository() else path


def _load_project_from_db(project_path: Path) -> tuple[Project, Database]:
    """Load project from database, handling errors."""
    prj_dir = project_path / ".prj"

    if not prj_dir.exists():
        console.print("❌ No PruneJuice project found in current directory", style="red")
        console.print("Run 'prunejuice init' to initialize a project", style="dim")
        raise typer.Exit(1)

    db = Database(prj_dir / "prunejuice.db")
    project_data = db.get_project_by_path(str(project_path))

    if not project_data:
        console.print("❌ Project not found in database", style="red")
        console.print("The .prj directory exists but no project is registered", style="dim")
        raise typer.Exit(1)

    return Project(**project_data), db


def _display_project_info(project: Project, workspaces: list[Workspace]) -> None:
    """Display project information and workspaces."""
    console.print("✅ PruneJuice project found", style="green")
    console.print(f"Project: [bold]{project.name}[/bold] (ID: {project.id})")
    console.print(f"Path: {project.path}")
    console.print(f"Slug: {project.slug}")
    if project.git_init_branch:
        console.print(f"Git branch: {project.git_init_branch}")
    if project.date_created:
        console.print(f"Created: {project.date_created}")

    # Display workspaces
    if workspaces:
        console.print(f"\nWorkspaces ({len(workspaces)}):", style="bold")
        for workspace in workspaces:
            console.print(f"  • {workspace.name} (ID: {workspace.id}) - {workspace.git_branch}")
    else:
        console.print("\nNo workspaces found", style="dim")


def _display_events(db: Database, project: Project, workspaces: list[Workspace]) -> None:
    """Display recent events for a project."""
    if project.id is None:
        console.print("\nNo events recorded", style="dim")
        return
    events = db.get_events_by_project_id(project.id)

    if events:
        console.print("\nRecent Events:", style="bold")

        # Create a rich table for events
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("◉", justify="center")
        table.add_column("Workspace", style="yellow")
        table.add_column("Action", style="cyan")
        table.add_column("Timestamp", style="dim")

        # Add events to the table (already ordered by timestamp DESC)
        for event in events[:10]:  # Show only the 10 most recent events
            # Format timestamp for display
            timestamp_str = event.timestamp.strftime("%Y-%m-%d %H:%M:%S") if event.timestamp else "N/A"

            # Get workspace name if available
            workspace_name = "—"
            if event.workspace_id:
                for ws in workspaces:
                    if ws.id == event.workspace_id:
                        workspace_name = ws.name
                        break

            # Create status symbol
            if event.status == "success":
                status_symbol = "[green]✓[/green]"
            elif event.status == "failed":
                status_symbol = "[red]✗[/red]"
            else:
                status_symbol = "[yellow]●[/yellow]"

            table.add_row(status_symbol, workspace_name, event.action, timestamp_str)

        console.print(table)

        if len(events) > 10:
            console.print(f"\n[dim]Showing 10 of {len(events)} total events[/dim]")
    else:
        console.print("\nNo events recorded", style="dim")


@app.command("status")
def status() -> Project:
    """Show the current status of the PruneJuice project."""
    project_path = _get_project_path()
    project, db = _load_project_from_db(project_path)

    # Get workspaces for this project
    if project.id is None:
        console.print("❌ Project has no ID", style="red")
        raise typer.Exit(1)
    workspaces_data = db.get_workspaces_by_project_id(project.id)
    workspaces = [Workspace(**workspace_data) for workspace_data in workspaces_data]

    _display_project_info(project, workspaces)

    # Get and display events
    _display_events(db, project, workspaces)

    return project


@app.command("create-workspace")
def create_workspace(
    name: str = typer.Argument(..., help="Name for the workspace"),
    branch_name: Optional[str] = typer.Option(None, "--branch-name", help="Git branch name for the workspace"),
    base_branch: Optional[str] = typer.Option(None, "--base-branch", help="Base branch to create the workspace from"),
) -> None:
    """Create a new workspace."""
    project_path = _get_project_path()
    project, db = _load_project_from_db(project_path)

    git_manager = GitManager(Path(project.path))

    console.print(f"🚀 Creating workspace: [bold]{name}[/bold]", style="bold green")

    try:
        workspace_service = WorkspaceService(db, git_manager, project)
        workspace = workspace_service.create_workspace(name, branch_name, base_branch)

        console.print(f"✅ Workspace '{workspace.name}' created successfully!", style="bold green")
        console.print(f"Branch: {workspace.git_branch}")
        console.print(f"Path: {workspace.path}")
        if workspace.git_origin_branch:
            console.print(f"Base branch: {workspace.git_origin_branch}")

    except Exception as e:
        console.print(f"❌ Failed to create workspace: {e}", style="red")
        raise typer.Exit(1) from e


if __name__ == "__main__":
    app()
